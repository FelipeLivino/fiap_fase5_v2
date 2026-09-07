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

# Exemplos de uso cotidiano; não são o conjunto de avaliação.
EXAMPLES['confirmar'] += ['Sim', 'Isso mesmo', 'Tá certo', 'Pode salvar assim']
EXAMPLES['corrigir_informacao'] += ['Na verdade a pressão foi 125/82 mmHg', 'Errei os batimentos, foram 78 bpm', 'Quero corrigir', 'Não está certo']
EXAMPLES['informar_medicao'] += ['Medi agora e deu 120/80 mmHg', 'Meus batimentos deram 72 bpm', 'Quero anotar uma medida']
EXAMPLES.update({
    'agradecer': ['Obrigado', 'Obrigada pela ajuda', 'Valeu', 'Muito obrigado mesmo', 'Agradeço por explicar'],
    'negar': ['Não', 'Não é isso', 'Ainda não', 'Não confirmo', 'Tá errado'],
    'pular': ['Prefiro não responder', 'Não sei informar', 'Não lembro', 'Podemos pular essa pergunta?', 'Não quero contar isso', 'Não sei'],
    'cancelar_etapa': ['Deixa pra lá', 'Quero cancelar essa parte', 'Não quero mais registrar isso', 'Esquece essa pergunta', 'Vamos falar de outra coisa'],
    'repetir': ['Não entendi a pergunta', 'Pode explicar de outro jeito?', 'O que eu preciso escrever?', 'Pode repetir?', 'Fiquei confuso', 'A pergunta não ficou clara', 'Não sei o que preciso responder', 'Não compreendi o que você perguntou'],
    'frustracao': ['Você não está entendendo', 'Já falei isso', 'Estou ficando irritado com esse chat', 'Você fica repetindo a mesma coisa', 'Nada a ver com o que eu disse'],
    'identidade': ['Você é uma pessoa?', 'Estou falando com um robô?', 'Você é médico?', 'Quem está falando comigo?', 'Quero falar com uma pessoa'],
    'fora_escopo': ['Qual a previsão do tempo?', 'Me ajuda com minha lição de matemática', 'Quem ganhou o jogo?', 'Me conta uma piada', 'Qual filme eu vejo hoje?'],
})

