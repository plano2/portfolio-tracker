from flask import Flask, render_template_string, request, jsonify
import json, pathlib, datetime, requests

app = Flask(__name__)
DATA = pathlib.Path(__file__).parent / "portfolio.json"
HTML = r"""
<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portfolio Tracker + Simulator - Abbas</title>
<style>
body{font-family:Vazir,Tahoma,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:20px}
.card{background:#1e293b;border-radius:12px;padding:16px;margin:10px 0}
h1{color:#38bdf8} h2{color:#7dd3fc;margin:10px 0}
table{width:100%;border-collapse:collapse} th,td{padding:8px;border-bottom:1px solid #334155;text-align:center;font-size:13px}
th{background:#0ea5e9;color:white}
.btn{background:#0ea5e9;color:white;border:0;padding:8px 14px;border-radius:8px;cursor:pointer;margin:4px}
.btn:hover{background:#0284c7}
.btn-red{background:#ef4444}.btn-green{background:#10b981}.btn-gray{background:#475569}
input,select{padding:6px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:white}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.port-bar{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:10px;margin:10px 0;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.badge{padding:4px 8px;border-radius:999px;font-size:12px;background:#334155}
.badge-active{background:#0ea5e9;color:white}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head><body>
<h1>💰 پورتفولیو ترکر + شبیه‌ساز — عباس <small style="font-size:13px;color:#94a3b8">واقعی | آزمایشی | مقایسه</small></h1>

<div class="port-bar">
  <b>📂 پورتفولیو فعال:</b>
  <select id="portSelect" style="min-width:220px"></select>
  <button class="btn btn-green" onclick="createPort()">➕ ساخت پورتفولیو جدید</button>
  <button class="btn btn-gray" onclick="renamePort()">✏️ تغییر نام</button>
  <button class="btn btn-red" onclick="deletePort()">🗑 حذف پورتفولیو</button>
  <span id="portInfo" class="badge"></span>
</div>

<div id="compareCard" class="card"><h2>📊 مقایسه پورتفولیوها</h2>
<div style="overflow:auto"><table id="compareTbl"><tr><th>پورتفولیو</th><th>سرمایه اولیه</th><th>ارزش فعلی</th><th>سود/زیان</th><th>بازدهی</th><th>معاملات</th><th>کارمزد</th><th>نقد</th><th>max افت</th><th>سالانه</th></tr></table></div>
<canvas id="compareChart" height="200" style="margin-top:12px"></canvas>
</div>

<div class="card" id="total"></div>
<div class="grid">
<div class="card"><h2>💰 دارایی‌ها</h2><table id="assets"><tr><th>نماد</th><th>مقدار</th><th>میانگین</th><th>قیمت فعلی</th><th>ارزش</th><th>سود/زیان</th><th>سهم</th></tr></table>
<form id="addAsset" style="margin-top:10px"><select name="symbol" required style="width:160px"><option value="BTC">BTC - بیتکوین</option><option value="ETH">ETH - اتریوم</option><option value="PAXG">PAXG - طلای پکس</option><option value="GOLD">GOLD - طلا</option><option value="USDT">USDT - تتر</option><option value="IRT">IRT - تومان</option><option value="SOL">SOL - سولانا</option><option value="BNB">BNB - بایننس کوین</option><option value="USD">USD - دلار نقدی</option></select> <input name="amount" type="number" step="any" placeholder="مقدار" required style="width:90px"> <input name="avg" type="number" step="any" placeholder="میانگین $" required style="width:110px"> <button class="btn">➕ افزودن</button> <button type="button" class="btn btn-red" onclick="clearAssets()">🗑 حذف همه</button></form>
</div>
<div class="card"><h2>⚖️ Allocation</h2><canvas id="alloc" height="200"></canvas></div>
</div>
<div class="card"><h2>🧾 معاملات</h2>
<form id="txForm"><select name="type"><option>خرید</option><option>فروش</option><option>انتقال</option></select> <select name="symbol"><option value="BTC">BTC - بیتکوین</option><option value="ETH">ETH - اتریوم</option><option value="PAXG">PAXG - طلای پکس</option><option value="GOLD">GOLD - طلا</option><option value="USDT">USDT - تتر</option><option value="IRT">IRT - تومان</option><option value="SOL">SOL - سولانا</option><option value="BNB">BNB - بایننس</option><option value="USD">USD - دلار</option></select> <input name="amount" type="number" step="any" placeholder="مقدار" required style="width:90px"> <input name="price" type="number" step="any" placeholder="قیمت $" required style="width:110px"> <input name="fee" type="number" step="any" placeholder="کارمزد" value="0" style="width:80px"> <button class="btn">ثبت</button> <button type="button" class="btn btn-red" onclick="clearTxs()">🗑 حذف همه معاملات</button></form>
<table id="txs" style="margin-top:10px"><tr><th>تاریخ</th><th>نوع</th><th>نماد</th><th>مقدار</th><th>قیمت</th><th>کارمزد</th><th>حذف</th></tr></table>
</div>
<div class="grid">
<div class="card"><h2>📉 نمودار ارزش (فعال)</h2><canvas id="chart" height="180"></canvas></div>
<div class="card"><h2>🔔 هشدار + 💵 نقد و گزارش</h2>
<form id="alertForm"><select name="symbol"><option value="BTC">BTC - بیتکوین</option><option value="ETH">ETH - اتریوم</option><option value="PAXG">PAXG - طلای پکس</option><option value="GOLD">GOLD - طلا</option></select> <input name="target" type="number" step="any" placeholder="قیمت هدف $" required style="width:120px"> <button class="btn">🔔 افزودن هشدار</button></form>
<div id="alerts" style="margin:8px 0"></div>
<hr style="border-color:#334155">
<form id="cashForm">نقد USD: <input name="usd" type="number" step="any" style="width:100px" id="cashUsd"> نرخ USD→تومان: <input name="rate" type="number" style="width:110px" id="rate"> <button class="btn">💾 ذخیره</button></form>
<div style="margin-top:10px"><button class="btn" onclick="report('daily')">📅 گزارش روزانه</button> <button class="btn" onclick="report('weekly')">📅 هفتگی</button></div>
<pre id="report" style="background:#0f172a;padding:10px;border-radius:8px;white-space:pre-wrap;margin-top:10px"></pre>
</div>
</div>
<script>
let data={}, prices={}, portfolios={}, activeId="real";
const faNames={"BTC":"بیتکوین","ETH":"اتریوم","PAXG":"طلای پکس","GOLD":"طلا","USDT":"تتر","IRT":"تومان","SOL":"سولانا","BNB":"بایننس کوین","USD":"دلار نقدی"};
async function load(){
  let r=await fetch('/api/data'); data=await r.json();
  portfolios=data.portfolios||{}; activeId=data.active||"real";
  prices=await (await fetch('/api/prices')).json();
  renderPortSelect(); renderCompare(); render();
}
function renderPortSelect(){
  let sel=document.getElementById('portSelect');
  sel.innerHTML="";
  Object.entries(portfolios).forEach(([id,p])=>{
    let o=document.createElement('option'); o.value=id; o.textContent=(id==="real"?"⭐ ":"🧪 ")+p.name+" ("+id+")";
    if(id===activeId) o.selected=true; sel.appendChild(o);
  });
  sel.onchange=async()=>{ await fetch('/api/portfolios/switch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:sel.value})}); load(); };
  let ap=portfolios[activeId]; document.getElementById('portInfo').textContent= ap ? (ap.strategy||"—")+" | اولیه $"+(ap.initial_capital||0).toLocaleString() : "";
}
async function createPort(){
  let name=prompt("نام پورتفولیو (مثل: آزمایشی ۱ — DCA):"); if(!name) return;
  let strat=prompt("استراتژی (DCA / خرید در اصلاح / BTC/ETH / Altcoin ...):","DCA")||"";
  let cap=parseFloat(prompt("سرمایه اولیه به دلار:","10000")||"10000");
  let r=await fetch('/api/portfolios/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name, strategy:strat, initial_capital:cap})});
  let j=await r.json(); if(j.ok) load(); else alert(j.error||"خطا");
}
async function renamePort(){
  let np=prompt("نام جدید برای "+portfolios[activeId].name+":",portfolios[activeId].name); if(!np) return;
  await fetch('/api/portfolios/rename',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:activeId, name:np})}); load();
}
async function deletePort(){
  if(activeId==="real"){ alert("پورتفولیوی واقعی قابل حذف نیست"); return; }
  if(!confirm("پورتفولیو '"+portfolios[activeId].name+"' حذف شود؟")) return;
  await fetch('/api/portfolios/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:activeId})}); load();
}
async function renderCompare(){
  let cmp=await (await fetch('/api/compare')).json();
  let tbl=document.getElementById('compareTbl');
  tbl.innerHTML='<tr><th>پورتفولیو</th><th>سرمایه اولیه</th><th>ارزش فعلی</th><th>سود/زیان</th><th>بازدهی</th><th>معاملات</th><th>کارمزد</th><th>نقد</th><th>max افت</th><th>سالانه</th></tr>';
  cmp.forEach(c=>{
    let cls=c.pnl>=0?'#4ade80':'#f87171';
    tbl.innerHTML+=`<tr style="${c.id===activeId?'background:#0ea5e920':''}"><td>${c.id==="real"?"⭐":"🧪"} ${c.name}</td><td>$${c.initial.toLocaleString()}</td><td>$${c.current.toLocaleString(undefined,{maximumFractionDigits:0})}</td><td style="color:${cls}">$${c.pnl.toLocaleString(undefined,{maximumFractionDigits:0})}</td><td style="color:${cls}">${c.ret.toFixed(2)}%</td><td>${c.trades}</td><td>$${c.fees.toLocaleString()}</td><td>$${c.cash.toLocaleString()}</td><td>${c.dd.toFixed(1)}%</td><td>${c.annual.toFixed(1)}%</td></tr>`;
  });
  // combined chart
  let hist=await (await fetch('/api/history/combined')).json();
  let ctx=document.getElementById('compareChart').getContext('2d');
  if(window.cmpChart) window.cmpChart.destroy();
  let labels=hist.dates;
  let datasets=hist.series.map((s,i)=>({label:s.name, data:s.values, borderColor:['#38bdf8','#f59e0b','#10b981','#a78bfa','#f43f5e','#06b6d4'][i%6], tension:0.3, fill:false}));
  window.cmpChart=new Chart(ctx,{type:'line', data:{labels, datasets}, options:{plugins:{legend:{labels:{color:'#e2e8f0'}}}, scales:{x:{ticks:{color:'#94a3b8'}}, y:{ticks:{color:'#94a3b8'}}}}});
}
function render(){
  let curData=portfolios[activeId]||{assets:[], cash:{USD:0}, transactions:[], history:[]};
  let total=(curData.cash?.USD||0), vals=[];
  curData.assets.forEach(a=>{let cur=prices[a.symbol]||0; vals.push(a.amount*cur); total+=a.amount*cur;});
  let rate=data.usd_to_toman||60000, toman=total*rate, rial=toman*10;
  let pnl = curData.assets.reduce((s,a)=> s + ((prices[a.symbol]||0)-a.avg_price)*a.amount,0);
  let pnlToman=pnl*rate; let pnlPct=(total-pnl)!=0?(pnl/(total-pnl)*100):0;
  document.getElementById('total').innerHTML=`<b>📊 [${portfolios[activeId]?.name||activeId}] ارزش کل: $${total.toLocaleString(undefined,{maximumFractionDigits:2})} | ${Math.round(toman).toLocaleString()} تومان | ${Math.round(rial).toLocaleString()} ریال<br>💹 سود/زیان: <span style="color:${pnl>=0?'#4ade80':'#f87171'}">$${pnl.toLocaleString(undefined,{maximumFractionDigits:2})} | ${Math.round(pnlToman).toLocaleString()} تومان | ${pnlPct.toFixed(2)}%</span> | سرمایه اولیه $${(portfolios[activeId]?.initial_capital||0).toLocaleString()}</b> <button class="btn" onclick="load()">🔄 بروزرسانی</button>`;
  let tbl=document.getElementById('assets'); tbl.innerHTML='<tr><th>نماد</th><th>مقدار</th><th>میانگین</th><th>قیمت فعلی</th><th>ارزش</th><th>سود/زیان</th><th>سهم</th></tr>';
  let allocLabels=[], allocVals=[];
  curData.assets.forEach((a,i)=>{
    let cur=prices[a.symbol]||0, val=a.amount*cur, pnlA=(cur-a.avg_price)*a.amount, pnlT=pnlA*rate, pct=a.avg_price?((cur-a.avg_price)/a.avg_price*100):0, alloc=total?val/total*100:0;
    tbl.innerHTML+=`<tr><td>${a.symbol} - ${faNames[a.symbol]||""}</td><td>${a.amount}</td><td>$${a.avg_price.toLocaleString()}</td><td>$${cur.toLocaleString()}</td><td>$${val.toLocaleString(undefined,{maximumFractionDigits:0})}</td><td style="color:${pnlA>=0?'#4ade80':'#f87171'}">$${pnlA.toLocaleString(undefined,{maximumFractionDigits:0})}<br><small>${Math.round(pnlT).toLocaleString()} ت | ${pct.toFixed(1)}%</small></td><td>${alloc.toFixed(1)}% <button onclick="delAsset(${i})" title="حذف" style="background:#ef4444;color:white;border:0;border-radius:6px;padding:4px 8px;cursor:pointer">🗑</button></td></tr>`;
    allocLabels.push(a.symbol+" - "+(faNames[a.symbol]||"")); allocVals.push(val);
  });
  document.getElementById('cashUsd').value=curData.cash?.USD||0; document.getElementById('rate').value=rate;
  let txTbl=document.getElementById('txs'); txTbl.innerHTML='<tr><th>تاریخ</th><th>نوع</th><th>نماد</th><th>مقدار</th><th>قیمت</th><th>کارمزد</th><th>حذف</th></tr>';
  let txsAll=curData.transactions||[];
  txsAll.slice().reverse().slice(0,20).forEach(t=>{
    let origIdx=txsAll.lastIndexOf(t);
    txTbl.innerHTML+=`<tr><td>${t.date}</td><td>${t.type}</td><td>${t.symbol}</td><td>${t.amount}</td><td>${t.price}</td><td>${t.fee}</td><td><button onclick="delTx(${origIdx})" style="background:#ef4444;color:white;border:0;border-radius:6px;padding:2px 6px;cursor:pointer">🗑</button></td></tr>`;
  });
  let al=document.getElementById('alerts'); al.innerHTML='';
  (data.alerts||[]).forEach((a,i)=>{
    let cur=prices[a.symbol]||0, reached=cur && cur>=a.target;
    al.innerHTML+=`<div style="padding:4px;border-bottom:1px solid #334155">${a.symbol} هدف $${a.target} (فعلی $${cur}) ${reached?'🔔 رسید!':''} <button onclick="delAlert(${i})" style="color:red;background:none;border:0">حذف</button></div>`;
  });
  drawAlloc(allocLabels, allocVals);
  drawChart(curData.history||[]);
}
function drawAlloc(labels, vals){
  let ctx=document.getElementById('alloc').getContext('2d');
  if(window.allocChart) window.allocChart.destroy();
  window.allocChart=new Chart(ctx,{type:'doughnut', data:{labels, datasets:[{data:vals, backgroundColor:['#0ea5e9','#38bdf8','#7dd3fc','#f59e0b','#10b981','#a78bfa']}]}, options:{plugins:{legend:{labels:{color:'#e2e8f0'}}}}});
}
function drawChart(hist){
  let ctx=document.getElementById('chart').getContext('2d');
  if(window.myChart) window.myChart.destroy();
  window.myChart=new Chart(ctx,{type:'line', data:{labels:hist.map(h=>h.date.slice(5)), datasets:[{label:'ارزش کل $', data:hist.map(h=>h.total), borderColor:'#38bdf8', tension:0.3}]}, options:{plugins:{legend:{labels:{color:'#e2e8f0'}}}, scales:{x:{ticks:{color:'#94a3b8'}}, y:{ticks:{color:'#94a3b8'}}}}});
}
async function delAsset(i){ if(!confirm('حذف شود؟')) return; await fetch('/api/asset/delete',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:i})}); load(); }
async function delAlert(i){ await fetch('/api/alert/delete',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:i})}); load(); }
async function delTx(i){ if(!confirm('این معامله حذف شود؟')) return; await fetch('/api/tx/delete',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:i})}); load(); }
async function clearAssets(){ if(!confirm('همه دارایی‌های این پورتفولیو حذف شوند؟')) return; await fetch('/api/assets/clear',{method:'POST'}); load(); }
async function clearTxs(){ if(!confirm('همه معاملات این پورتفولیو حذف شوند؟')) return; await fetch('/api/txs/clear',{method:'POST'}); load(); }
document.getElementById('addAsset').onsubmit=async e=>{e.preventDefault(); let fd=new FormData(e.target); await fetch('/api/asset/add',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({symbol:fd.get('symbol').toUpperCase(), amount:parseFloat(fd.get('amount')), avg_price:parseFloat(fd.get('avg'))})}); e.target.reset(); load();};
document.getElementById('txForm').onsubmit=async e=>{e.preventDefault(); let fd=new FormData(e.target); await fetch('/api/tx/add',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:fd.get('type'), symbol:fd.get('symbol'), amount:parseFloat(fd.get('amount')), price:parseFloat(fd.get('price')), fee:parseFloat(fd.get('fee')||0)})}); load();};
document.getElementById('alertForm').onsubmit=async e=>{e.preventDefault(); let fd=new FormData(e.target); await fetch('/api/alert/add',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({symbol:fd.get('symbol'), target:parseFloat(fd.get('target'))})}); load();};
document.getElementById('cashForm').onsubmit=async e=>{e.preventDefault(); let fd=new FormData(e.target); await fetch('/api/cash',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({usd:parseFloat(fd.get('usd')), rate:parseFloat(fd.get('rate'))})}); load();};
async function report(p){ let r=await (await fetch('/api/report/'+p)).json(); document.getElementById('report').textContent=r.text; }
load();
</script>
</body></html>
"""

