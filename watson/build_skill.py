"""Gera a skill importável. O JSON final deve ser reexportado após validação IBM."""
import json
from pathlib import Path

EXAMPLES={
 'saudacao':['Olá','Oi, quero começar','Bom dia','Boa tarde','Gostaria de iniciar uma conversa'],
 'ajuda':['Como funciona?','O que você consegue fazer?','Preciso de ajuda para usar o chat','Quais opções estão disponíveis?','Me explique suas funções'],
 'relatar_sintomas':['Quero relatar como estou me sentindo','Sinto palpitações','Tenho sentido cansaço','Quero contar meus sintomas','Estou com tontura hoje'],
 'informar_medicao':['Quero registrar minha pressão','Anotar frequência cardíaca','Tenho uma medição para informar','Posso registrar minha pressão arterial?','Quero informar meus batimentos'],
 'informar_historico':['Quero informar meu histórico de saúde','Tenho informações sobre meu histórico','Quero registrar meu histórico familiar','Posso contar sobre meu histórico?','Gostaria de acrescentar meu histórico'],
 'duvida_saude':['O que significa frequência cardíaca?','O que é pressão arterial?','Explique o termo pressão','O que significa bpm?','O que significa mmHg?'],
 'solicitar_conduta_medica':['Qual remédio devo tomar?','Você pode me dar um diagnóstico?','Qual é minha doença?','Qual dose devo usar?','Posso parar de tomar o medicamento?'],
 'relatar_urgencia':['Preciso de atendimento urgente','Estou em uma emergência','Preciso de socorro agora','Isso é uma urgência','Quero ajuda de emergência'],
 'consultar_resumo':['Mostre o resumo','Quero consultar o resumo','O que já informei?','Veja meus dados registrados','Pode reunir minhas informações?'],
 'confirmar':['Sim, está correto','Confirmo os dados','Isso está certo','Pode confirmar','As informações estão corretas'],
 'corrigir_informacao':['Quero corrigir a medição','Preciso corrigir um dado','Informei errado','Quero alterar meu relato','Pode corrigir meu histórico?'],
 'reiniciar':['Quero começar de novo','Reinicie o atendimento','Nova conversa','Limpe minha conversa','Vamos reiniciar'],
 'encerrar':['Obrigado, pode encerrar','Quero terminar a conversa','Até logo','Tchau','Encerrar atendimento'],
 'extrair_relato':['Quero organizar um texto clínico','Extrair informações do relato','Transformar um relato em JSON','Organize meu texto','Quero usar a extração de informações'],
}


def entity(name,values):
    return {'entity':name,'fuzzy_match':False,'values':[
        {'value':value,'synonyms':synonyms,'type':'synonyms'} for value,synonyms in values.items()]}


