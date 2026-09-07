import tempfile
import unittest
from pathlib import Path
from automation.data import connect,seed
from automation.robot import analyze,flush


class Collection:
    def __init__(self): self.docs={}
    def replace_one(self,query,body,upsert=False): self.docs[query['_id']]=body


class Mongo:
    def __init__(self):self.collections={}
    def __getitem__(self,key):return self.collections.setdefault(key,Collection())


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.db=connect(Path(self.temp.name));self.addCleanup(self.db.close);seed(self.db)

    def test_seeding_is_idempotent(self):
        seed(self.db)
        self.assertEqual(self.db.execute('SELECT count(*) FROM measurements').fetchone()[0],303)

    def test_isolation_forest_and_validation(self):
        self.assertEqual(analyze(self.db,'test-run'),63)
        labels={r['measurement_id']:r['label'] for r in self.db.execute('SELECT * FROM evaluations')}
        self.assertEqual(labels[301],'anomalia_estatistica')
        self.assertEqual(labels[302],'sem_desvio_detectado')
        self.assertEqual(labels[303],'dado_invalido')

    def test_second_cycle_does_not_duplicate_alerts(self):
        analyze(self.db,'first')
        before=self.db.execute('SELECT count(*) FROM alerts').fetchone()[0]
        self.assertEqual(analyze(self.db,'second'),0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM alerts').fetchone()[0],before)

    def test_outbox_retries_without_duplicates(self):
        analyze(self.db,'first');mongo=Mongo();flush(self.db,mongo)
        count=len(mongo['events'].docs)
        with self.db:self.db.execute('UPDATE outbox SET delivered=0')
        flush(self.db,mongo)
        self.assertEqual(len(mongo['events'].docs),count)
        self.assertEqual(self.db.execute('SELECT count(*) FROM outbox WHERE delivered=0').fetchone()[0],0)

    def test_failed_delivery_keeps_pending_event(self):
        analyze(self.db,'first')
        class Broken:
            def __getitem__(self,key):raise ConnectionError('simulated')
        with self.assertRaises(ConnectionError):flush(self.db,Broken())
        self.assertEqual(self.db.execute('SELECT count(*) FROM outbox WHERE delivered=0').fetchone()[0],63)
