import { validateCafe, filterCafes, readWorkspace } from './workspace.mjs';
const $ = id => document.getElementById(id);
const storageKey = 'brewdesk-workspace-v1';
let workspace = {cafes:[],saved:[]};
try { workspace = readWorkspace(localStorage.getItem(storageKey)); } catch {}
let view = 'all', catalog = [], matched = [], selected = new Set(), pendingRemove = null, sequence = 0, timer, toastTimer;
const cup = '<svg viewBox="0 0 140 120" aria-hidden="true"><ellipse cx="68" cy="98" rx="51" ry="10" fill="#9aaa90"/><path d="M33 40h63v37a25 25 0 0 1-25 25H58a25 25 0 0 1-25-25z" fill="#fcfaf2"/><path d="M95 47h9a15 15 0 0 1 0 30h-9" fill="none" stroke="#fcfaf2" stroke-width="9"/><ellipse cx="64" cy="40" rx="31" ry="9" fill="#d3b896"/><ellipse cx="64" cy="40" rx="25" ry="6" fill="#805d43"/><path d="M52 26c-7-7 7-9 0-16m21 16c-7-7 7-9 0-16" stroke="#77866c" stroke-width="3" fill="none" stroke-linecap="round"/></svg>';
const bookmark = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h10v14l-5-3-5 3z"/></svg>';
function el(tag, cls, text) { const node = document.createElement(tag); if(cls) node.className = cls; if(text !== undefined) node.textContent = text; return node; }
function toast(text) { clearTimeout(toastTimer); $('toast').textContent=text; $('toast').hidden=false; toastTimer=setTimeout(()=>$('toast').hidden=true,3500); }
function persist() { try { localStorage.setItem(storageKey,JSON.stringify(workspace)); return true; } catch { $('error').textContent='Browser storage is unavailable or full. Changes last only for this visit.'; $('error').hidden=false; return false; } }
function params() { return Object.fromEntries(new FormData($('filters'))); }
function allCafes() { return [...catalog,...workspace.cafes]; }
function formatTime(value) { const [h,m]=value.split(':').map(Number); return `${h%12||12}:${String(m).padStart(2,'0')} ${h>=12?'PM':'AM'}`; }
function render() {
  const options=params();
  for(const key of ['coffee','wifi','power']) $(`${key}-value`).textContent=options[key]==='0'?'Any':`${options[key]}+ / 5`;
  let rows = filterCafes([...matched,...workspace.cafes],options);
  if(view==='saved') rows=rows.filter(c=>workspace.saved.includes(c.id));
  if(view==='personal') rows=rows.filter(c=>typeof c.id==='string');
  $('cards').replaceChildren(...rows.map(card));
  $('count').textContent=`${rows.length} spot${rows.length===1?'':'s'}`;
  $('empty').hidden=rows.length!==0;
  $('empty-message').textContent=view==='personal'?'Add a café to start your personal collection, or reset your filters.':view==='saved'?'Save a spot using its bookmark button, or reset your filters.':'Try another name or loosen your filters.';
  $('compare').textContent=`Compare (${selected.size}/3)`; $('compare').disabled=selected.size<2;
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
}
function card(cafe) {
  const article=el('article','cafe-card');
  const art=el('div',`card-art tone-${String(cafe.id).length % 5}`); art.innerHTML=cup;
  art.append(el('span','tag',cafe.sample?'LEGACY SAMPLE':'MY CAFÉ'));
  const save=el('button','save'); save.type='button'; save.innerHTML=bookmark; save.setAttribute('aria-label',`Save ${cafe.name}`); save.setAttribute('aria-pressed',String(workspace.saved.includes(cafe.id)));
  save.addEventListener('click',()=>{ const has=workspace.saved.includes(cafe.id); workspace.saved=has?workspace.saved.filter(id=>id!==cafe.id):[...workspace.saved,cafe.id]; const saved=persist(); render(); toast(saved?(has?'Removed from saved spots.':'Saved to your shortlist.'):'Updated for this visit only.'); }); art.append(save); article.append(art);
  const content=el('div','card-content'); content.append(el('h3','',cafe.name),el('p','hours',`${formatTime(cafe.open_time)} – ${formatTime(cafe.close_time)}${cafe.open_time>=cafe.close_time?' · overnight':''}`));
  const ratings=el('div','card-ratings'); for(const [key,label] of [['coffee','Coffee'],['wifi','Wi-Fi'],['power','Power']]) { const item=el('div'); const value=el('span','rating-score',String(cafe[`${key}_rating`])); value.append(el('small','',' / 5')); item.append(el('span','rating-label',label),value); ratings.append(item); } content.append(ratings); article.append(content);
  const actions=el('div','card-actions'), link=el('a','','Open map ↗'); link.href=cafe.location; link.target='_blank'; link.rel='noopener noreferrer'; link.setAttribute('aria-label',`Open map for ${cafe.name}`);
  const label=el('label','compare-label'), check=el('input'); check.type='checkbox'; check.checked=selected.has(cafe.id); check.setAttribute('aria-label',`Compare ${cafe.name}`);
  check.addEventListener('change',()=>{ if(check.checked && selected.size>=3){check.checked=false;toast('Choose up to three cafés to compare.');return;} if(check.checked) selected.add(cafe.id); else selected.delete(cafe.id); render(); }); label.append(check,document.createTextNode('Compare')); actions.append(link,label); article.append(actions);
  if(typeof cafe.id==='string') { const personal=el('div','personal-actions'); for(const [label,fn] of [['Edit',()=>openForm(cafe)],['Remove',()=>{pendingRemove=cafe.id;$('remove-dialog').showModal();}]]) { const b=el('button','',label); b.setAttribute('aria-label',`${label} ${cafe.name}`);b.addEventListener('click',fn);personal.append(b); } article.append(personal); }
  return article;
}
async function refresh(initial=false) {
  const requestId=++sequence;
  $('count').textContent='Finding your spots…';
  try { const response=await fetch(`/api/cafes?${new URLSearchParams(params())}`); if(!response.ok) throw new Error('The catalog could not be loaded. Try Apply filters again.'); const data=await response.json(); if(requestId!==sequence)return; matched=data.cafes; if(initial)catalog=data.cafes; else { const known=new Map(catalog.map(c=>[c.id,c])); data.cafes.forEach(c=>known.set(c.id,c));catalog=[...known.values()]; } $('error').hidden=true; render(); }
  catch(error){if(requestId!==sequence)return;$('error').textContent=error.message;$('error').hidden=false;matched=[];render();}
}
function openForm(cafe=null) {
  $('cafe-form').reset(); $('form-error').hidden=true; $('cafe-id').value=cafe?.id||'';
  $('form-title').textContent=cafe?'Edit your café.':'Add your café.';
  for(const [id,key] of [['name','name'],['location','location'],['open','open_time'],['close','close_time'],['coffee','coffee_rating'],['wifi','wifi_rating'],['power','power_rating']]) if(cafe)$(`cafe-${id}`).value=cafe[key];
  $('cafe-dialog').showModal();
}
$('add-cafe').addEventListener('click',()=>openForm());
$('cafe-form').addEventListener('submit',event=>{event.preventDefault();try{
  if(!$('cafe-id').value && workspace.cafes.length>=100)throw new Error('Your personal collection is limited to 100 cafés.');
  const values=Object.fromEntries(new FormData(event.target)); for(const key of ['coffee_rating','wifi_rating','power_rating']) values[key]=Number(values[key]);
  const cafe={...validateCafe(values),id:$('cafe-id').value||`local-${crypto.randomUUID()}`};
  workspace.cafes=workspace.cafes.filter(c=>c.id!==cafe.id).concat(cafe); const saved=persist();
  $('cafe-dialog').close();view='personal';$('filters').reset();refresh();toast(saved?'Your café is saved on this device.':'Your café is available for this visit only.');
}catch(error){$('form-error').textContent=error.message;$('form-error').hidden=false;}});
$('confirm-remove').addEventListener('click',()=>{workspace.cafes=workspace.cafes.filter(c=>c.id!==pendingRemove);workspace.saved=workspace.saved.filter(id=>id!==pendingRemove);selected.delete(pendingRemove);persist();pendingRemove=null;$('remove-dialog').close();render();toast('Personal café removed.');});
$('compare').addEventListener('click',()=>{
  const rows=allCafes().filter(c=>selected.has(c.id)),table=el('table'),head=el('thead'),header=el('tr');header.append(el('th','','Compare'));for(const c of rows)header.append(el('th','',c.name));head.append(header);table.append(head);const body=el('tbody');
  for(const [key,label] of [['coffee_rating','Coffee'],['wifi_rating','Wi-Fi'],['power_rating','Power'],['hours','Hours'],['source','Collection']]){const tr=el('tr');const th=el('th','',label);th.scope='row';tr.append(th);for(const c of rows)tr.append(el('td','',key==='hours'?`${formatTime(c.open_time)} – ${formatTime(c.close_time)}`:key==='source'?(c.sample?'Legacy sample':'Personal'):`${c[key]} / 5`));body.append(tr);}table.append(body);$('comparison').replaceChildren(table);$('compare-dialog').showModal();
});
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>$(b.dataset.close).close()));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;render();}));
$('filters').addEventListener('submit',event=>{event.preventDefault();clearTimeout(timer);refresh();});
$('filters').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>refresh(),180);});
$('clear-filters').addEventListener('click',()=>{$('filters').reset();clearTimeout(timer);refresh();});
refresh(true);
