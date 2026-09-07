const $ = (id) => document.getElementById(id);
const csrf = document.querySelector('meta[name="csrf-token"]').content;
let ready = false;
let busy = false;

async function api(path, body) {
  const response = await fetch(path, {method: body === undefined ? 'GET' : 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
    body: body === undefined ? undefined : JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) {
    if (data.error?.code === 'SESSION_EXPIRED') { ready = false; renderSummary(null); }
    throw new Error(data.error?.message || 'Não foi possível concluir. Tente novamente.');
  }
  return data;
}
function feedback(text='') { $('feedback').textContent = text; }
function message(text, who='bot') {
  $('messages').querySelector('.intro')?.remove();
  const block = document.createElement('div'); block.className = `message ${who}`;
  const label = document.createElement('strong'); label.textContent = who === 'user' ? 'VOCÊ' : 'CARDIOIA';
  const content = document.createElement('span'); content.textContent = text;
  block.append(label, content); $('messages').append(block); $('messages').scrollTop = $('messages').scrollHeight;
}
function renderSummary(summary) {
  $('summary').replaceChildren();
  if (!summary) { const p = document.createElement('p'); p.className='empty'; p.textContent='Ainda não há informações registradas.'; $('summary').append(p); return; }
  const dl = document.createElement('dl');
  const fields = {relato_original:'Relato informado',inicio_relatado:'Início / duração',pressao_arterial:'Pressão informada',frequencia_cardiaca:'Frequência informada',historico_declarado:'Histórico declarado',confirmado_pelo_usuario:'Confirmação do resumo'};
  for (const [key, label] of Object.entries(fields)) {
    const dt=document.createElement('dt'), dd=document.createElement('dd'); dt.textContent=label;
    const value=summary[key]; dd.textContent = typeof value==='boolean' ? (value?'Confirmado':'Aguardando confirmação') : (value?.texto_original || value || 'Não informado'); dl.append(dt,dd);
  } $('summary').append(dl);
}
async function status() {
  const s=await api('/api/status');
  $('watson-status').textContent=s.watson_configured?'Watson configurado':'Watson aguardando configuração';
  $('gemini-status').textContent=`${s.model} · ${s.calls_24h}/${s.local_limit} chamadas locais nas últimas 24h${s.gemini_configured?'':' · Chave não configurada'}`;
  return s;
}
function setBusy(value) {
  busy=value;
  for(const el of document.querySelectorAll('#send,#reset,.suggestions button,#extract,#confirm-extraction'))el.disabled=value;
}
async function send(text) {
  if(busy || !text.trim())return;
  setBusy(true); feedback('Enviando…');
  try {
    if(!ready){const initial=await api('/api/chat/start',{}); ready=true;message(initial.response);renderSummary(initial.summary);}
    message(text,'user'); $('message').value='';
    const data=await api('/api/chat',{message:text});
    if(data.reset)$('messages').replaceChildren();
    message(data.response);renderSummary(data.summary); feedback();
  }catch(error){feedback(error.message);}finally{setBusy(false);}
}
$('chat-form').addEventListener('submit',(e)=>{e.preventDefault();send($('message').value.trim());});
$('message').addEventListener('keydown',(e)=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(e.target.value.trim());}});
document.querySelectorAll('[data-message]').forEach(b=>b.addEventListener('click',()=>send(b.dataset.message)));
$('reset').addEventListener('click',async()=>{if(busy)return;setBusy(true);try{const d=await api('/api/chat/reset',{});$('messages').replaceChildren();ready=true;message(d.response);renderSummary(d.summary);$('confirm-extraction').hidden=true;feedback();}catch(e){feedback(e.message);}finally{setBusy(false);}});
document.querySelectorAll('[data-panel]').forEach(button=>button.addEventListener('click',()=>{
  document.querySelectorAll('.panel').forEach(p=>p.hidden=p.id!==button.dataset.panel);
  if(button.dataset.panel==='conversation')$('messages').scrollTop=$('messages').scrollHeight;
  document.querySelectorAll('[data-panel]').forEach(b=>{b.classList.toggle('active',b===button);if(b===button)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  feedback();if(button.dataset.panel==='automation')loadAutomation();
}));
$('example').addEventListener('click',()=>{$('clinical-text').value='Medi minha pressão: 120/80 mmHg. Não tenho dor. Minha frequência foi 72 bpm.';});
$('extract-form').addEventListener('submit',async(e)=>{
  e.preventDefault();if(busy)return;setBusy(true);feedback('Organizando o relato…');$('confirm-extraction').hidden=true;
  try{
    const d=await api('/api/extract',{message:$('clinical-text').value.trim()});$('extraction-output').replaceChildren();
    for(const f of d.fatos){const card=document.createElement('div');card.className='fact';const title=document.createElement('strong'),meta=document.createElement('small'),quote=document.createElement('blockquote');title.textContent=f.valor;meta.textContent=`${f.campo.replaceAll('_',' ')} · ${f.estado}`;quote.textContent=f.evidencia;card.append(title,meta,quote);$('extraction-output').append(card);}
    if(!d.fatos.length){const p=document.createElement('p');p.textContent='Nenhuma informação dos campos previstos foi encontrada.';$('extraction-output').append(p);}
    const details=document.createElement('details'),caption=document.createElement('summary'),pre=document.createElement('pre');caption.textContent='Ver JSON estruturado';pre.textContent=JSON.stringify(d,null,2);details.append(caption,pre);$('extraction-output').append(details);
    $('confirm-extraction').hidden=!ready||!d.fatos.length;feedback(d.cache?'Resultado reutilizado, sem nova chamada à API.':'Extração pronta para revisão. Nenhum dado foi confirmado automaticamente.');await status();
  }catch(error){feedback(error.message);}finally{setBusy(false);}
});
$('confirm-extraction').addEventListener('click',async()=>{setBusy(true);try{const d=await api('/api/extract/confirm',{});renderSummary(d.summary);message(d.response);$('confirm-extraction').hidden=true;feedback('Relato incluído na conversa para conferência.');}catch(e){feedback(e.message);}finally{setBusy(false);}});
async function loadAutomation(){try{
  const data=await api('/api/automation');const host=$('automation-output');host.replaceChildren();
  if(!data.available){const p=document.createElement('p');p.textContent='O robô ainda não foi iniciado. As execuções aparecerão aqui quando a automação estiver ativa.';host.append(p);return;}
  const stats=document.createElement('div');stats.className='stats';for(const [label,value] of [['Medições',data.measurements],['Anomalias estatísticas',data.alerts],['Eventos pendentes de sincronização',data.pending_events]]){const c=document.createElement('div');c.className='stat';const b=document.createElement('b'),s=document.createElement('span');b.textContent=value;s.textContent=label;c.append(b,s);stats.append(c);}host.append(stats);
  const table=document.createElement('table');const head=document.createElement('tr');for(const title of ['Execução','Situação','Registros processados']){const th=document.createElement('th');th.textContent=title;head.append(th);}table.append(head);for(const row of data.runs){const tr=document.createElement('tr');for(const val of [row.started,row.status,row.processed]){const td=document.createElement('td');td.textContent=val;tr.append(td);}table.append(tr);}host.append(table);
}catch(e){feedback(e.message);}}
$('refresh-automation').addEventListener('click',loadAutomation);
status().catch(e=>feedback(e.message));
