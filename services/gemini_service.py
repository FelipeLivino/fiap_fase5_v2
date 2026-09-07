"""Extração limitada a evidências literais; nenhuma decisão clínica."""
import hashlib
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from services.errors import ServiceError


class Fact(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    campo: Literal['sintoma', 'pressao_arterial', 'frequencia_cardiaca', 'inicio', 'historico', 'adesao']
    valor: str = Field(min_length=1, max_length=500)
    evidencia: str = Field(min_length=1, max_length=1000)
    estado: Literal['afirmado', 'negado', 'incerto']


class Extraction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    fatos: list[Fact] = Field(max_length=30)


def validate_extraction(raw, source):
    try:
        parsed = Extraction.model_validate_json(raw)
        for fact in parsed.fatos:
            if fact.evidencia not in source or fact.valor not in fact.evidencia:
                raise ValueError('Evidência não literal')
            # Triagem conservadora de possíveis negações, sem alegar validação semântica completa.
            if fact.estado == 'afirmado' and any(word in fact.evidencia.casefold().split()
                                               for word in ('não', 'nego', 'nega', 'sem')):
                raise ValueError('Afirmação possivelmente negada')
        return parsed.model_dump()
    except (ValueError, ValidationError):
        raise ServiceError('INVALID_EXTRACTION',
            'A extração não passou na verificação de formato/evidências. Revise o texto; nenhum dado foi confirmado.', 422) from None


class GeminiService:
    def __init__(self, config, store):
        self.config, self.store = config, store

    @property
    def configured(self):
        return bool(self.config.get('GEMINI_API_KEY'))

    def extract(self, text):
        if not self.configured:
            raise ServiceError('GEMINI_NOT_CONFIGURED', 'Preencha GEMINI_API_KEY no .env e recrie o container.')
        prompt = Path('extensions/generative/prompt.txt').read_text(encoding='utf-8')
        model = self.config['GEMINI_MODEL']
        key = hashlib.sha256((model+'\0'+prompt+'\0'+text).encode()).hexdigest()
        cached = self.store.cached(key)
        if cached is not None:
            return dict(cached, cache=True)
        self.store.reserve_call(self.config['GEMINI_DAILY_LIMIT'], self.config['GEMINI_MIN_INTERVAL_SECONDS'])
        try:
            from google import genai
            from google.genai import types
            with genai.Client(api_key=self.config['GEMINI_API_KEY'], http_options=types.HttpOptions(
                    timeout=30000, retry_options=types.HttpRetryOptions(attempts=1))) as client:
                response = client.models.generate_content(model=model, contents=text,
                    config=types.GenerateContentConfig(system_instruction=prompt,
                        response_mime_type='application/json', response_json_schema=Extraction.model_json_schema(),
                        max_output_tokens=4096))
            result = validate_extraction(response.text or '', text)
        except ServiceError:
            raise
        except Exception as exc:
            code = getattr(exc, 'code', None)
            if code == 429:
                raise ServiceError('GEMINI_QUOTA', 'O Google limitou as chamadas. Tente mais tarde; não haverá repetição automática.', 429) from None
            if code == 404:
                raise ServiceError('GEMINI_MODEL', 'O modelo configurado não está disponível para esta chave. Confira GEMINI_MODEL.', 503) from None
            raise ServiceError('GEMINI_UNAVAILABLE', 'Não foi possível concluir a extração no Gemini. Confira a chave e a disponibilidade do serviço.') from None
        result.update(model=model, texto_original=text, confirmacao_necessaria=True)
        self.store.save_cache(key, result)
        return dict(result, cache=False)
