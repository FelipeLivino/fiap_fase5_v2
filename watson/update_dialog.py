"""Atualiza apenas o diálogo CardioIA no rascunho, com cópia anterior local."""
import json
import time
from datetime import datetime, timezone

from config import settings
from services.watson_service import WatsonService
from watson.build_skill import build


def main():
    config = settings()
    client = WatsonService(config).client
    assistant = config['WA_ASSISTANT_ID']
    environment = client.get_environment(assistant, config['WA_ENVIRONMENT_ID']).get_result()
    if environment.get('environment') != 'draft':
        raise RuntimeError('A atualização exige que o aplicativo use o ambiente draft.')
    for attempt in range(6):
        exported = client.export_skills(assistant).get_result()
        if 'assistant_skills' in exported:
            break
        if exported.get('status') == 'Failed':
            raise RuntimeError('A exportação falhou; nenhum diálogo foi alterado.')
        time.sleep(5)
    else:
        raise RuntimeError('Exportação em processamento. Execute novamente em alguns segundos.')
    dialogs = [skill for skill in exported['assistant_skills'] if skill.get('type') == 'dialog']
    if len(dialogs) != 1 or dialogs[0].get('workspace', {}).get('metadata', {}).get('project') != 'CardioIA Fase 5 v2':
        raise RuntimeError('O diálogo remoto não corresponde a este projeto.')
    skill = dialogs[0]
    directory = config['DATA_DIR']
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = directory / f'dialog-before-{stamp}.json'
    backup.write_text(json.dumps(skill, ensure_ascii=False, indent=2), encoding='utf-8')
    definition = build()
    workspace = dict(skill['workspace'])
    for key in ('intents', 'entities', 'dialog_nodes'):
        workspace[key] = definition[key]
    client.update_skill(assistant, skill['skill_id'], workspace=workspace).get_result()
    print(f'Diálogo enviado ao rascunho. Cópia anterior: {backup.name}. Aguarde o treinamento e valide antes de exportar.')


if __name__ == '__main__':
    main()