def load_data():
    if DATA.exists():
        d=json.loads(DATA.read_text(encoding="utf-8"))
        # migrate old single-portfolio to multi
        if "portfolios" not in d:
            old_assets=d.get("assets",[]); old_cash=d.get("cash",{"USD":0}); old_txs=d.get("transactions",[]); old_hist=d.get("history",[])
            init = sum(a["amount"]*a.get("avg_price",0) for a in old_assets) + old_cash.get("USD",0)
            if init==0: init=10000
            d={"portfolios":{"real":{"name":"واقعی","strategy":"واقعی","initial_capital":init,"assets":old_assets,"cash":old_cash,"transactions":old_txs,"history":old_hist}},
                "active":"real","alerts":d.get("alerts",[]),"usd_to_toman":d.get("usd_to_toman",60000)}
            save_data(d)
        return d
    return {"portfolios":{"real":{"name":"واقعی","strategy":"واقعی","initial_capital":10000,"assets":[],"cash":{"USD":0},"transactions":[],"history":[]}}, "active":"real","alerts":[],"usd_to_toman":60000}

def save_data(d): DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def get_active(d):
    aid=d.get("active","real")
    return aid, d["portfolios"].get(aid, list(d["portfolios"].values())[0])

def fetch_prices():
    try:
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,pax-gold,tether,solana,binancecoin&vs_currencies=usd", timeout=8)
        j=r.json()
        m={"BTC":j.get("bitcoin",{}).get("usd",0),"ETH":j.get("ethereum",{}).get("usd",0),"PAXG":j.get("pax-gold",{}).get("usd",0),"GOLD":j.get("pax-gold",{}).get("usd",0),"USDT":1,"IRT":1,"USD":1,"SOL":j.get("solana",{}).get("usd",0),"BNB":j.get("binancecoin",{}).get("usd",0)}
        try:
            d=load_data(); rate=d.get("usd_to_toman",60000)
            if rate and rate>0: m["IRT"]=1/rate; m["TOMAN"]=1/rate
        except: pass
        return m
    except: return {"BTC":77000,"ETH":2500,"PAXG":2000,"GOLD":2000,"USD":1,"USDT":1,"IRT":0.00001}

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/api/data")
def api_data(): return jsonify(load_data())

