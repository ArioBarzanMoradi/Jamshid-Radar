(()=>{'use strict';
const base=document.body.dataset.base;
const $=id=>document.getElementById(id);
const esc=value=>String(value??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatRate=n=>{if(!Number.isFinite(+n))return '—';let v=+n*8,u='bps';for(const next of ['Kbps','Mbps','Gbps','Tbps']){if(v<1000)break;v/=1000;u=next;}return `${v>=100?Math.round(v):v.toFixed(1)} ${u}`};
const fmtTime=t=>t?new Date(t*1000).toLocaleTimeString('fa-IR',{hour:'2-digit',minute:'2-digit',second:'2-digit'}):'—';
const fmtUptime=s=>`${Math.floor(s/86400)} روز ${Math.floor((s%86400)/3600)} ساعت`;
const stat=check=>!check?'pending':check.ok?'ok':'bad';
const statusBadge=check=>!check?'<span class="tiny-tag">در انتظار</span>':`<span class="tiny-tag ${check.ok?'green-tag':'yellow-tag'}">${check.ok?'موفق':'بدون پاسخ'}</span>`;
const protocolDescriptions={ipv4_tcp:['IPv4 · TCP','اتصال به 1.1.1.1:443'],ipv6_tcp:['IPv6 · TCP','اتصال به آدرس IPv6 کلادفلر'],dns:['DNS','حل نام example.com'],https:['HTTPS / TLS','درخواست رمزنگاری‌شده Google'],icmp:['ICMP / PING','پاسخ Echo از 1.1.1.1'],udp_stun:['UDP / STUN','تست خروجی UDP به 19302']};
let last=null,loading=false,active='overview';
function selectView(name){active=name;document.querySelectorAll('[data-page]').forEach(el=>el.classList.toggle('current',el.dataset.page===name));document.querySelectorAll('.nav-btn').forEach(el=>el.classList.toggle('active',el.dataset.view===name));const titles={overview:'نمای کلی',connectivity:'دسترسی بین‌الملل',ports:'پورت‌های باز',vpn:'سرویس‌های VPN',network:'رابط‌های شبکه',events:'رویدادها'};$('page-name').textContent=titles[name]||name;$('sidebar').classList.remove('open');window.scrollTo({top:0,behavior:'smooth'});if(name==='ports'&&last)renderPorts(last.data.ports)}
document.querySelectorAll('.nav-btn').forEach(b=>b.addEventListener('click',()=>selectView(b.dataset.view)));
document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>selectView(b.dataset.go)));
$('mobile-menu').addEventListener('click',()=>$('sidebar').classList.toggle('open'));
$('refresh').addEventListener('click',()=>fetchSnapshot());
$('port-search').addEventListener('input',()=>{if(last)renderPorts(last.data.ports)});
$('port-transport').addEventListener('change',()=>{if(last)renderPorts(last.data.ports)});
$('logout').addEventListener('click',async()=>{try{await fetch(base+'api/logout',{method:'POST',credentials:'same-origin'})}finally{window.location.assign(base)}});
function renderProtocols(checks){let mini='',full='';for(const [key,[name,detail]] of Object.entries(protocolDescriptions)){
const c=checks[key],s=stat(c),ms=c?.ms!=null?`${c.ms} ms`:(c?.ok?'موفق':'—');
mini+=`<div class="protocol-box"><div class="protocol-top"><strong>${esc(name)}</strong><i class="dot-status ${s}"></i></div><small>${esc(detail)}</small><div class="latency">${esc(ms)}</div></div>`;
full+=`<div class="protocol-box"><div class="protocol-top"><strong>${esc(name)}</strong><i class="dot-status ${s}"></i></div><small>${esc(detail)}</small><div class="latency">${esc(ms)}</div><div style="margin-top:12px">${statusBadge(c)}</div><small title="${esc(c?.detail||'')}">${esc(c?.detail||'تست در صف اجراست')}</small></div>`;
}$('protocol-mini').innerHTML=mini;$('protocol-details').innerHTML=full;}
function renderTargets(probes){let rows='';for(const t of probes.targets||[]){rows+=`<tr><td><strong>${esc(t.name)}</strong><br><span class="tiny-tag">${esc(t.country)}</span></td><td><span class="mono">${esc(t.host)}:${esc(t.port)}</span></td><td>${statusBadge(t.tcp)} <span class="mono">${t.tcp?.ms==null?'':esc(t.tcp.ms)+'ms'}</span></td><td>${statusBadge(t.icmp)} <span class="mono">${t.icmp?.ms==null?'':esc(t.icmp.ms)+'ms'}</span></td><td class="mono">${esc(fmtTime(t.checked_at))}</td></tr>`}
$('targets-body').innerHTML=rows||'<tr><td colspan="5" class="empty">هنوز مقصدی معرفی نشده یا آزمون آغاز نشده است</td></tr>';$('target-count').textContent=`${(probes.targets||[]).length} هدف`;
const count=(probes.targets||[]).filter(t=>t.ok).length,total=(probes.targets||[]).length;
$('kpi-reach').textContent=total?`${count}/${total}`:'—';$('kpi-reach-caption').textContent=total?'موفق در آزمایش TCP':'در انتظار تست مقصدها';}
function renderPorts(ports){const term=$('port-search').value.trim().toLowerCase(),transport=$('port-transport').value;const visible=ports.filter(p=>(transport==='all'||p.transport===transport)&&(!term||[p.port,p.transport,p.family,p.bind,p.hint].some(v=>String(v).toLowerCase().includes(term))));$('port-counter').textContent=`${visible.length} / ${ports.length}`;let body='';for(const p of visible){body+=`<tr><td><span class="tiny-tag ${p.transport==='TCP'?'blue-tag':'yellow-tag'}">${esc(p.transport)}</span></td><td>${esc(p.family)}</td><td><strong class="mono">${esc(p.port)}</strong></td><td><span class="mono">${esc(p.bind)}</span></td><td><span class="tiny-tag">${esc(p.scope)}</span></td><td>${esc(p.hint)}</td></tr>`}$('ports-body').innerHTML=body||'<tr><td colspan="6" class="empty">پورتی مطابق فیلتر پیدا نشد</td></tr>';}
function renderVpn(services){$('vpn-counter').textContent=`${services.length} سرویس`;const activeCount=services.filter(s=>s.state==='active'||s.state==='interface').length;$('kpi-vpn').textContent=activeCount;let html='';for(const s of services){const ok=s.state==='active'||s.state==='interface';html+=`<div class="vpn-row"><div class="vpn-symbol">◇</div><div><strong>${esc(s.name)}</strong><small>systemd / tunnel interface • ${esc(s.substate)}</small></div><span class="tiny-tag ${ok?'green-tag':'yellow-tag'}">${ok?'فعال / موجود':'غیرفعال'}</span></div>`}
$('vpn-list').innerHTML=html||'<div class="empty">سرویس VPN با نام شناخته‌شده شناسایی نشد. این نتیجه به معنی نصب نبودن یا از کار افتادن همه VPNها نیست.</div>';}
function renderNetwork(n){let ifs='';for(const x of n.interfaces){ifs+=`<div class="interface-row"><div class="if-symbol">⌘</div><div><strong>${esc(x.name)}</strong> ${x.default?'<span class="tiny-tag blue-tag">Default Route</span>':''}<small>IPv4: ${esc(x.ipv4.join(', ')||'—')}</small><small>IPv6: ${esc(x.ipv6.join(', ')||'—')}</small><small>Link Speed: ${esc(x.speed_mbps>0?x.speed_mbps+' Mbps':'نامشخص')}</small></div><span class="tiny-tag ${x.up?'green-tag':'yellow-tag'}">${x.up?'UP':'DOWN'}</span></div>`}$('interfaces-list').innerHTML=ifs||'<div class="empty">رابطی یافت نشد</div>';
let html=`<div class="route-row"><small>رابط مسیر پیش‌فرض</small><strong>${esc(n.device||'نامشخص')}</strong></div><div class="route-row"><small>IPv4 DEFAULT</small><strong>${esc(n.routes.ipv4.map(r=>`${r.gateway||'direct'} via ${r.dev||'?'}`).join(' / ')||'مسیر پیش‌فرض وجود ندارد')}</strong></div><div class="route-row"><small>IPv6 DEFAULT</small><strong>${esc(n.routes.ipv6.map(r=>`${r.gateway||'direct'} via ${r.dev||'?'}`).join(' / ')||'مسیر پیش‌فرض وجود ندارد')}</strong></div><div class="route-row"><small>NAME SERVERS</small><strong>${esc(n.dns.join('  •  ')||'نامشخص')}</strong></div>`;$('routes-list').innerHTML=html;}
function renderEvents(events){const format=e=>`<div class="event"><div class="event-bullet ${e.type==='restored'?'restored':''}">${e.type==='restored'?'✓':'!'}</div><div><strong>${esc(e.message)}</strong><small>${esc(fmtTime(e.time))} • ${e.type==='restored'?'اتصال برقرار شد':'اتصال یا تست ناموفق'}</small></div></div>`;
$('recent-events').innerHTML=events.length?events.slice(0,4).map(format).join(''):'<div class="empty">هنوز تغییر وضعیتی ثبت نشده است</div>';
$('all-events').innerHTML=events.length?events.map(format).join(''):'<div class="empty">تاریخچه فقط از زمان اجرای فعلی سرویس نگهداری می‌شود. هنوز رویدادی ثبت نشده است.</div>';}
function renderChart(history){const svg=$('traffic-chart'),width=660,height=205,left=6,right=6,top=10,bottom=192;
const samples=history.length?history:[{rx:0,tx:0}];const max=Math.max(2048,...samples.map(p=>Math.max(p.rx,p.tx)))*1.2;
const xy=(v,i)=>`${(left+(width-left-right)*i/Math.max(samples.length-1,1)).toFixed(1)},${(bottom-(bottom-top)*Math.min(1,v/max)).toFixed(1)}`;
const rx=samples.map((s,i)=>xy(s.rx,i)).join(' '),tx=samples.map((s,i)=>xy(s.tx,i)).join(' ');
$('rx-line').setAttribute('points',rx);$('tx-line').setAttribute('points',tx);$('rx-area').setAttribute('d',`M ${left},${bottom} L ${rx.replaceAll(' ',' L ')} L ${width-right},${bottom} Z`);
$('gridlines').innerHTML=[0,1,2,3,4].map(i=>`<line x1="0" x2="660" y1="${top+(bottom-top)*i/4}" y2="${top+(bottom-top)*i/4}" stroke="currentColor" stroke-opacity=".12" stroke-dasharray="5 7"/>`).join('');$('chart-max').textContent=formatRate(max);}
function render(json){last=json;const d=json.data,n=d.network,s=d.system,ports=d.ports,pr=json.probes;
$('hero-host').textContent=s.hostname;$('sidebar-host').textContent=s.hostname;
$('last-update').textContent=`به‌روزرسانی: ${fmtTime(d.collected_at)}`;
$('kpi-ports').textContent=d.counts.unique_ports??ports.length;$('kpi-ports-caption').textContent=`${d.counts.tcp} TCP · ${d.counts.udp} UDP`;
$('kpi-speed').textContent=formatRate(n.rx_bps+n.tx_bps);$('kpi-interface').textContent=`روی رابط ${n.device||'نامشخص'}`;
$('rx-label').textContent=formatRate(n.rx_bps);$('tx-label').textContent=formatRate(n.tx_bps);
$('cpu-val').textContent=s.cpu.toFixed(0);$('cpu-gauge').style.setProperty('--percent',Math.max(0,Math.min(100,s.cpu)));
$('ram-val').textContent=s.memory.toFixed(0);$('ram-gauge').style.setProperty('--percent',Math.max(0,Math.min(100,s.memory)));
$('disk-val').textContent=s.disk+'%';$('disk-progress').style.width=Math.max(0,Math.min(100,s.disk))+'%';$('uptime-val').textContent=fmtUptime(s.uptime);
renderChart(json.history);renderProtocols(pr.checks);renderTargets(pr);renderPorts(ports);renderVpn(d.vpn);renderNetwork(n);renderEvents(json.events||[]);
}
async function fetchSnapshot(){if(loading)return;loading=true;try{const r=await fetch(base+'api/snapshot',{credentials:'same-origin',cache:'no-store'});if(r.status===401){window.location.replace(base);return}if(!r.ok)throw Error('HTTP '+r.status);render(await r.json());document.querySelector('.live-pill').innerHTML='<i></i> LIVE DATA';}catch(error){$('last-update').textContent='ارتباط با سرور قطع است';document.querySelector('.live-pill').textContent='CONNECTION LOST';}finally{loading=false}}
fetchSnapshot();setInterval(fetchSnapshot,3000);
})();
