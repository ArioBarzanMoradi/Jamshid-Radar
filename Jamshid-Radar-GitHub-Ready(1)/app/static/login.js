(()=>{'use strict'; const base=document.body.dataset.base;
const f=document.getElementById('login-form'),b=document.getElementById('submit'),e=document.getElementById('login-error');
f.addEventListener('submit',async ev=>{ev.preventDefault();e.textContent='';b.disabled=true;b.textContent='در حال بررسی...';try{
  const r=await fetch(base+'api/login',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('username').value,password:document.getElementById('password').value})});const j=await r.json();if(!r.ok)throw new Error(j.error||'خطای ورود');window.location.assign(base);
}catch(err){e.textContent=err.message||'خطا در ارتباط';b.disabled=false;b.innerHTML='ورود امن به داشبورد <span>←</span>';}});
})();