@app.route("/api/prices")
def api_prices(): return jsonify(fetch_prices())

# --- portfolio management ---
@app.route("/api/portfolios/create", methods=["POST"])
def create_port():
    d=load_data(); j=request.json
    name=j.get("name","آزمایشی"); strat=j.get("strategy",""); cap=float(j.get("initial_capital",10000))
    # generate id
    base="sim_"+str(len(d["portfolios"])+1)
    pid=base; n=1
    while pid in d["portfolios"]:
        n+=1; pid=f"sim_{n}"
    d["portfolios"][pid]={"name":name,"strategy":strat,"initial_capital":cap,"assets":[],"cash":{"USD":cap},"transactions":[],"history":[{"date":datetime.date.today().isoformat(),"total":cap}]}
    save_data(d); return jsonify({"ok":True,"id":pid})

@app.route("/api/portfolios/switch", methods=["POST"])
def switch_port():
    d=load_data(); pid=request.json.get("id")
    if pid in d["portfolios"]: d["active"]=pid; save_data(d); return jsonify({"ok":True})
    return jsonify({"ok":False,"error":"not found"}),404

@app.route("/api/portfolios/rename", methods=["POST"])
def rename_port():
    d=load_data(); j=request.json; pid=j.get("id"); name=j.get("name")
    if pid in d["portfolios"]: d["portfolios"][pid]["name"]=name; save_data(d); return jsonify({"ok":True})
    return jsonify({"ok":False}),404

