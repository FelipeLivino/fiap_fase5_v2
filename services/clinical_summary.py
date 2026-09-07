import re


def summarize(context):
    data = context.get('skills', {}).get('main skill', {}).get('user_defined', {})
    summary = {key: data.get(key) or None for key in ('relato_original', 'inicio_relatado', 'historico_declarado')}
    summary['sintomas_relatados'] = []  # Uma entidade lexical não comprova sintoma presente.
    summary['pressao_arterial'] = None
    pressure = str(data.get('pressao_informada') or '')
    match = re.fullmatch(r'\s*(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmhg)?\s*', pressure, re.I)
    if match:
        summary['pressao_arterial'] = dict(sistolica=int(match[1]), diastolica=int(match[2]),
                                         unidade='mmHg', texto_original=pressure)
    summary['frequencia_cardiaca'] = None
    heart = str(data.get('frequencia_informada') or '')
    match = re.fullmatch(r'\s*(\d{2,3})\s*bpm\s*', heart, re.I)
    if match:
        summary['frequencia_cardiaca'] = {'valor': int(match[1]), 'unidade': 'bpm', 'texto_original': heart}
    summary['confirmado_pelo_usuario'] = data.get('resumo_confirmado') is True
    return summary if any(summary[k] for k in ('relato_original','inicio_relatado','historico_declarado','pressao_arterial','frequencia_cardiaca')) else None
