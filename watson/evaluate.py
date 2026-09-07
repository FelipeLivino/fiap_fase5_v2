"""Avaliação real com 42 frases fora do conjunto de treinamento."""
import json
from datetime import datetime,timezone
from config import settings
from services.watson_service import WatsonService

CASES={
 'saudacao':['Boa noite, assistente','Oi, tudo bem por aí?','Olá, vamos conversar?'],
 'ajuda':['Me ensine a usar este assistente','Quais são as funções deste atendimento?','Como posso utilizar o CardioIA?'],
 'relatar_sintomas':['Ando sentindo palpitações ultimamente','Gostaria de descrever o que estou sentindo','Estou cansado e quero registrar isso'],
 'informar_medicao':['Gostaria de anotar o valor da pressão','Podemos salvar uma medida dos meus batimentos?','Vou registrar uma medição arterial'],
 'informar_historico':['Desejo acrescentar meu histórico familiar','Vamos registrar meu histórico de saúde?','Tenho um histórico médico para relatar'],
 'duvida_saude':['Qual o significado da unidade bpm?','Pode explicar o que são batimentos por minuto?','O que quer dizer mmHg?'],
 'solicitar_conduta_medica':['Me diga qual medicamento devo usar','Faça o diagnóstico do meu problema','Devo suspender meu remédio?'],
 'relatar_urgencia':['Estou precisando de socorro urgente','É uma emergência e preciso de ajuda','Quero procurar atendimento de emergência'],
 'consultar_resumo':['Exiba minhas informações reunidas','Quais dados eu já passei nesta conversa?','Gostaria de ver o resumo do atendimento'],
 'confirmar':['Sim, os dados estão certos','Pode considerar essas informações confirmadas','Conferi e confirmo o resumo'],
 'corrigir_informacao':['Gostaria de retificar meu relato','Preciso alterar a pressão que passei','Meu histórico foi informado errado'],
 'reiniciar':['Apague o contexto e comece outra conversa','Quero iniciar tudo novamente','Vamos começar uma conversa do zero'],
 'encerrar':['Podemos finalizar por aqui','Pode terminar este atendimento','Até mais, encerre a conversa'],
 'extrair_relato':['Quero converter este texto em dados estruturados','Pode extrair os dados do meu texto clínico?','Gostaria de transformar meu relato em informações organizadas'],
}

def main():
    config=settings();watson=WatsonService(config);records=[]
    for expected,phrases in CASES.items():
        for text in phrases:
            session=watson.create()
            try:
                response=watson.message(session,text)
                intents=response.get('output',{}).get('intents',[])
                top=intents[0] if intents else {}
                records.append({'input':text,'expected':expected,'predicted':top.get('intent'),
                    'confidence':top.get('confidence'),'correct':top.get('intent')==expected})
            finally:watson.delete(session)
        print(json.dumps({'intent':expected,'correct':sum(r['correct'] for r in records[-3:]),'count':3}),flush=True)
    result={'at':datetime.now(timezone.utc).isoformat(),'cases':records,
        'correct':sum(r['correct'] for r in records),'total':len(records),
        'note':'Amostra acadêmica pequena de frases inéditas. Resultado de classificação não comprova qualidade clínica.'}
    path=config['DATA_DIR']/'watson-evaluation.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