@app.route("/api/portfolios/delete", methods=["POST"])
def delete_port():
    d=load_data(); pid=request.json.get("id")
    if pid=="real": return jsonify({"ok":False,"error":"real cannot be deleted"}),400
    if pid in d["portfolios"]:
        del d["portfolios"][pid]
        if d.get("active")==pid: d["active"]="real"
        save_data(d); return jsonify({"ok":True})
    return jsonify({"ok":False}),404

@app.route("/api/compare")
def api_compare():
    d=load_data(); prices=fetch_prices()
    out=[]
    for pid, p in d["portfolios"].items():
        assets=p.get("assets",[]); cash=p.get("cash",{}).get("USD",0)
        total=sum(a["amount"]*prices.get(a["symbol"],0) for a in assets)+cash
        pnl=sum((prices.get(a["symbol"],0)-a["avg_price"])*a["amount"] for a in assets)
        # fees
        fees=sum(t.get("fee",0) for t in p.get("transactions",[]))
        trades=len(p.get("transactions",[]))
        init=p.get("initial_capital", total-pnl if total-pnl!=0 else 1)
        ret=(pnl/init*100) if init else 0
        # max drawdown from history
        hist=p.get("history",[]); peak=0; dd=0
        for h in hist:
            v=h["total"]
            if v>peak: peak=v
            if peak: dd=min(dd, (v-peak)/peak*100)
        # annualized: (total/init)^(365/days)-1
        annual=0
        if hist and len(hist)>=2 and init:
            try:
                days=(datetime.date.fromisoformat(hist[-1]["date"])-datetime.date.fromisoformat(hist[0]["date"])).days
                if days>0: annual=((total/init)**(365/days)-1)*100
            except: pass
        out.append({"id":pid,"name":p["name"],"initial":init,"current":total,"pnl":pnl,"ret":ret,"trades":trades,"fees":fees,"cash":cash,"dd":dd,"annual":annual})
    return jsonify(out)

