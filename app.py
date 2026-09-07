"""CardioIA: interface local, Watson conversacional e extração Gemini."""
import json
import secrets
from contextlib import closing
from threading import RLock
from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException
from config import settings
from services.errors import ServiceError
from services.storage import Store
from services.watson_service import WatsonService
from services.gemini_service import GeminiService
from services.clinical_summary import summarize
from services.conversation_ui import suggestions


def create_app(overrides=None, watson=None, gemini=None):
    app = Flask(__name__)
    app.config.update(settings())
    app.config.update(overrides or {})
    if not app.config['SECRET_KEY']:
        raise RuntimeError('Defina FLASK_SECRET_KEY no .env antes de iniciar.')
    store = Store(app.config['DATA_DIR'])
    watson = watson or WatsonService(app.config)
    gemini = gemini or GeminiService(app.config, store)
    lock = RLock()  # Um worker; serializa operações de sessão e evita duplicar a mesma extração.
    app.extensions.update(store=store, watson=watson, gemini=gemini)

    @app.before_request
    def check_csrf():
        if request.method == 'POST':
            expected = session.get('csrf')
            actual = request.headers.get('X-CSRF-Token', '')
            if not expected or not secrets.compare_digest(expected, actual):
                raise ServiceError('CSRF', 'Recarregue a página antes de enviar.', 403)

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    @app.errorhandler(ServiceError)
    def service_error(exc):
        return jsonify(error={'code': exc.code, 'message': exc.message}), exc.status

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error={'code': 'INVALID_REQUEST', 'message': 'Requisição inválida ou conteúdo excessivo.'}), exc.code

    @app.errorhandler(Exception)
    def internal_error(exc):
        app.logger.error('Erro interno: %s', type(exc).__name__)
        return jsonify(error={'code': 'INTERNAL_ERROR', 'message': 'Não foi possível concluir a operação.'}), 500

    def message_text(limit):
        if not request.is_json:
            raise ServiceError('INVALID_REQUEST', 'Envie uma mensagem em JSON.', 400)
        body = request.get_json()
        value = body.get('message') if isinstance(body, dict) else None
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
            raise ServiceError('INVALID_MESSAGE', f'Informe um texto de 1 a {limit} caracteres.', 400)
        return value.strip()

    def conversation():
        token = session.get('conversation')
        row = store.get(token) if token else None
        if not row:
            raise ServiceError('SESSION_EXPIRED', 'Inicie uma nova conversa para continuar.', 409)
        return token, row

    def convert(response, token):
        context = response.get('context', {})
        data = context.get('skills', {}).get('main skill', {}).get('user_defined', {})
        summary = summarize(context)
        store.update(token, 'summary', summary)
        texts = [x['text'] for x in response.get('output', {}).get('generic', [])
                 if x.get('response_type') == 'text' and isinstance(x.get('text'), str)]
        return {'response': '\n'.join(texts) or 'Não reconheci essa entrada. Pode reformular?',
                'summary': summary, 'action': data.get('app_action'),
                'suggestions': suggestions(data.get('etapa_atual'))}

    def start_new():
        old_token = session.get('conversation')
        old = store.get(old_token) if old_token else None
        wa_id = watson.create()
        token = secrets.token_urlsafe(32)
        try:
            response = watson.message(wa_id)
        except ServiceError:
            try:
                watson.delete(wa_id)
            except ServiceError:
                pass
            raise
        store.create(token, wa_id)
        session['conversation'] = token
        if old:
            store.delete(old_token)
            try:
                watson.delete(old['wa_id'])
            except ServiceError:
                pass  # A sessão remota restante expira; o contexto local já foi separado.
        return convert(response, token)

    @app.get('/')
    def index():
        session.setdefault('csrf', secrets.token_urlsafe(32))
        return render_template('index.html', csrf=session['csrf'])

    @app.get('/health')
    def health():
        return jsonify(status='ok')

    @app.get('/api/status')
    def status():
        return jsonify(watson_configured=watson.configured, gemini_configured=gemini.configured,
                       model=app.config['GEMINI_MODEL'], calls_24h=store.usage(),
                       local_limit=app.config['GEMINI_DAILY_LIMIT'])

    @app.get('/api/automation')
    def automation_status():
        import sqlite3
        path=app.config['DATA_DIR']/'automation.sqlite3'
        if not path.exists():
            return jsonify(available=False)
        with closing(sqlite3.connect(f'file:{path}?mode=ro',uri=True,timeout=5)) as db:
            db.row_factory=sqlite3.Row
            count=db.execute("SELECT count(*) FROM measurements WHERE dataset='monitoramento'").fetchone()[0]
            alerts=db.execute('SELECT count(*) FROM alerts').fetchone()[0]
            pending=db.execute('SELECT count(*) FROM outbox WHERE delivered=0').fetchone()[0]
            runs=[dict(r) for r in db.execute('SELECT started,status,processed FROM runs ORDER BY started DESC LIMIT 10')]
        return jsonify(available=True,measurements=count,alerts=alerts,pending_events=pending,runs=runs)

    @app.post('/api/chat/start')
    def start():
        with lock:
            token = session.get('conversation')
            row = store.get(token) if token else None
            if row:
                return jsonify(response='Conversa retomada. Como posso ajudar?', summary=json.loads(row['summary']) if row['summary'] else None)
            return jsonify(start_new())

    @app.post('/api/chat/reset')
    def reset():
        with lock:
            return jsonify(start_new())

    @app.post('/api/chat')
    def chat():
        text = message_text(2000)
        with lock:
            token, row = conversation()
            try:
                result = convert(watson.message(row['wa_id'], text), token)
            except ServiceError as exc:
                if exc.code == 'SESSION_EXPIRED':
                    store.delete(token)
                    session.pop('conversation', None)
                raise
            if result.pop('action', None) == 'reiniciar':
                return jsonify(**start_new(), reset=True)
            return jsonify(result)

    @app.post('/api/extract')
    def extract():
        text = message_text(6000)
        with lock:
            result = gemini.extract(text)
            token = session.get('conversation')
            if token and store.get(token):
                store.update(token, 'pending', result)
            return jsonify(result)

    @app.post('/api/extract/confirm')
    def confirm():
        with lock:
            token, row = conversation()
            if not row['pending']:
                raise ServiceError('NO_EXTRACTION', 'Não há extração pendente nesta conversa.', 409)
            result = json.loads(row['pending'])
            # Conservar a extração como declaração textual; não converter fatos incertos em diagnóstico.
            response = watson.message(row['wa_id'], 'Quero consultar o resumo', context={
                'relato_original': result['texto_original'], 'extracao_confirmada': result['fatos'],
                'resumo_confirmado': False, 'app_action': None})
            store.update(token, 'pending', None)
            return jsonify(convert(response, token))

    return app


# Importar create_app em testes não exige configuração de execução.
if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=5000, debug=False)
