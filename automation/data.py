"""Dados sintéticos reprodutíveis. As distribuições não são faixas clínicas."""
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3


def connect(directory):
    directory.mkdir(parents=True, exist_ok=True)
    db=sqlite3.connect(directory/'automation.sqlite3', timeout=20)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript(Path('database/relational/schema.sql').read_text(encoding='utf-8'))
    return db


def seed(db):
    randomizer=random.Random(42)
    base=datetime(2026,9,1,tzinfo=timezone.utc)
    with db:
        db.execute("INSERT OR IGNORE INTO patients VALUES ('SIM-001','Paciente fictício 01')")
        for i in range(1,301):
            values=[round(randomizer.gauss(120,5),1),round(randomizer.gauss(80,3),1),
                    round(randomizer.gauss(72,5),1),randomizer.choice([0.8,0.9,1.0])]
            db.execute('INSERT OR IGNORE INTO measurements VALUES (?,?,?,?,?,?,?,?,?)',
                (i,'SIM-001',(base+timedelta(minutes=i)).isoformat(),*values,
                 'treino' if i<=240 else 'monitoramento','amostra_sintetica'))
        cases=[(301,220,145,165,0.1,'desvio_injetado'),(302,120,80,72,1,'referencia'),
               (303,None,80,72,1,'dado_ausente')]
        for i,sy,di,hr,ad,kind in cases:
            db.execute('INSERT OR IGNORE INTO measurements VALUES (?,?,?,?,?,?,?,?,?)',
                (i,'SIM-001',(base+timedelta(minutes=i)).isoformat(),sy,di,hr,ad,'monitoramento',kind))


MESSAGES=[
    {'_id':'texto-001','paciente_id':'SIM-001','text':'Minha frequência foi 72 bpm. Não tenho dor.'},
    {'_id':'texto-002','paciente_id':'SIM-001','text':'Medi minha pressão: 120/80 mmHg.'},
    {'_id':'texto-003','paciente_id':'SIM-001','text':'Esqueci o tratamento ontem. Hoje quero conversar sobre isso.'},
]