@app.route("/api/history/combined")
def api_combined():
    d=load_data()
    # collect all dates
    all_dates=sorted(set(h["date"] for p in d["portfolios"].values() for h in p.get("history",[])))
    series=[]
    for pid,p in d["portfolios"].items():
        mp={h["date"]:h["total"] for h in p.get("history",[])}
        # forward fill
        vals=[]; last=None
        for dt in all_dates:
            if dt in mp: last=mp[dt]
            vals.append(last if last is not None else p.get("initial_capital",0))
        series.append({"id":pid,"name":p["name"],"values":vals})
    return jsonify({"dates":[x[5:] for x in all_dates],"series":series})

# --- per-portfolio asset/tx ops (use active) ---
@app.route("/api/asset/add", methods=["POST"])
def add_asset():
    d=load_data(); aid,_=get_active(d); j=request.json
    d["portfolios"][aid]["assets"].append({"symbol":j["symbol"],"amount":j["amount"],"avg_price":j["avg_price"]}); save_data(d); return jsonify({"ok":True})

@app.route("/api/asset/delete", methods=["POST"])
def del_asset():
    d=load_data(); aid,_=get_active(d); idx=request.json["index"]
    d["portfolios"][aid]["assets"].pop(idx); save_data(d); return jsonify({"ok":True})