QUESTIONS = {
    'pressao': 'Quais foram os dois números da pressão? Escreva como no aparelho, por exemplo: 120/80 mmHg.',
    'frequencia': 'Quantos batimentos por minuto o aparelho mostrou? Pode escrever, por exemplo: 72 bpm.',
    'tipo': 'Você quer anotar a pressão ou os batimentos?',
    'relato': 'O que você gostaria de registrar sobre como está se sentindo?',
    'inicio': 'Desde quando isso acontece? Pode ser algo como “desde ontem”. Se não lembrar, pode dizer.',
    'historico': 'Que informação do seu histórico você quer acrescentar?',
    'corrigir': 'Qual parte precisa mudar: relato, pressão, batimentos ou histórico?',
    'confirmacao': 'O resumo está de acordo com o que você contou? Você pode confirmar ou dizer o que precisa mudar.',
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
        {'entity':'confirmacao_explicita','fuzzy_match':False,'values':[{'value':'confirmar','type':'patterns','patterns':[r'(?i)^\s*(?:conferi e )?confirmo(?: o resumo| os dados| as informações)?[.!]?\s*$']}]},
    ]
    nodes=[]
    def node(identifier,condition,text,**context):
        texts = [text] if isinstance(text, str) else text
        item={'dialog_node':identifier,'type':'standard','title':identifier.replace('_',' ').title(),
              'conditions':condition,'output':{'generic':[{'response_type':'text','values':[{'text':value} for value in texts], 'selection_policy':'sequential'}]},
              'context':dict({'app_action':None,'tentativas':0},**context)}
        if nodes:item['previous_sibling']=nodes[-1]['dialog_node']
        nodes.append(item)
    node('boas_vindas','welcome','Oi! Sou o CardioIA, um assistente virtual. Aqui usamos dados fictícios para organizar relatos e medições. O que você gostaria de anotar hoje?',
         etapa_atual='livre',tentativas=0,resumo_confirmado=False)
    node('urgencia','#relatar_urgencia','Se você acredita estar em uma emergência, procure atendimento de urgência. Esta simulação não avalia risco clínico.',etapa_atual='livre')
    node('reiniciar','#reiniciar','Vamos iniciar uma nova conversa.',etapa_atual='livre')
    nodes[-1]['context']['app_action']='reiniciar'
    node('encerrar','#encerrar','Até mais! Seu resumo continua aqui para você conferir.',etapa_atual='livre')
    node('limites','#solicitar_conduta_medica','Não posso diagnosticar, prescrever ou alterar tratamentos. Leve essas dúvidas a um profissional de saúde.',etapa_atual='livre')
    node('ajuda','#ajuda','Posso registrar relatos fictícios, pressão em mmHg, frequência em bpm e histórico declarado. Também posso mostrar ou corrigir o resumo.')
    node('extrair','#extrair_relato','Se você já tem um texto, abra Organizar relato. Lá você pode conferir cada informação antes de trazer o texto para esta conversa.')
    node('identidade','#identidade','Sou um assistente virtual do projeto CardioIA. Posso ajudar a organizar informações, mas não sou profissional de saúde e este chat não tem atendimento humano.')
    node('cancelar_etapa','#cancelar_etapa','Tudo bem, vamos deixar essa parte. O que já foi anotado continua no resumo. O que você quer fazer agora?',etapa_atual='livre')
    node('fora_escopo','#fora_escopo','Por aqui consigo ajudar com relatos, medições e o resumo. Você quer continuar de onde paramos?')
    for stage, question in QUESTIONS.items():
        node('repetir_'+stage,f"(#repetir || #frustracao) && $etapa_atual == '{stage}'",
             'Vou perguntar de outro jeito. '+question)
        node('agradecer_'+stage,f"#agradecer && $etapa_atual == '{stage}'",'De nada! '+question)
    node('repetir_livre','#repetir || #frustracao','Vamos por partes. Você quer anotar algo, ver o resumo ou corrigir uma informação?')
    node('agradecer','#agradecer',['De nada! Se quiser, podemos acrescentar algo ao resumo.', 'Por nada. Quer conferir o que ficou anotado?'])
    node('pular_inicio',"#pular && $etapa_atual == 'inicio'",'Tudo bem. Vou deixar o período sem informação. Quer conferir o resumo?',inicio_relatado=None,etapa_atual='confirmacao',resumo_confirmado=False)
    node('pular','#pular','Tudo bem, você não precisa informar essa parte. Mantive o que já estava anotado. Quer ver o resumo ou registrar outra coisa?',etapa_atual='livre')
    node('negar_confirmacao',"#negar && $etapa_atual == 'confirmacao'",'Vamos ajustar. Qual parte do resumo precisa mudar?',etapa_atual='corrigir',resumo_confirmado=False)
    node('negar','#negar','Tudo bem. Você quer corrigir alguma informação ou deixar essa parte para depois?')
    node('corrigir_duas_medicoes','#corrigir_informacao && @pressao_arterial && @frequencia_cardiaca',
         'Corrigi a pressão e os batimentos. Confira os dois valores no resumo antes de confirmar.',
         pressao_informada='<? @pressao_arterial.literal ?>',frequencia_informada='<? @frequencia_cardiaca.literal ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    for field, entity_name, context_key, label in [('pressao','pressao_arterial','pressao_informada','pressão'),('frequencia','frequencia_cardiaca','frequencia_informada','frequência')]:
        node('corrigir_valor_'+field,f'#corrigir_informacao && @{entity_name}',
             f'Corrigi a {label} para <? @{entity_name}.literal ?>. Ficou certo agora?',
             **{context_key:f'<? @{entity_name}.literal ?>','etapa_atual':'confirmacao','resumo_confirmado':False})
    for field in ('pressao','frequencia','relato','historico'):
        node('corrigir_campo_'+field,f'#corrigir_informacao && @campo_correcao:{field}',QUESTIONS[field],etapa_atual=field,resumo_confirmado=False)
    node('corrigir','#corrigir_informacao','Qual campo deseja corrigir: relato, pressão, frequência ou histórico?',etapa_atual='corrigir',resumo_confirmado=False)
    for field,stage,question in [('pressao','pressao','Informe a pressão completa em mmHg, por exemplo 120/80 mmHg.'),
                                ('frequencia','frequencia','Informe a frequência com a unidade bpm.'),
                                ('relato','relato','Escreva o relato corrigido.'),('historico','historico','Informe o histórico corrigido.')]:
        node('corrigir_'+field,f"$etapa_atual == 'corrigir' && @campo_correcao:{field}",question,etapa_atual=stage)
    node('receber_duas_medicoes','@pressao_arterial && @frequencia_cardiaca','Anotei a pressão de <? @pressao_arterial.literal ?> e os batimentos de <? @frequencia_cardiaca.literal ?>. Os dois valores estão certos?',
         pressao_informada='<? @pressao_arterial.literal ?>',frequencia_informada='<? @frequencia_cardiaca.literal ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('receber_pressao','@pressao_arterial','Anotei <? @pressao_arterial.literal ?> para a pressão. É esse o valor que você quis registrar?',
         pressao_informada='<? @pressao_arterial.literal ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('receber_frequencia','@frequencia_cardiaca','Anotei <? @frequencia_cardiaca.literal ?> para os batimentos. Está certo?',
         frequencia_informada='<? @frequencia_cardiaca.literal ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('pedir_medicao_pressao',"#informar_medicao && @tipo_medicao:pressao",'Informe a pressão completa em mmHg, por exemplo 120/80 mmHg.',etapa_atual='pressao')
    node('pedir_medicao_frequencia',"#informar_medicao && @tipo_medicao:frequencia",'Informe a frequência com a unidade bpm.',etapa_atual='frequencia')
    node('pedir_tipo','#informar_medicao','Deseja registrar pressão arterial ou frequência cardíaca?',etapa_atual='tipo')
    node('tipo_pressao',"$etapa_atual == 'tipo' && @tipo_medicao:pressao",'Informe a pressão completa em mmHg.',etapa_atual='pressao')
    node('tipo_frequencia',"$etapa_atual == 'tipo' && @tipo_medicao:frequencia",'Informe a frequência com a unidade bpm.',etapa_atual='frequencia')
    node('receber_relato',"$etapa_atual == 'relato'",QUESTIONS['inicio'],relato_original='<? input.text ?>',inicio_relatado=None,etapa_atual='inicio',resumo_confirmado=False)
    node('receber_inicio',"$etapa_atual == 'inicio'",'Anotei esse período junto com o relato. O resumo ficou de acordo com o que você contou?',inicio_relatado='<? input.text ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('receber_historico',"$etapa_atual == 'historico'",'Anotei seu histórico com as suas palavras. Quer conferir se ficou certo no resumo?',historico_declarado='<? input.text ?>',etapa_atual='confirmacao',resumo_confirmado=False)
    node('sintoma_na_frase',"#relatar_sintomas && @sintoma && $etapa_atual != 'inicio'",QUESTIONS['inicio'],relato_original='<? input.text ?>',inicio_relatado=None,etapa_atual='inicio',resumo_confirmado=False)
    node('pedir_relato',"#relatar_sintomas && $etapa_atual != 'relato' && $etapa_atual != 'inicio'",QUESTIONS['relato'],etapa_atual='relato')
    node('pedir_historico',"#informar_historico && $etapa_atual != 'historico'",QUESTIONS['historico'],etapa_atual='historico')
    confirmation = '(#confirmar || @confirmacao_explicita)'
    node('confirmar',f"{confirmation} && $etapa_atual == 'confirmacao'",'Pronto, o resumo ficou confirmado. Quer acrescentar mais alguma coisa?',resumo_confirmado=True,etapa_atual='livre')
    has_data='($relato_original || $pressao_informada || $frequencia_informada || $historico_declarado)'
    node('confirmar_vazio',f'{confirmation} && !{has_data}','Ainda não há nada no resumo para confirmar. O que você quer registrar?',etapa_atual='livre',resumo_confirmado=False)
    node('confirmar_sem_contexto',confirmation,'Antes de confirmar, vamos conferir o resumo. Você pode pedir “ver resumo”.')
    node('resumo_vazio',f'#consultar_resumo && !@confirmacao_explicita && !{has_data}','Seu resumo ainda está vazio. Você quer começar com um relato ou uma medição?',etapa_atual='livre',resumo_confirmado=False)
    node('resumo','#consultar_resumo && !@confirmacao_explicita','Confira o resumo ao lado. O que não foi informado fica em branco. Está tudo certo?',etapa_atual='confirmacao')
    node('termos','#duvida_saude','Pressão arterial descreve a pressão do sangue nas artérias e é expressa em mmHg. Frequência cardíaca é o número de batimentos por minuto (bpm). Estes termos não determinam um diagnóstico.')
    node('saudacao','#saudacao','Olá! Quer registrar um relato, uma medição ou consultar suas informações?')
    node('formato_pressao',"$etapa_atual == 'pressao'",'Não consegui registrar esse formato. Informe os dois valores e a unidade, por exemplo 120/80 mmHg. Você também pode pedir ajuda ou reiniciar.')
    node('formato_frequencia',"$etapa_atual == 'frequencia'",'Informe o valor acompanhado de bpm. Você também pode pedir ajuda ou reiniciar.')
    node('fallback_repetido',"$tentativas >= 1",'Vamos escolher um caminho: relatar sintomas, registrar uma medição, consultar resumo ou reiniciar?',tentativas=0,etapa_atual='livre')
    node('fallback','anything_else',['Não consegui entender o que você quer fazer. Você pode dizer “anotar minha pressão” ou “ver resumo”, por exemplo.', 'Pode me dizer de outro jeito? Eu consigo anotar um relato, uma medição ou ajudar a corrigir o resumo.'],tentativas='<? $tentativas + 1 ?>')
    # Comandos globais precisam preceder a captura de texto livre por etapa.
    priorities=['boas_vindas','urgencia','reiniciar','encerrar','limites','ajuda','extrair','identidade','cancelar_etapa','fora_escopo']
    priorities += [item['dialog_node'] for item in nodes if item['dialog_node'].startswith(('repetir_', 'agradecer_', 'corrigir_duas_', 'corrigir_valor_', 'corrigir_campo_'))]
    priorities += ['agradecer','pular_inicio','pular','negar_confirmacao','negar','corrigir','resumo_vazio','resumo','confirmar_vazio','confirmar','confirmar_sem_contexto','termos','saudacao',
                   'receber_duas_medicoes','receber_pressao','receber_frequencia',
                   'pedir_medicao_pressao','pedir_medicao_frequencia','pedir_tipo','sintoma_na_frase','pedir_relato','pedir_historico']
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
    print('Skill gerada. Importação e validação IBM necessárias.')
