import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from google.genai.errors import ClientError, ServerError

from services.errors import ServiceError
from services.gemini_service import GeminiService
from services.storage import Store


class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name))
        self.service = GeminiService({
            'GEMINI_API_KEY': 'SENSITIVE_KEY',
            'GEMINI_MODEL': 'gemini-test',
            'GEMINI_DAILY_LIMIT': 500,
            'GEMINI_MIN_INTERVAL_SECONDS': 0,
        }, self.store)
        self.text = 'Não tenho dor.'
        self.payload = {'fatos': [{
            'campo': 'sintoma', 'valor': 'dor',
            'evidencia': self.text, 'estado': 'negado',
        }]}
        self.client_factory = self.enterContext(patch('google.genai.Client'))
        self.generate = self.client_factory.return_value.__enter__.return_value.models.generate_content
        self.generate.return_value.text = json.dumps(self.payload)

    def test_success_is_validated_and_cached_without_another_call(self):
        result = self.service.extract(self.text)
        self.assertEqual(result['fatos'], self.payload['fatos'])
        self.assertTrue(result['confirmacao_necessaria'])
        self.assertFalse(result['cache'])
        self.assertTrue(self.service.extract(self.text)['cache'])
        self.generate.assert_called_once()
        self.assertEqual(self.store.usage(), 1)

    def test_failures_are_distinguished_redacted_and_not_retried(self):
        sensitive = 'SENSITIVE_KEY SENSITIVE_REPORT https://example.invalid/?key=SECRET'
        errors = [
            (httpx.ReadTimeout(sensitive), 'GEMINI_TIMEOUT', 504),
            (httpx.ConnectTimeout(sensitive), 'GEMINI_TIMEOUT', 504),
            (TimeoutError(sensitive), 'GEMINI_TIMEOUT', 504),
            (httpx.ConnectError(sensitive), 'GEMINI_CONNECTION', 503),
            (httpx.RemoteProtocolError(sensitive), 'GEMINI_CONNECTION', 503),
            (ClientError(400, {'error': {'message': sensitive}}), 'GEMINI_REQUEST', 503),
            (ClientError(401, {'error': {'message': sensitive}}), 'GEMINI_AUTH', 503),
            (ClientError(403, {'error': {'message': sensitive}}), 'GEMINI_AUTH', 503),
            (ClientError(404, {'error': {'message': sensitive}}), 'GEMINI_MODEL', 503),
            (ClientError(408, {'error': {'message': sensitive}}), 'GEMINI_TIMEOUT', 504),
            (ClientError(429, {'error': {'message': sensitive}}), 'GEMINI_QUOTA', 429),
            (ServerError(503, {'error': {'message': sensitive}}), 'GEMINI_UNAVAILABLE', 503),
            (ServerError(504, {'error': {'message': sensitive}}), 'GEMINI_TIMEOUT', 504),
            (RuntimeError(sensitive), 'GEMINI_UNAVAILABLE', 503),
        ]
        for attempt, (error, code, status) in enumerate(errors, start=1):
            with self.subTest(error=type(error).__name__, code=code):
                self.generate.side_effect = error
                with self.assertLogs('services.gemini_service', level='WARNING') as logs:
                    with self.assertRaises(ServiceError) as caught:
                        self.service.extract(self.text)
                self.assertEqual((caught.exception.code, caught.exception.status), (code, status))
                public_output = str(caught.exception) + '\n'.join(logs.output)
                for secret in ('SENSITIVE_KEY', 'SENSITIVE_REPORT', 'example.invalid', 'SECRET'):
                    self.assertNotIn(secret, public_output)
                self.assertIn(type(error).__name__, '\n'.join(logs.output))
                self.assertEqual(self.generate.call_count, attempt)
                self.assertEqual(self.store.usage(), attempt)
                options = self.client_factory.call_args.kwargs['http_options']
                self.assertEqual(options.retry_options.attempts, 1)
                self.assertEqual(options.timeout, 30000)

    def test_manual_retry_after_timeout_succeeds_and_caches(self):
        self.generate.side_effect = httpx.ReadTimeout('SENSITIVE_KEY')
        with self.assertLogs('services.gemini_service', level='WARNING'):
            with self.assertRaises(ServiceError):
                self.service.extract(self.text)
        self.generate.side_effect = None
        self.assertFalse(self.service.extract(self.text)['cache'])
        self.assertTrue(self.service.extract(self.text)['cache'])
        self.assertEqual(self.generate.call_count, 2)
        self.assertEqual(self.store.usage(), 2)

    def test_invalid_evidence_is_not_cached_or_reclassified(self):
        self.generate.return_value.text = json.dumps(self.payload)
        with self.assertRaises(ServiceError) as caught:
            self.service.extract('Estou bem.')
        self.assertEqual(caught.exception.code, 'INVALID_EXTRACTION')
        self.generate.return_value.text = '{"fatos": []}'
        self.assertFalse(self.service.extract('Estou bem.')['cache'])
        self.assertEqual(self.generate.call_count, 2)

    def test_budget_blocks_manual_retry_before_contacting_google(self):
        self.service.config['GEMINI_DAILY_LIMIT'] = 1
        self.generate.side_effect = httpx.ReadTimeout('timeout')
        with self.assertLogs('services.gemini_service', level='WARNING'):
            with self.assertRaises(ServiceError):
                self.service.extract(self.text)
        with self.assertRaises(ServiceError) as caught:
            self.service.extract(self.text)
        self.assertEqual(caught.exception.code, 'LOCAL_QUOTA')
        self.generate.assert_called_once()

    def test_missing_key_does_not_reserve_or_call(self):
        self.service.config['GEMINI_API_KEY'] = ''
        with self.assertRaises(ServiceError) as caught:
            self.service.extract(self.text)
        self.assertEqual(caught.exception.code, 'GEMINI_NOT_CONFIGURED')
        self.client_factory.assert_not_called()
        self.assertEqual(self.store.usage(), 0)
