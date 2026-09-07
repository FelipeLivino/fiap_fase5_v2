"""Verificação opt-in das APIs reais por HTTP; não faz parte dos testes unitários."""
import json
import re
from pathlib import Path
from datetime import datetime,timezone
import requests

BASE='http://127.0.0.1:5000'

def browser():
    client=requests.Session()
    page=client.get(BASE,timeout=10);page.raise_for_status()
    token=re.search(r'name="csrf-token" content="([^"]+)"',page.text)[1]
    client.headers['X-CSRF-Token']=token
    return client

def main():
    first,second=browser(),browser();records=[]
    def post(path,body=None,client=first):
        response=client.post(BASE+path,json=body or {},timeout=50)
        data=response.json()
        records.append({'path':path,'input':body,'status':response.status_code,'output':data})
        response.raise_for_status()
        return data
    post('/api/chat/start')
    post('/api/chat',{'message':'Quero registrar minha pressão'})
    data=post('/api/chat',{'message':'120/80 mmHg'})
    assert data['summary']['pressao_arterial']['sistolica']==120
    data=post('/api/chat',{'message':'Minha frequência foi 72 bpm'})
    assert data['summary']['pressao_arterial']['sistolica']==120
    assert data['summary']['frequencia_cardiaca']['valor']==72
    post('/api/chat',{'message':'Mostre o resumo'})
    data=post('/api/chat',{'message':'Sim, está correto'})
    assert data['summary']['confirmado_pelo_usuario'] is True
    post('/api/chat',{'message':'Quero corrigir um dado'})
    post('/api/chat',{'message':'pressão'})
    data=post('/api/chat',{'message':'125/82 mmHg'})
    assert data['summary']['pressao_arterial']['sistolica']==125
    assert data['summary']['confirmado_pelo_usuario'] is False
    data=post('/api/chat/start',client=second)
    assert data['summary'] is None
    post('/api/extract',{'message':'Medi minha pressão: 120/80 mmHg. Não tenho dor. Minha frequência foi 72 bpm.'})
    data=post('/api/extract/confirm')
    assert 'Não tenho dor.' in data['summary']['relato_original']
    data=post('/api/chat/reset')
    assert data['summary'] is None
    Path('runtime/live-workflow.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),
        'passed':True,'note':'APIs reais, cenários fictícios, verificação HTTP com dois clientes isolados.','steps':records},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Fluxo real aprovado: contexto, medições, confirmação, correção, isolamento, Gemini + Watson e reinício.')

if __name__=='__main__':
    main()
