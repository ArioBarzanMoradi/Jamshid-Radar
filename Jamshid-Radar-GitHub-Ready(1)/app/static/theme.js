/* Jamshid theme: local-only preference, applied before first paint. */
(()=>{
  'use strict';
  const storageKey='jamshid-theme';
  let theme='dark';
  try { if(localStorage.getItem(storageKey)==='light') theme='light'; } catch (_) {}
  const apply=(next)=>{
    const name=next==='light'?'light':'dark';
    document.documentElement.dataset.theme=name;
    document.documentElement.style.colorScheme=name;
    const meta=document.querySelector('meta[name="theme-color"]');
    if(meta) meta.setAttribute('content',name==='dark'?'#202124':'#F5F1E8');
    document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
      const icon=button.querySelector('[data-theme-icon]');
      const label=button.querySelector('[data-theme-label]');
      if(icon) icon.textContent=name==='dark'?'☾':'☀';
      if(label) label.textContent=name==='dark'?'تم تیره':'تم روشن';
      const action=name==='dark'?'تغییر به تم روشن':'تغییر به تم تیره';
      button.setAttribute('aria-label',action);
      button.setAttribute('title',action);
      button.setAttribute('aria-pressed',String(name==='light'));
    });
  };
  apply(theme);
  document.addEventListener('DOMContentLoaded',()=>{
    apply(theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
      button.addEventListener('click',()=>{
        theme=document.documentElement.dataset.theme==='dark'?'light':'dark';
        apply(theme);
        try { localStorage.setItem(storageKey,theme); } catch (_) {}
      });
    });
  });
})();
