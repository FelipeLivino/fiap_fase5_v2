import unittest
from unittest.mock import create_autospec
from ibm_watson import AssistantV2
from services.watson_service import WatsonService
from services.errors import ServiceError


class WatsonTests(unittest.TestCase):
    def test_missing_credentials(self):
        with self.assertRaises(ServiceError):WatsonService({}).create()

    def test_requests_context_and_keeps_session_id(self):
        service=WatsonService({'WA_ASSISTANT_ID':'test','WA_ENVIRONMENT_ID':'draft-test'})
        service._client=create_autospec(AssistantV2,instance=True)
        service.config.update(WA_API_KEY='test',WA_URL='https://example.invalid')
        service.message('session-test','texto')
        args=service._client.message.call_args.kwargs
        self.assertEqual(args['session_id'],'session-test')
        self.assertEqual(args['environment_id'],'draft-test')
        self.assertEqual(args['user_id'],'session-test')
        self.assertTrue(args['input']['options']['return_context'])

    def test_external_error_is_redacted(self):
        service=WatsonService({'WA_ASSISTANT_ID':'test','WA_ENVIRONMENT_ID':'draft-test','WA_API_KEY':'test','WA_URL':'https://example.invalid'})
        service._client=create_autospec(AssistantV2,instance=True)
        service._client.create_session.side_effect=RuntimeError('SENSITIVE_EXAMPLE')
        with self.assertRaises(ServiceError) as ctx:service.create()
        self.assertNotIn('SENSITIVE_EXAMPLE',str(ctx.exception))
