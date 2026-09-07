"""Exporta evidência dos dados fictícios e vínculos SQL/MongoDB, sem credenciais."""
import json
import os
from pymongo import MongoClient
from config import settings
from automation.data import connect

def main():
    db=connect(settings()['DATA_DIR'])
    client=MongoClient(host=os.getenv('MONGO_HOST','mongo'),username='cardioia',
        password=os.environ['MONGO_PASSWORD'],authSource='admin',serverSelectionTimeoutMS=5000)
    try:
        evidence={
            'counts':{name:db.execute(f'SELECT count(*) FROM {name}').fetchone()[0]
                      for name in ('measurements','evaluations','alerts','runs')},
            'pending_events':db.execute('SELECT count(*) FROM outbox WHERE delivered=0').fetchone()[0],
            'controlled_cases':[dict(x) for x in db.execute('''SELECT m.id,m.expected_case,e.label,e.score,e.run_id,
                e.model_version FROM measurements m JOIN evaluations e ON e.measurement_id=m.id WHERE m.id>=301 ORDER BY m.id''')],
            'recent_runs':[dict(x) for x in db.execute('SELECT * FROM runs ORDER BY started DESC LIMIT 5')],
            'mongo_events':client.cardioia.events.count_documents({}),
            'messages':list(client.cardioia.messages.find({}))}
        print(json.dumps(evidence,ensure_ascii=False,indent=2))
    finally:
        db.close();client.close()

if __name__=='__main__':
    main()
