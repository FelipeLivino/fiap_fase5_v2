from urllib.parse import urlparse
from services.errors import ServiceError


class WatsonService:
    def __init__(self, config):
        self.config = config
        self._client = None

    @property
    def configured(self):
        return all(self.config.get(k) for k in ('WA_API_KEY', 'WA_URL', 'WA_ASSISTANT_ID', 'WA_ENVIRONMENT_ID'))

    @property
    def client(self):
        if not self.configured:
            raise ServiceError('WATSON_NOT_CONFIGURED', 'Configure o Watson no .env e reinicie o serviço para conversar.')
        if self._client is None:
            if urlparse(self.config['WA_URL']).scheme != 'https':
                raise ServiceError('WATSON_CONFIG', 'A URL do Watson deve usar HTTPS.')
            from ibm_watson import AssistantV2
            from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
            self._client = AssistantV2(version=self.config['WA_API_VERSION'],
                authenticator=IAMAuthenticator(self.config['WA_API_KEY']))
            self._client.set_service_url(self.config['WA_URL'])
            self._client.set_http_config({'timeout': 25})
            self._client.disable_retries()
        return self._client

    def invoke(self, operation, **kwargs):
        try:
            return getattr(self.client, operation)(assistant_id=self.config['WA_ASSISTANT_ID'],
                environment_id=self.config['WA_ENVIRONMENT_ID'], **kwargs).get_result()
        except ServiceError:
            raise
        except Exception as exc:
            # Não retransmitir mensagens do SDK, URLs ou conteúdo de requisições.
            if getattr(exc, 'code', None) == 404 and operation == 'message':
                raise ServiceError('SESSION_EXPIRED', 'A sessão expirou. Inicie uma nova conversa.', 409) from None
            raise ServiceError('WATSON_UNAVAILABLE', 'Não foi possível acessar o Watson. Confira a configuração e tente novamente.') from None

    def create(self):
        return self.invoke('create_session')['session_id']

    def delete(self, session_id):
        return self.invoke('delete_session', session_id=session_id)

    def message(self, session_id, text='', context=None):
        # Solicitar o contexto atualizado permite montar o resumo e os atalhos da próxima etapa.
        kwargs = {'session_id': session_id, 'user_id': session_id,
                  'input': {'message_type': 'text', 'text': text, 'options': {'return_context': True}}}
        if context is not None:
            kwargs['context'] = {'skills': {'main skill': {'user_defined': context}}}
        return self.invoke('message', **kwargs)