def build():
    entities=[
        entity('sintoma',{'palpitacoes':['palpitação','palpitações'],'tontura':['tonto','tonta'],'cansaco':['cansaço','cansado'],'dor':['dor no peito']}),
        entity('tipo_medicao',{'pressao':['pressão','pressão arterial','mmHg'],'frequencia':['frequência','frequência cardíaca','batimentos','bpm']}),
        entity('campo_correcao',{'pressao':['pressão','pressão arterial'],'frequencia':['frequência','batimentos'],'relato':['relato','sintomas'],'historico':['histórico']}),
        {'entity':'pressao_arterial','fuzzy_match':False,'values':[{'value':'medicao','type':'patterns','patterns':[r'(?i)\b\d{2,3}\s*/\s*\d{2,3}\s*mmhg\b']}]},
        {'entity':'frequencia_cardiaca','fuzzy_match':False,'values':[{'value':'medicao','type':'patterns','patterns':[r'(?i)\b\d{2,3}\s*bpm\b']}]},
    ]
    nodes=[]
    def node(identifier,condition,text,**context):
        item={'dialog_node':identifier,'type':'standard','title':identifier.replace('_',' ').title(),
              'conditions':condition,'output':{'generic':[{'response_type':'text','values':[{'text':text}], 'selection_policy':'sequential'}]},
              'context':dict({'app_action':None,'tentativas':0},**context)}
        if nodes:item['previous_sibling']=nodes[-1]['dialog_node']
        nodes.append(item)
    node('boas_vindas','welcome','Olá! Sou o CardioIA. Este é um atendimento acadêmico com dados fictícios. Posso registrar um relato, uma medição ou explicar termos. Como posso ajudar?',
         etapa_atual='livre',tentativas=0,resumo_confirmado=False)
    node('urgencia','#relatar_urgencia','Se você acredita estar em uma emergência, procure atendimento de urgência. Esta simulação não avalia risco clínico.',etapa_atual='livre')
    node('reiniciar','#reiniciar','Vamos iniciar uma nova conversa.',etapa_atual='livre')
    nodes[-1]['context']['app_action']='reiniciar'
    node('encerrar','#encerrar','Conversa encerrada. Você pode iniciar um novo atendimento quando quiser.',etapa_atual='livre')
    node('limites','#solicitar_conduta_medica','Não posso diagnosticar, prescrever ou alterar tratamentos. Leve essas dúvidas a um profissional de saúde.',etapa_atual='livre')
    node('ajuda','#ajuda','Posso registrar relatos fictícios, pressão em mmHg, frequência em bpm e histórico declarado. Também posso mostrar ou corrigir o resumo.')
    node('extrair','#extrair_relato','Use a aba Organizar relato para extrair informações com o Gemini. Você poderá revisar os trechos antes de incluí-los na conversa.')
    node('corrigir','#corrigir_informacao','Qual campo deseja corrigir: relato, pressão, frequência ou histórico?',etapa_atual='corrigir',resumo_confirmado=False)
    for field,stage,question in [('pressao','pressao','Informe a pressão completa em mmHg, por exemplo 120/80 mmHg.'),
                                ('frequencia','frequencia','Informe a frequência com a unidade bpm.'),
                                ('relato','relato','Escreva o relato corrigido.'),('historico','historico','Informe o histórico corrigido.')]:
        node('corrigir_'+field,f"$etapa_atual == 'corrigir' && @campo_correcao:{field}",question,etapa_atual=stage)
    node('receber_pressao','@pressao_arterial','Registrei a pressão informada. Consulte o resumo e confirme se está correto.',
         pressao_informada='<? @pressao_arterial.literal ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('receber_frequencia','@frequencia_cardiaca','Registrei a frequência informada. Consulte o resumo e confirme se está correto.',
         frequencia_informada='<? @frequencia_cardiaca.literal ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('pedir_medicao_pressao',"#informar_medicao && @tipo_medicao:pressao",'Informe a pressão completa em mmHg, por exemplo 120/80 mmHg.',etapa_atual='pressao')
    node('pedir_medicao_frequencia',"#informar_medicao && @tipo_medicao:frequencia",'Informe a frequência com a unidade bpm.',etapa_atual='frequencia')
    node('pedir_tipo','#informar_medicao','Deseja registrar pressão arterial ou frequência cardíaca?',etapa_atual='tipo')
    node('tipo_pressao',"$etapa_atual == 'tipo' && @tipo_medicao:pressao",'Informe a pressão completa em mmHg.',etapa_atual='pressao')
    node('tipo_frequencia',"$etapa_atual == 'tipo' && @tipo_medicao:frequencia",'Informe a frequência com a unidade bpm.',etapa_atual='frequencia')
    node('receber_relato',"$etapa_atual == 'relato'",'Relato registrado. A que período ele se refere?',relato_original='<? input.text ?>',etapa_atual='inicio',resumo_confirmado=False)
    node('receber_inicio',"$etapa_atual == 'inicio'",'Período registrado. Confira o resumo e confirme ou peça uma correção.',inicio_relatado='<? input.text ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('receber_historico',"$etapa_atual == 'historico'",'Histórico declarado registrado. Confira o resumo e confirme ou peça uma correção.',historico_declarado='<? input.text ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('sintoma_na_frase','#relatar_sintomas && @sintoma','Registrei seu relato exatamente como foi informado. A que período ele se refere?',relato_original='<? input.text ?>',etapa_atual='inicio',resumo_confirmado=False)
    node('pedir_relato','#relatar_sintomas','Conte como está se sentindo no cenário fictício.',etapa_atual='relato')
    node('pedir_historico','#informar_historico','Informe o histórico fictício que deseja registrar.',etapa_atual='historico')
    node('confirmar',"#confirmar && $etapa_atual == 'confirmacao'",'Resumo confirmado por você. Deseja registrar mais alguma informação?',resumo_confirmado=True,etapa_atual='livre')
    node('confirmar_sem_contexto','#confirmar','Primeiro consulte o resumo para conferir o que está sendo confirmado.')
    node('resumo','#consultar_resumo','Confira o resumo ao lado. Campos vazios são informações não fornecidas. Está correto?',etapa_atual='confirmacao')
    node('termos','#duvida_saude','Pressão arterial descreve a pressão do sangue nas artérias e é expressa em mmHg. Frequência cardíaca é o número de batimentos por minuto (bpm). Estes termos não determinam um diagnóstico.')
    node('saudacao','#saudacao','Olá! Quer registrar um relato, uma medição ou consultar suas informações?')
    node('formato_pressao',"$etapa_atual == 'pressao'",'Não consegui registrar esse formato. Informe os dois valores e a unidade, por exemplo 120/80 mmHg. Você também pode pedir ajuda ou reiniciar.')
    node('formato_frequencia',"$etapa_atual == 'frequencia'",'Informe o valor acompanhado de bpm. Você também pode pedir ajuda ou reiniciar.')
    node('fallback_repetido',"$tentativas >= 1",'Vamos escolher um caminho: relatar sintomas, registrar uma medição, consultar resumo ou reiniciar?',tentativas=0,etapa_atual='livre')
    node('fallback','anything_else','Não entendi essa mensagem. Pode reformular? Você também pode pedir ajuda ou reiniciar.',tentativas='<? $tentativas + 1 ?>')
    # Comandos globais precisam preceder a captura de texto livre por etapa.
    priorities=['boas_vindas','urgencia','reiniciar','encerrar','limites','ajuda','extrair',
                'corrigir','resumo','confirmar','confirmar_sem_contexto','termos','saudacao']
    nodes.sort(key=lambda item: priorities.index(item['dialog_node']) if item['dialog_node'] in priorities else len(priorities))
    for index,item in enumerate(nodes):
        item.pop('previous_sibling',None)
        if index:
            item['previous_sibling']=nodes[index-1]['dialog_node']
    return {'name':'CardioIA Dialog v2','description':'Simulação acadêmica com dados fictícios. Capítulo 10, pp. 17-37.',
            'language':'pt-br','intents':[{'intent':k,'examples':[{'text':t} for t in v]} for k,v in EXAMPLES.items()],
            'entities':entities,'dialog_nodes':nodes,'metadata':{'project':'CardioIA Fase 5 v2'}}


if __name__=='__main__':
    target=Path('watson/assistant-skill.json')
    target.write_text(json.dumps(build(),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Skill gerada: 14 intenções, 70 exemplos. Importação e validação IBM necessárias.')
