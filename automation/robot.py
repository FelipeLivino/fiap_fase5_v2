"""Robô periódico: SQLite + Isolation Forest + MongoDB + extração Gemini.

Eventos são gravados numa outbox SQL e replicados por upsert no MongoDB.
Uma falha entre as gravações mantém os eventos disponíveis para reenvio.
"""
import argparse
import fcntl
import json
import os
import signal
import threading
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient
from config import settings
from automation.data import connect, seed, MESSAGES
from automation.analysis import features, train
from services.storage import Store
from services.gemini_service import GeminiService
from services.errors import ServiceError


def now():
    return datetime.now(timezone.utc).isoformat()


def event(db, identifier, collection, body):
    db.execute('INSERT OR REPLACE INTO outbox(id,collection,body,delivered) VALUES (?,?,?,0)',
               (identifier,collection,json.dumps(body,ensure_ascii=False)))


def flush(db, mongo):
    for row in db.execute('SELECT * FROM outbox WHERE delivered=0 ORDER BY rowid').fetchall():
        # Reutilizar o identificador permite reenviar um evento sem duplicá-lo no MongoDB.
        mongo[row['collection']].replace_one({'_id':row['id']},json.loads(row['body']),upsert=True)
        with db:
            db.execute('UPDATE outbox SET delivered=1 WHERE id=?',(row['id'],))


def analyze(db, run_id):
    model,version=train(db.execute("SELECT * FROM measurements WHERE dataset='treino' ORDER BY id").fetchall())
    # Cada medição é avaliada uma vez por versão; mudanças no treinamento permitem nova avaliação.
    rows=db.execute("""SELECT m.* FROM measurements m WHERE dataset='monitoramento'
        AND NOT EXISTS (SELECT 1 FROM evaluations e WHERE e.measurement_id=m.id AND e.model_version=?)
        ORDER BY m.id""",(version,)).fetchall()
    for row in rows:
        values=features(row)
        if values is None:
            label,score='dado_invalido',None
        else:
            label='anomalia_estatistica' if model.predict([values])[0]==-1 else 'sem_desvio_detectado'
            score=float(model.decision_function([values])[0])
        identifier=f"medicao:{row['id']}:{version}"
        body={'measurement_id':row['id'],'patient_id':row['patient_id'],'run_id':run_id,
              'model_version':version,'label':label,'score':score,'created':now(),
              'note':'Simulação acadêmica. Resultado estatístico não é avaliação clínica.'}
        with db:
            db.execute('INSERT OR IGNORE INTO evaluations VALUES (?,?,?,?,?)',(row['id'],version,run_id,label,score))
            if label=='anomalia_estatistica':
                db.execute('INSERT OR IGNORE INTO alerts VALUES (?,?,?,?,?,?)',
                    (identifier,row['id'],run_id,version,'Desvio do conjunto sintético de referência',now()))
            event(db,identifier,'events',body)
    return len(rows)


def run_once(config, mongo, extractor):
    db=connect(config['DATA_DIR'])
    run_id=uuid.uuid4().hex
    started=now()
    with db:
        db.execute("INSERT INTO runs(id,started,status) VALUES (?,?,'em_execucao')",(run_id,started))
        event(db,run_id,'runs',{'started':started,'status':'em_execucao','processed':0})
    processed=0
    status='concluida'
    error=None
    try:
        seed(db)
        processed=analyze(db,run_id)
        flush(db,mongo)
        for message in MESSAGES:
            mongo.messages.update_one({'_id':message['_id']},{'$setOnInsert':dict(message,status='pendente')},upsert=True)
        if not extractor.configured:
            status='aguardando_gemini'
        else:
            for item in mongo.messages.find({'status':'pendente'}).sort('_id',1).limit(5):
                try:
                    result=extractor.extract(item['text'])
                except ServiceError as exc:
                    error=exc.code
                    status='parcial'
                    break
                mongo.messages.update_one({'_id':item['_id']},{'$set':{
                    'status':'interpretada','extraction':result,'run_id':run_id,'updated':now()}})
                with db:
                    event(db,f"texto:{item['_id']}",'events',{
                        'message_id':item['_id'],'run_id':run_id,'label':'texto_interpretado',
                        'model':result['model'],'created':now()})
    except Exception as exc:
        error=type(exc).__name__
        status='falha'
    finally:
        finished=now()
        with db:
            db.execute('UPDATE runs SET finished=?,status=?,processed=?,error_code=? WHERE id=?',
                       (finished,status,processed,error,run_id))
            event(db,run_id,'runs',{'started':started,'finished':finished,'status':status,
                                  'processed':processed,'error_code':error})
        try:
            flush(db,mongo)
        except Exception as exc:
            with db:
                db.execute("UPDATE runs SET status='sincronizacao_pendente',error_code=? WHERE id=?",(type(exc).__name__,run_id))
                event(db,run_id,'runs',{'started':started,'finished':finished,'status':'sincronizacao_pendente',
                                      'processed':processed,'error_code':type(exc).__name__})
            status='sincronizacao_pendente'
        db.close()
    return {'run_id':run_id,'status':status,'processed':processed}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    config=settings()
    config['DATA_DIR'].mkdir(parents=True,exist_ok=True)
    with (config['DATA_DIR']/'robot.lock').open('a') as lock:
        try:
            # O bloqueio do arquivo impede dois robôs de processarem o mesmo volume ao mesmo tempo.
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1,'Já há uma execução do robô ativa neste volume.\n')
        password=os.getenv('MONGO_PASSWORD','')
        if not password:
            parser.exit(1,'Defina MONGO_PASSWORD no .env.\n')
        client=MongoClient(host=os.getenv('MONGO_HOST','mongo'),port=27017,
                           username='cardioia',password=password,authSource='admin',
                           serverSelectionTimeoutMS=5000,connectTimeoutMS=5000,socketTimeoutMS=10000)
        stopped=threading.Event()
        signal.signal(signal.SIGTERM,lambda *_:stopped.set())
        signal.signal(signal.SIGINT,lambda *_:stopped.set())
        extractor=GeminiService(config,Store(config['DATA_DIR']))
        try:
            while not stopped.is_set():
                result=run_once(config,client.cardioia,extractor)
                print(json.dumps(result),flush=True)
                if args.once:
                    if result['status'] in ('falha','sincronizacao_pendente'):
                        raise SystemExit(1)
                    break
                stopped.wait(max(10,int(os.getenv('ROBOT_INTERVAL_SECONDS','60'))))
        finally:
            client.close()


if __name__=='__main__':
    main()