@app.route("/api/tx/add", methods=["POST"])
def add_tx():
    d=load_data(); aid,port=get_active(d); j=request.json
    sym=j["symbol"]; amt=j["amount"]; price=j["price"]; fee=j.get("fee",0); typ=j["type"]
    found=next((a for a in port["assets"] if a["symbol"]==sym),None)
    if typ=="خرید":
        if found:
            total_cost=found["amount"]*found["avg_price"]+amt*price+fee
            total_amt=found["amount"]+amt
            found["avg_price"]=total_cost/total_amt if total_amt else 0
            found["amount"]=total_amt
        else: port["assets"].append({"symbol":sym,"amount":amt,"avg_price":price+(fee/amt if amt else 0)})
    elif typ=="فروش":
        if found: found["amount"]=max(0,found["amount"]-amt); port["cash"]["USD"]=port["cash"].get("USD",0)+amt*price-fee
    else:
        if found: found["amount"]=max(0,found["amount"]-amt)
    port["transactions"].append({"date":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"type":typ,"symbol":sym,"amount":amt,"price":price,"fee":fee})
    prices=fetch_prices()
    total=sum(a["amount"]*prices.get(a["symbol"],0) for a in port["assets"])+port["cash"].get("USD",0)
    today=datetime.date.today().isoformat()
    if not port["history"] or port["history"][-1]["date"]!=today: port["history"].append({"date":today,"total":total}); port["history"]=port["history"][-365:]
    save_data(d); return jsonify({"ok":True})

