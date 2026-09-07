"""Avaliação opt-in do diálogo real, sem Gemini, com frases fictícias.

Execute: docker compose exec app python tests/live_conversation.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import settings
from services.watson_service import WatsonService


# Frases de avaliação diferentes dos novos exemplos de treinamento sempre
# que possível. Asserções sobre estado, não sobre uma redação exata.
CASES = {
    'medicoes_e_correcao': [
        ('Anote 120/80 mmHg e 72 bpm', {'pressao_informada': '120/80 mmHg', 'frequencia_informada': '72 bpm'}),
        ('Conferi e confirmo o resumo', {'resumo_confirmado': True}),
        ('Corrige a pressão para 125/82 mmHg', {'pressao_informada': '125/82 mmHg', 'frequencia_informada': '72 bpm', 'resumo_confirmado': False}),
    ],
    'incerteza_e_agradecimento': [
        ('Quero contar meus sintomas', {'etapa_atual': 'relato'}),
        ('Agradeço a ajuda', {'etapa_atual': 'relato', 'relato_original': None}),
        ('Não sinto dor, só um cansaço leve', {'etapa_atual': 'inicio', 'relato_original': 'Não sinto dor, só um cansaço leve'}),
        ('Não lembro quando começou', {'etapa_atual': 'confirmacao', 'inicio_relatado': None}),
    ],
    'recusa': [
        ('Quero registrar meu histórico', {'etapa_atual': 'historico'}),
        ('Prefiro pular essa parte', {'etapa_atual': 'livre', 'historico_declarado': None}),
    ],
    'reformular_sem_gravar': [
        ('Quero contar meus sintomas', {'etapa_atual': 'relato'}),
        ('Não ficou claro o que preciso responder', {'etapa_atual': 'relato', 'relato_original': None}),
        ('Você não entendeu o que eu pedi', {'etapa_atual': 'relato', 'relato_original': None}),
    ],
    'trocar_de_assunto': [
        ('Quero contar meus sintomas', {'etapa_atual': 'relato'}),
        ('Gostaria de anotar o valor da pressão', {'etapa_atual': 'pressao', 'relato_original': None}),
        ('120/80 mmHg', {'pressao_informada': '120/80 mmHg'}),
        ('Quero acrescentar meu histórico familiar', {'etapa_atual': 'historico'}),
    ],
    'recusar_confirmacao': [
        ('72 bpm', {'etapa_atual': 'confirmacao'}),
        ('Não', {'etapa_atual': 'corrigir', 'resumo_confirmado': False}),
        ('batimentos', {'etapa_atual': 'frequencia'}),
        ('78 bpm', {'frequencia_informada': '78 bpm'}),
    ],
    'resumo_vazio': [
        ('Quero ver o resumo', {'etapa_atual': 'livre', 'resumo_confirmado': False}),
        ('Sim', {'etapa_atual': 'livre', 'resumo_confirmado': False}),
    ],
    'cancelar_preserva_dados': [
        ('72 bpm', {'frequencia_informada': '72 bpm'}),
        ('Quero corrigir meu histórico', {'etapa_atual': 'historico'}),
        ('Quero cancelar essa pergunta', {'etapa_atual': 'livre', 'frequencia_informada': '72 bpm', 'historico_declarado': None}),
    ],
    'identidade_e_escopo': [
        ('Quero contar meus sintomas', {'etapa_atual': 'relato'}),
        ('Você é um atendente humano?', {'etapa_atual': 'relato', 'relato_original': None}),
        ('Me sugere um filme', {'etapa_atual': 'relato', 'relato_original': None}),
    ],
    'limites': [
        ('Quero contar meus sintomas', {'etapa_atual': 'relato'}),
        ('Qual medicamento você recomenda?', {'etapa_atual': 'livre', 'relato_original': None}),
        ('Preciso de socorro urgente', {'etapa_atual': 'livre', 'relato_original': None}),
    ],
}


def main():
    config = settings()
    watson = WatsonService(config)
    records = []
    for name, turns in CASES.items():
        session = watson.create()
        try:
            watson.message(session)
            for text, expected in turns:
                result = watson.message(session, text)
                data = result.get('context', {}).get('skills', {}).get('main skill', {}).get('user_defined', {})
                mismatches = {key: {'expected': value, 'actual': data.get(key)} for key, value in expected.items() if data.get(key) != value}
                record = {'case': name, 'input': text, 'passed': not mismatches, 'mismatches': mismatches,
                          'output': result.get('output', {}).get('generic', []), 'intents': result.get('output', {}).get('intents', [])}
                records.append(record)
                if mismatches:
                    print(json.dumps(record, ensure_ascii=False), flush=True)
            print(f'{name}: concluído', flush=True)
        finally:
            watson.delete(session)
    report = {'at': datetime.now(timezone.utc).isoformat(), 'passed': all(r['passed'] for r in records),
              'total': len(records), 'correct': sum(r['passed'] for r in records), 'steps': records,
              'note': 'API Watson real; cenários sintéticos. Não avalia qualidade clínica nem todos os modos de formular uma mensagem.'}
    (config['DATA_DIR'] / 'conversation-evaluation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"{report['correct']}/{report['total']} turnos aprovados.")
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
