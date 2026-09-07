"""Acrescenta uma leitura fictícia para o próximo ciclo periódico."""
import argparse
from datetime import datetime, timezone
from config import settings
from automation.data import connect, seed

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--systolic',type=float,required=True)
    parser.add_argument('--diastolic',type=float,required=True)
    parser.add_argument('--heart-rate',type=float,required=True)
    parser.add_argument('--adherence',type=float,required=True)
    args=parser.parse_args()
    db=connect(settings()['DATA_DIR'])
    try:
        seed(db)
        with db:
            cursor=db.execute('''INSERT INTO measurements(patient_id,measured_at,systolic,diastolic,
                heart_rate,adherence,dataset,expected_case) VALUES (?,?,?,?,?,?,'monitoramento','insercao_manual')''',
                ('SIM-001',datetime.now(timezone.utc).isoformat(),args.systolic,args.diastolic,args.heart_rate,args.adherence))
        print(f'Medição fictícia {cursor.lastrowid} disponível para o próximo ciclo.')
    finally:
        db.close()

if __name__=='__main__':
    main()