@app.route("/api/tx/delete", methods=["POST"])
def del_tx():
    d=load_data(); aid,port=get_active(d); idx=request.json["index"]
    if 0 <= idx < len(port.get("transactions",[])): port["transactions"].pop(idx); save_data(d)
    return jsonify({"ok":True})

@app.route("/api/assets/clear", methods=["POST"])
def clear_assets():
    d=load_data(); aid,_=get_active(d); d["portfolios"][aid]["assets"]=[]; save_data(d); return jsonify({"ok":True})

@app.route("/api/txs/clear", methods=["POST"])
def clear_txs():
    d=load_data(); aid,_=get_active(d); d["portfolios"][aid]["transactions"]=[]; save_data(d); return jsonify({"ok":True})

@app.route("/api/alert/add", methods=["POST"])
def add_alert():
    d=load_data(); j=request.json; d["alerts"].append({"symbol":j["symbol"],"target":j["target"]}); save_data(d); return jsonify({"ok":True})

@app.route("/api/alert/delete", methods=["POST"])
def del_alert():
    d=load_data(); idx=request.json["index"]; d["alerts"].pop(idx); save_data(d); return jsonify({"ok":True})

@app.route("/api/cash", methods=["POST"])
def cash():
    d=load_data(); aid,port=get_active(d); j=request.json; port["cash"]["USD"]=j["usd"]; d["usd_to_toman"]=j["rate"]; save_data(d); return jsonify({"ok":True})

@app.route("/api/report/<period>")
def report(period):
    d=load_data(); aid,port=get_active(d); prices=fetch_prices()
    total=sum(a["amount"]*prices.get(a["symbol"],0) for a in port["assets"])+port["cash"].get("USD",0)
    pnl=sum(((prices.get(a["symbol"],0)-a["avg_price"])*a["amount"]) for a in port["assets"])
    rate=d.get("usd_to_toman",60000); pnl_toman=pnl*rate; cost=total-pnl; pnl_pct=(pnl/cost*100) if cost else 0
    hist=port.get("history",[]); change=0
    if period=="daily" and len(hist)>=2: change=total-hist[-2]["total"]
    if period=="weekly" and len(hist)>=7: change=total-hist[-7]["total"]
    text=f"📅 گزارش {'روزانه' if period=='daily' else 'هفتگی'} [{port['name']}] - {datetime.date.today()}\nارزش کل: ${total:,.2f} | {total*rate:,.0f} تومان\nسود/زیان: ${pnl:,.2f} | {pnl_toman:,.0f} تومان | {pnl_pct:.2f}%\nتغییر: ${change:,.2f}\n"
    for a in port["assets"]:
        cur=prices.get(a["symbol"],0); pnlA=(cur-a["avg_price"])*a["amount"]; pct=((cur-a["avg_price"])/a["avg_price"]*100) if a["avg_price"] else 0
        text+=f" - {a['symbol']}: {a['amount']} × ${cur:,.0f} = ${a['amount']*cur:,.0f} | سود ${pnlA:,.0f} ({pct:.1f}%)\n"
    return jsonify({"text":text})

if __name__=="__main__":
    import webbrowser, threading, time
    def open_browser():
        time.sleep(1.5)
        try: webbrowser.open("http://127.0.0.1:8081")
        except: pass
    threading.Thread(target=open_browser, daemon=True).start()
    print("Portfolio Tracker + Simulator running at http://127.0.0.1:8081 - browser will open automatically. Do not close this window.")
    app.run(host="0.0.0.0", port=8081, debug=False)
