import json
import tempfile
import unittest
from pathlib import Path
from app import create_app
from services.errors import ServiceError


class FakeWatson:
    configured=True
    def __init__(self): self.sessions={}; self.counter=0; self.fail=False
    def create(self):
        self.counter+=1; key=str(self.counter); self.sessions[key]={}; return key
    def delete(self,key): self.sessions.pop(key,None)
    def message(self,key,text='',context=None):
        if self.fail: raise ServiceError('SESSION_EXPIRED','Sessão expirada',409)
        data=self.sessions[key]
        if context: data.update(context)
        if text.startswith('Relato:'): data.update(relato_original=text[7:].strip())
        return {'output':{'generic':[{'response_type':'text','text':'Recebido: '+text}]},
                'context':{'skills':{'main skill':{'user_defined':data}}}}


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.wa=FakeWatson()
        self.app=create_app({'TESTING':True,'SECRET_KEY':'somente-teste','DATA_DIR':Path(self.temp.name)},watson=self.wa)
        self.client=self.app.test_client(); self.client.get('/')
        with self.client.session_transaction() as s: self.csrf=s['csrf']

    def post(self,path,body=None):
        return self.client.post(path,json=body or {},headers={'X-CSRF-Token':self.csrf})

    def test_health_does_not_create_session(self):
        self.assertEqual(self.client.get('/health').status_code,200); self.assertEqual(self.wa.counter,0)

    def test_post_requires_csrf(self):
        self.assertEqual(self.client.post('/api/chat/start',json={}).status_code,403)

    def test_start_is_idempotent(self):
        self.post('/api/chat/start'); self.post('/api/chat/start'); self.assertEqual(self.wa.counter,1)

    def test_suggestions_follow_conversation_without_inserting_measurements(self):
        self.post('/api/chat/start')
        self.wa.sessions['1']['etapa_atual'] = 'pressao'
        result = self.post('/api/chat', {'message': 'Pode explicar?'}).json
        self.assertIn('Prefiro não responder', result['suggestions'])
        self.assertIsNone(result['summary'])
        self.wa.sessions['1']['etapa_atual'] = 'confirmacao'
        result = self.post('/api/chat', {'message': 'Ver resumo'}).json
        self.assertIn('Sim, está correto', result['suggestions'])
        self.assertIn('Quero corrigir um dado', result['suggestions'])

    def test_context_survives_turns(self):
        self.post('/api/chat/start')
        self.post('/api/chat',{'message':'Relato: Não tenho dor'})
        result=self.post('/api/chat',{'message':'Mostre o resumo'}).json
        self.assertEqual(result['summary']['relato_original'],'Não tenho dor')
        self.assertEqual(result['summary']['sintomas_relatados'],[])
        self.assertEqual(self.wa.counter,1)

    def test_reset_clears_context_and_pending(self):
        self.post('/api/chat/start'); self.post('/api/chat',{'message':'Relato: Exemplo'})
        result=self.post('/api/chat/reset').json
        self.assertIsNone(result['summary']); self.assertEqual(len(self.wa.sessions),1)

    def test_independent_browsers(self):
        self.post('/api/chat/start'); self.post('/api/chat',{'message':'Relato: A'})
        other=self.app.test_client();other.get('/')
        with other.session_transaction() as s: token=s['csrf']
        result=other.post('/api/chat/start',json={},headers={'X-CSRF-Token':token})
        self.assertIsNone(result.json['summary']); self.assertEqual(len(self.wa.sessions),2)

    def test_expiration_invalidates_local_session(self):
        self.post('/api/chat/start'); self.wa.fail=True
        self.assertEqual(self.post('/api/chat',{'message':'oi'}).status_code,409)
        with self.client.session_transaction() as s: self.assertNotIn('conversation',s)

    def test_invalid_inputs(self):
        for value in ['',None,123,[],{},'a'*2001]:
            with self.subTest(value=type(value).__name__):
                self.assertEqual(self.post('/api/chat',{'message':value}).status_code,400)

    def test_missing_gemini_does_not_fabricate_extraction(self):
        self.app.extensions['gemini'].config['GEMINI_API_KEY']=''
        result=self.post('/api/extract',{'message':'120/80 mmHg'})
        self.assertEqual(result.status_code,503)
        self.assertEqual(result.json['error']['code'],'GEMINI_NOT_CONFIGURED')

    def test_cookie_contains_no_clinical_text(self):
        self.post('/api/chat/start'); self.post('/api/chat',{'message':'Relato: DADO_FICTICIO'})
        with self.client.session_transaction() as s:
            self.assertEqual(set(s),{'csrf','conversation'})

    def test_no_pending_extraction(self):
        self.post('/api/chat/start')
        self.assertEqual(self.post('/api/extract/confirm').status_code,409)

    def test_errors_dont_expose_internal_exception(self):
        self.wa.message=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('SENSITIVE_EXAMPLE'))
        response=self.post('/api/chat/start')
        self.assertEqual(response.status_code,500)
        self.assertNotIn('SENSITIVE_EXAMPLE',response.text)
