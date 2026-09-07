import json
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from services.errors import ServiceError
from services.gemini_service import validate_extraction
from services.storage import Store
from services.clinical_summary import summarize


class ExtractionTests(unittest.TestCase):
    def test_literal_negation_preserved(self):
        raw=json.dumps({'fatos':[{'campo':'sintoma','valor':'dor','evidencia':'Não tenho dor','estado':'negado'}]})
        self.assertEqual(validate_extraction(raw,'Não tenho dor')['fatos'][0]['estado'],'negado')

    def test_unsupported_evidence_rejected(self):
        raw=json.dumps({'fatos':[{'campo':'sintoma','valor':'dor','evidencia':'Tenho dor','estado':'afirmado'}]})
        with self.assertRaises(ServiceError): validate_extraction(raw,'Estou bem')

    def test_negation_cannot_be_affirmed(self):
        raw=json.dumps({'fatos':[{'campo':'sintoma','valor':'dor','evidencia':'Não tenho dor','estado':'afirmado'}]})
        with self.assertRaises(ServiceError): validate_extraction(raw,'Não tenho dor')

    def test_unknown_fields_rejected(self):
        with self.assertRaises(ServiceError): validate_extraction('{"fatos":[],"diagnostico":"x"}','x')

    def test_invalid_json_rejected(self):
        with self.assertRaises(ServiceError): validate_extraction('texto sem JSON','x')

    def test_ambiguous_pressure_not_converted(self):
        c={'skills':{'main skill':{'user_defined':{'pressao_informada':'12/8','relato_original':'12/8'}}}}
        self.assertIsNone(summarize(c)['pressao_arterial'])

    def test_missing_values_are_not_invented(self):
        self.assertIsNone(summarize({}))


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name))

    def test_quota_atomic_across_connections(self):
        def attempt(_):
            try:self.store.reserve_call(5,0);return True
            except ServiceError:return False
        with ThreadPoolExecutor(max_workers=8) as executor:
            results=list(executor.map(attempt,range(20)))
        self.assertEqual(sum(results),5);self.assertEqual(self.store.usage(),5)

    def test_quota_survives_recreation(self):
        self.store.reserve_call(1,0)
        with self.assertRaises(ServiceError): Store(Path(self.temp.name)).reserve_call(1,0)

    def test_cache_survives_recreation(self):
        self.store.save_cache('example',{'fatos':[]})
        self.assertEqual(Store(Path(self.temp.name)).cached('example'),{'fatos':[]})

    def test_interval_is_enforced(self):
        self.store.reserve_call(500,60)
        with self.assertRaises(ServiceError):self.store.reserve_call(500,60)
