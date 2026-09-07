"""Exporta o diálogo oficial e registra procedência sem credenciais da instância."""
import json
import time
import hashlib
from datetime import datetime,timezone
from pathlib import Path
from config import settings
from services.watson_service import WatsonService

def main():
    config=settings();client=WatsonService(config).client
    for attempt in range(6):
        exported=client.export_skills(assistant_id=config['WA_ASSISTANT_ID']).get_result()
        if 'assistant_skills' in exported:break
        time.sleep(5)
    else:raise RuntimeError('Exportação ainda não disponível. Tente novamente mais tarde.')
    dialogs=[s for s in exported['assistant_skills'] if s.get('type')=='dialog']
    if len(dialogs)!=1:raise RuntimeError('Esperado exatamente um diálogo no assistente configurado.')
    skill=dialogs[0]
    definition=dict(skill['workspace'],**{k:skill[k] for k in ('name','description','language')})
    directory=config['DATA_DIR'];directory.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(definition,ensure_ascii=False,indent=2)
    (directory/'assistant-skill.json').write_text(payload,encoding='utf-8')
    provenance={'source':'IBM Watson Assistant API v2 export_skills','at':datetime.now(timezone.utc).isoformat(),
        'transformation':'Diálogo extraído de assistant_skills; workspace preservado com name, description e language. Demais skills e estado privado da instância omitidos.',
        'sha256':hashlib.sha256(payload.encode()).hexdigest(),'intents':len(definition['intents']),
        'entities':len(definition['entities']),'dialog_nodes':len(definition['dialog_nodes'])}
    (directory/'export-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(provenance,ensure_ascii=False))

if __name__=='__main__':
    main()
