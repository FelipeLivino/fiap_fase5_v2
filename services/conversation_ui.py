"""Atalhos da conversa: sempre sugestões, nunca informações pré-preenchidas."""

DEFAULT_SUGGESTIONS = ['Quero relatar como estou me sentindo', 'Quero registrar uma medição', 'Mostre o resumo']


def suggestions(stage):
    if stage == 'confirmacao':
        return ['Sim, está correto', 'Quero corrigir um dado', 'Quero registrar outra medição']
    if stage == 'corrigir':
        return ['Corrigir pressão', 'Corrigir relato', 'Corrigir histórico']
    if stage == 'tipo':
        return ['Quero registrar minha pressão', 'Quero anotar meus batimentos', 'Deixa pra lá']
    if stage in {'pressao', 'frequencia', 'relato', 'inicio', 'historico'}:
        return ['Não entendi a pergunta', 'Prefiro não responder', 'Deixa pra lá']
    return DEFAULT_SUGGESTIONS.copy()
