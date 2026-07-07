import{r as e}from"./rolldown-runtime-Dte3XhyD.js";import{t}from"./react-D5nPORWt.js";import{a as n,d as r,r as i}from"./context-Djq4bxUc.js";import{n as a}from"./emotion-react.browser.esm-IuRf-uQu.js";import{t as o}from"./arrow-left-Cu6mwwSF.js";import{t as s}from"./circle-x-DUHhOdsX.js";import{t as c}from"./save-Dsib22-K.js";import{C as l,T as u,U as d,V as f,W as p,_ as m,tt as h,x as g}from"./esm-Cnohaohn.js";var _=e(t(),1);function v(){(0,_.useEffect)(()=>(((...t)=>e([r(`_call_script`,{javascript_code:`
(function(){
  if(window.__dekanatGuardInit){ return; }
  window.__dekanatGuardInit=true;
  window.__dekanatDirty=false;
  var onForm=function(){ var p=location.pathname; return /\\/add$/.test(p) || /\\/edit\\//.test(p); };
  var mark=function(){ if(onForm()){ window.__dekanatDirty=true; } };
  document.addEventListener('input', function(e){
    var t=e.target;
    if(t && t.matches && t.matches('input,textarea,select,[contenteditable="true"]')){ mark(); }
  }, true);
  document.addEventListener('change', function(e){
    var t=e.target;
    if(t && t.matches && t.matches('input,textarea,select')){ mark(); }
  }, true);
  document.addEventListener('pointerdown', function(e){
    var t=e.target;
    if(t && t.closest && t.closest('[role="option"],[role="switch"],[role="radio"],[role="checkbox"]')){ mark(); }
  }, true);
  // Скидаємо прапорець при реальній зміні маршруту (React Router — history API).
  var lastPath=location.pathname;
  var reset=function(){ if(location.pathname!==lastPath){ lastPath=location.pathname; window.__dekanatDirty=false; } };
  ['pushState','replaceState'].forEach(function(m){
    var orig=history[m];
    history[m]=function(){ var r=orig.apply(this, arguments); reset(); return r; };
  });
  window.addEventListener('popstate', reset);
  document.addEventListener('click', function(e){
    if(!onForm() || window.__dekanatDirty!==true){ return; }
    var a=e.target.closest ? e.target.closest('a[href]') : null;
    if(!a){ return; }
    if(a.target==='_blank' || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || (typeof e.button==='number' && e.button!==0)){ return; }
    var href=a.getAttribute('href')||'';
    if(!href || href==='#'){ return; }
    if(!window.confirm('Внесені зміни не буде збережено. Ви впевнені, що бажаєте залишити сторінку?')){
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
    } else {
      window.__dekanatDirty=false;
    }
  }, true);
  window.addEventListener('beforeunload', function(e){
    if(onForm() && window.__dekanatDirty===true){ e.preventDefault(); e.returnValue=''; }
  });
})();
`,callback:null},{})],t,{}))(),()=>{}),[]);let[e,t]=(0,_.useContext)(i);return a(p,{css:{display:`none`}})}function y(){(0,_.useEffect)(()=>(((...t)=>e([r(`reflex___state____state.dekanat___states___app____app_state.require_auth`,{},{})],t,{}))(),()=>{}),[]);let[e,t]=(0,_.useContext)(i);return a(h,{as:`p`,size:`3`},`Завантаження...`)}function b(){return a(d,{direction:`row`,gap:`4`},Array.prototype.map.call([`День`,`Період`],((e,t)=>a(h,{as:`label`,key:t,size:`2`},a(d,{gap:`2`},a(u,{disabled:!1,value:(typeof e)?.valueOf?.()===`string`?.valueOf?.()?e:JSON.stringify(e)}),(typeof e)?.valueOf?.()===`string`?.valueOf?.()?e:JSON.stringify(e))))))}function x(){let[e,t]=(0,_.useContext)(i);return a(f,{css:{padding:`0`,width:`2rem`,height:`2rem`},onClick:(0,_.useCallback)((t=>e([r(`_redirect`,{path:`/admission_commission/entrants_group/list`,external:!1,popup:!1,replace:!1},{})],[t],{})),[e,r]),variant:`outline`},a(o,{size:20}))}function S(){let e=(0,_.useContext)(n.reflex___state____state__dekanat___states___app____app_state__dekanat___states___entrant____list_entrant_state);return a(g,{},Array.prototype.map.call(e.speciality_options_rx_state_??[],((e,t)=>a(l,{key:t,value:e?.value},e?.label))))}function C(){let e=(0,_.useContext)(n.reflex___state____state__dekanat___states___app____app_state__dekanat___states___entrant____list_entrant_state);return a(g,{},Array.prototype.map.call(e.entry_base_options_rx_state_??[],((e,t)=>a(l,{key:t,value:e?.value},e?.label))))}function w(){let[e,t]=(0,_.useContext)(i);return a(f,{css:{padding:`0`,width:`2rem`,height:`2rem`},onClick:(0,_.useCallback)((t=>e([r(`reflex___state____state.dekanat___states___app____app_state.dekanat___states___entrant____entrant_form_state.on_cancel`,{},{})],[t],{})),[e,r]),variant:`outline`},a(s,{size:20}))}function T(){let[e,t]=(0,_.useContext)(i);return a(f,{css:{padding:`0`,width:`2rem`,height:`2rem`,color:`white`,backgroundImage:`linear-gradient(135deg, var(--accent-11) 20%, var(--accent-9) 65%)`},onClick:(0,_.useCallback)((t=>e([r(`reflex___state____state.dekanat___states___app____app_state.dekanat___states___entrant____entrant_form_state.on_save`,{},{})],[t],{})),[e,r])},a(c,{size:20}))}function E(){let e=(0,_.useContext)(n.reflex___state____state__dekanat___states___app____app_state__dekanat___states___entrant_application____list_entrant_application_state);return a(g,{},Array.prototype.map.call(e.speciality_options_rx_state_??[],((e,t)=>a(l,{key:t,value:e?.value},e?.label))))}function D(){return a(m,{},(0,_.useContext)(n.reflex___state____state__dekanat___states___app____app_state__dekanat___states___rating____list_rating_state).generated_at_display_rx_state_)}function O(){return a(_.Fragment,{},(0,_.useContext)(n.reflex___state____state__dekanat___states___app____app_state__dekanat___states___rating____list_rating_state).generated_at_display_rx_state_?.valueOf?.()===``?.valueOf?.()?a(_.Fragment,{},a(h,{as:`p`,css:{color:`gray`},size:`2`},`Рейтинг ще не формувався для цієї кампанії`)):a(_.Fragment,{},a(h,{as:`p`,css:{color:`gray`},size:`2`},`Останнє формування: `,a(D,{}))))}export{b as a,S as c,w as i,E as l,T as n,O as o,x as r,C as s,v as t,y as u};