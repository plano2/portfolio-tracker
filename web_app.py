from flask import Flask, render_template_string, request, jsonify
import json, pathlib, datetime, requests

app = Flask(__name__)
DATA = pathlib.Path(__file__).parent / "portfolio.json"
HTML = r"""
<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portfolio Tracker - Abbas</title>
<style>
body{font-family:Vazir,Tahoma,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:20px}
.card{background:#1e293b;border-radius:12px;padding:16px;margin:10px 0}
h1{color:#38bdf8} h2{color:#7dd3fc;margin:10px 0}
table{width:100%;border-collapse:collapse} th,td{padding:8px;border-bottom:1px solid #334155;text-align:center}
th{background:#0ea5e9;color:white}
.btn{background:#0ea5e9;color:white;border:0;padding:8px 14px;border-radius:8px;cursor:pointer;margin:4px}
.btn:hover{background:#0284c7}
input,select{padding:6px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:white}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head><body>
<h1>💰 پورتفولیو ترکر - عباس <small style="font-size:14px;color:#94a3b8">سبک | محلی | امن</small></h1>
<div class="card" id="total"></div>
<div class="grid">
<div class="card"><h2>💰 دارایی‌ها</h2><table id="assets"><tr><th>نماد</th><th>مقدار</th><th>میانگین</th><th>قیمت فعلی</th><th>ارزش</th><th>سود/زیان</th><th>سهم</th></tr></table>
<form id="addAsset" style="margin-top:10px"><select name="symbol" required style="width:160px"><option value="BTC">BTC - بیتکوین</option><option value="ETH">ETH - اتریوم</option><option value="PAXG">PAXG - طلای پکس</option><option value="GOLD">GOLD - طلا</option><option value="USDT">USDT - تتر</option><option value="IRT">IRT - تومان</option><option value="SOL">SOL - سولانا</option><option value="BNB">BNB - بایننس کوین</option><option value="USD">USD - دلار نقدی</option></select> <input name="amount" type="number" step="any" placeholder="مقدار" required style="width:90px"> <input name="avg" type="number" step="any" placeholder="میانگین $" required style="width:110px"> <button class="btn">➕ افزودن</button> <button type="button" class="btn" style="background:#ef4444" onclick="clearAssets()">🗑 حذف همه دارایی‌ها</button></form>
</div>
<div class="card"><h2>⚖️ Allocation</h2><canvas id="alloc" height="200"></canvas></div>
</div>
<div class="card"><h2>🧾 معاملات</h2>
<form id="txForm"><select name="type"><option>خرید</option><option>فروش</option><option>انتقال</option></select> <select name="symbol"><option value="BTC">BTC - بیتکوین</option><option value="ETH">ETH - اتریوم</option><option value="PAXG">PAXG - طلای پکس</option><option value="GOLD">GOLD - طلا</option><option value="USDT">USDT - تتر</option><option value="IRT">IRT - تومان</option><option value="SOL">SOL - سولانا</option><option value="BNB">BNB - بایننس</option><option value="USD">USD - دلار</option></select> <input name="amount" type="number" step="any" placeholder="مقدار" required style="width:90px"> <input name="price" type="number" step="any" placeholder="قیمت $" required style="width:110px"> <input name="fee" type="number" step="any" placeholder="کارمزد" value="0" style="width:80px"> <button class="btn">ثبت</button> <button type="button" class="btn" style="background:#ef4444" onclick="clearTxs()">🗑 حذف همه معاملات</button></form>
<table id="txs" style="margin-top:10px"><tr><th>تاریخ</th><th>نوع</th><th>نماد</th><th>مقدار</th><th>قیمت</th><th>کارمزد</th><th>حذف</th></tr></table>
</div>
<div class="grid">
<div class="card"><h2>📉 نمودار ارزش</h2><canvas id="chart" height="180"></canvas></div>
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
let data={}, prices={};
const faNames={"BTC":"بیتکوین","ETH":"اتریوم","PAXG":"طلای پکس","GOLD":"طلا","USDT":"تتر","IRT":"تومان","SOL":"سولانا","BNB":"بایننس کوین","USD":"دلار نقدی"};
async function load(){ data=await (await fetch('/api/data')).json(); prices=await (await fetch('/api/prices')).json(); render(); }
function render(){
  let total= (data.cash?.USD||0), vals=[];
  let htmlTotal="", rows="";
  let allocLabels=[], allocVals=[];
  data.assets.forEach(a=>{
    let cur=prices[a.symbol]||0, val=a.amount*cur;
    vals.push(val); total+=val;
  });
  let rate=data.usd_to_toman||60000, toman=total*rate, rial=toman*10;
  let pnl = data.assets.reduce((s,a)=> s + ((prices[a.symbol]||0)-a.avg_price)*a.amount,0);
  let pnlToman = pnl*rate;
  let pnlPct = total-pnl!=0 ? (pnl/(total-pnl)*100) : 0;
  document.getElementById('total').innerHTML=`<b>📊 ارزش کل: $${total.toLocaleString(undefined,{maximumFractionDigits:2})} | ${Math.round(toman).toLocaleString()} تومان | ${Math.round(rial).toLocaleString()} ریال<br>💹 سود/زیان کل: <span style="color:${pnl>=0?'#4ade80':'#f87171'}">$${pnl.toLocaleString(undefined,{maximumFractionDigits:2})} | ${Math.round(pnlToman).toLocaleString()} تومان | ${pnlPct.toFixed(2)}%</span></b> <button class="btn" onclick="load()">🔄 بروزرسانی قیمت</button>`;
  let tbl=document.getElementById('assets'); tbl.innerHTML='<tr><th>نماد</th><th>مقدار</th><th>میانگین</th><th>قیمت فعلی</th><th>ارزش</th><th>سود/زیان</th><th>سهم</th></tr>';
  data.assets.forEach((a,i)=>{
    let cur=prices[a.symbol]||0, val=a.amount*cur, pnlA=(cur-a.avg_price)*a.amount, pnlT=pnlA*(data.usd_to_toman||60000), pnlPct=a.avg_price?((cur-a.avg_price)/a.avg_price*100):0, alloc= total? val/total*100:0;
    tbl.innerHTML+=`<tr><td>${a.symbol} - ${faNames[a.symbol]||""}</td><td>${a.amount}</td><td>$${a.avg_price.toLocaleString()}</td><td>$${cur.toLocaleString()}</td><td>$${val.toLocaleString(undefined,{maximumFractionDigits:0})}</td><td style="color:${pnlA>=0?'#4ade80':'#f87171'}">$${pnlA.toLocaleString(undefined,{maximumFractionDigits:0})}<br><small>${Math.round(pnlT).toLocaleString()} ت | ${pnlPct.toFixed(1)}%</small></td><td>${alloc.toFixed(1)}% <button onclick="delAsset(${i})" title="حذف این دارایی" style="background:#ef4444;color:white;border:0;border-radius:6px;padding:4px 8px;cursor:pointer">🗑 حذف</button></td></tr>`;
    allocLabels.push(a.symbol + " - " + (faNames[a.symbol]||"")); allocVals.push(val);
  });
  document.getElementById('cashUsd').value=data.cash?.USD||0;
  document.getElementById('rate').value=rate;
  // txs
  let txTbl=document.getElementById('txs'); txTbl.innerHTML='<tr><th>تاریخ</th><th>نوع</th><th>نماد</th><th>مقدار</th><th>قیمت</th><th>کارمزد</th><th>حذف</th></tr>';
  let txsAll=data.transactions||[];
  txsAll.slice().reverse().slice(0,20).forEach(t=>{
    let origIdx = txsAll.lastIndexOf(t);
    txTbl.innerHTML+=`<tr><td>${t.date}</td><td>${t.type}</td><td>${t.symbol}</td><td>${t.amount}</td><td>${t.price}</td><td>${t.fee}</td><td><button onclick="delTx(${origIdx})" style="background:#ef4444;color:white;border:0;border-radius:6px;padding:2px 6px;cursor:pointer">🗑</button></td></tr>`});
  // alerts
  let al=document.getElementById('alerts'); al.innerHTML='';
  (data.alerts||[]).forEach((a,i)=>{
    let cur=prices[a.symbol]||0, reached=cur && cur>=a.target;
    al.innerHTML+=`<div style="padding:4px;border-bottom:1px solid #334155">${a.symbol} هدف $${a.target} (فعلی $${cur}) ${reached?'🔔 رسید!':''} <button onclick="delAlert(${i})" style="color:red;background:none;border:0">حذف</button></div>`;
  });
  drawAlloc(allocLabels, allocVals);
  drawChart();
}
function drawAlloc(labels, vals){
  let ctx=document.getElementById('alloc').getContext('2d');
  if(window.allocChart) window.allocChart.destroy();
  window.allocChart=new Chart(ctx,{type:'doughnut', data:{labels, datasets:[{data:vals, backgroundColor:['#0ea5e9','#38bdf8','#7dd3fc','#f59e0b','#10b981']}]}, options:{plugins:{legend:{labels:{color:'#e2e8f0'}}}}});
}
function drawChart(){
  let hist=data.history||[], ctx=document.getElementById('chart').getContext('2d');
  if(window.myChart) window.myChart.destroy();
  window.myChart=new Chart(ctx,{type:'line', data:{labels:hist.map(h=>h.date.slice(5)), datasets:[{label:'ارزش کل $', data:hist.map(h=>h.total), borderColor:'#38bdf8', tension:0.3}]}, options:{plugins:{legend:{labels:{color:'#e2e8f0'}}}, scales:{x:{ticks:{color:'#94a3b8'}}, y:{ticks:{color:'#94a3b8'}}}}});
}
async function delAsset(i){ if(!confirm('حذف شود؟')) return; await fetch('/api/asset/delete',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:i})}); load(); }
async function delAlert(i){ await fetch('/api/alert/delete',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:i})}); load(); }
async function delTx(i){ if(!confirm('این معامله حذف شود؟')) return; await fetch('/api/tx/delete',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:i})}); load(); }
async function clearAssets(){ if(!confirm('همه دارایی‌ها حذف شوند؟')) return; await fetch('/api/assets/clear',{method:'POST'}); load(); }
async function clearTxs(){ if(!confirm('همه معاملات حذف شوند؟')) return; await fetch('/api/txs/clear',{method:'POST'}); load(); }
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
        return json.loads(DATA.read_text(encoding="utf-8"))
    return {"assets":[],"cash":{"USD":0},"transactions":[],"alerts":[],"history":[],"usd_to_toman":60000}

def save_data(d): DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def fetch_prices():
    try:
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,pax-gold,tether,solana,binancecoin&vs_currencies=usd", timeout=8)
        j=r.json()
        m={"BTC":j.get("bitcoin",{}).get("usd",0),"ETH":j.get("ethereum",{}).get("usd",0),"PAXG":j.get("pax-gold",{}).get("usd",0),"GOLD":j.get("pax-gold",{}).get("usd",0),"USDT":1,"IRT":1,"USD":1,"SOL":j.get("solana",{}).get("usd",0),"BNB":j.get("binancecoin",{}).get("usd",0)}
        # IRT (تومان) قیمت دلاری = 1 / نرخ دلار به تومان (اگر تنظیم شده باشد)
        try:
            d=load_data()
            rate=d.get("usd_to_toman",0)
            if rate and rate>0:
                m["IRT"]=1/rate
                m["TOMAN"]=1/rate
        except: pass
        return m
    except: return {"BTC":77000,"ETH":2500,"PAXG":2000,"GOLD":2000,"USD":1,"USDT":1,"IRT":0.00001}

@app.route("/")
def index(): return render_template_string(HTML)

@app.route("/api/data")
def api_data(): return jsonify(load_data())

@app.route("/api/prices")
def api_prices(): return jsonify(fetch_prices())

@app.route("/api/asset/add", methods=["POST"])
def add_asset():
    d=load_data(); j=request.json; d["assets"].append({"symbol":j["symbol"],"amount":j["amount"],"avg_price":j["avg_price"]}); save_data(d); return jsonify({"ok":True})

@app.route("/api/asset/delete", methods=["POST"])
def del_asset():
    d=load_data(); idx=request.json["index"]; d["assets"].pop(idx); save_data(d); return jsonify({"ok":True})

@app.route("/api/tx/add", methods=["POST"])
def add_tx():
    d=load_data(); j=request.json
    sym=j["symbol"]; amt=j["amount"]; price=j["price"]; fee=j.get("fee",0); typ=j["type"]
    found=next((a for a in d["assets"] if a["symbol"]==sym),None)
    if typ=="خرید":
        if found:
            total_cost=found["amount"]*found["avg_price"]+amt*price+fee
            total_amt=found["amount"]+amt
            found["avg_price"]=total_cost/total_amt if total_amt else 0
            found["amount"]=total_amt
        else: d["assets"].append({"symbol":sym,"amount":amt,"avg_price":price+(fee/amt if amt else 0)})
    elif typ=="فروش":
        if found: found["amount"]=max(0,found["amount"]-amt); d["cash"]["USD"]=d["cash"].get("USD",0)+amt*price-fee
    else:
        if found: found["amount"]=max(0,found["amount"]-amt)
    d["transactions"].append({"date":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"type":typ,"symbol":sym,"amount":amt,"price":price,"fee":fee})
    # history
    import requests as req
    prices=fetch_prices()
    total=sum(a["amount"]*prices.get(a["symbol"],0) for a in d["assets"])+d["cash"].get("USD",0)
    today=datetime.date.today().isoformat()
    if not d["history"] or d["history"][-1]["date"]!=today: d["history"].append({"date":today,"total":total}); d["history"]=d["history"][-365:]
    save_data(d); return jsonify({"ok":True})

@app.route("/api/alert/add", methods=["POST"])
def add_alert():
    d=load_data(); j=request.json; d["alerts"].append({"symbol":j["symbol"],"target":j["target"]}); save_data(d); return jsonify({"ok":True})

@app.route("/api/alert/delete", methods=["POST"])
def del_alert():
    d=load_data(); idx=request.json["index"]; d["alerts"].pop(idx); save_data(d); return jsonify({"ok":True})

@app.route("/api/tx/delete", methods=["POST"])
def del_tx():
    d=load_data(); idx=request.json["index"]; 
    if 0 <= idx < len(d.get("transactions",[])): d["transactions"].pop(idx); save_data(d)
    return jsonify({"ok":True})

@app.route("/api/assets/clear", methods=["POST"])
def clear_assets():
    d=load_data(); d["assets"]=[]; save_data(d); return jsonify({"ok":True})

@app.route("/api/txs/clear", methods=["POST"])
def clear_txs():
    d=load_data(); d["transactions"]=[]; save_data(d); return jsonify({"ok":True})

@app.route("/api/cash", methods=["POST"])
def cash():
    d=load_data(); j=request.json; d["cash"]["USD"]=j["usd"]; d["usd_to_toman"]=j["rate"]; save_data(d); return jsonify({"ok":True})

@app.route("/api/report/<period>")
def report(period):
    d=load_data(); prices=fetch_prices()
    total=sum(a["amount"]*prices.get(a["symbol"],0) for a in d["assets"])+d["cash"].get("USD",0)
    pnl=sum(((prices.get(a["symbol"],0)-a["avg_price"])*a["amount"]) for a in d["assets"])
    rate=d.get("usd_to_toman",60000)
    pnl_toman=pnl*rate
    cost=total-pnl
    pnl_pct=(pnl/cost*100) if cost else 0
    hist=d.get("history",[]); change=0
    if period=="daily" and len(hist)>=2: change=total-hist[-2]["total"]
    if period=="weekly" and len(hist)>=7: change=total-hist[-7]["total"]
    text=f"📅 گزارش {'روزانه' if period=='daily' else 'هفتگی'} - {datetime.date.today()}\nارزش کل: ${total:,.2f} | {total*rate:,.0f} تومان\nسود/زیان: ${pnl:,.2f} | {pnl_toman:,.0f} تومان | {pnl_pct:.2f}%\nتغییر: ${change:,.2f}\n"
    for a in d["assets"]:
        cur=prices.get(a["symbol"],0)
        pnlA=(cur-a["avg_price"])*a["amount"]
        pct=((cur-a["avg_price"])/a["avg_price"]*100) if a["avg_price"] else 0
        text+=f" - {a['symbol']}: {a['amount']} × ${cur:,.0f} = ${a['amount']*cur:,.0f} | سود ${pnlA:,.0f} ({pct:.1f}%)\n"
    return jsonify({"text":text})

if __name__=="__main__":
    import webbrowser, threading, time
    def open_browser():
        time.sleep(1.5)
        try: webbrowser.open("http://127.0.0.1:8081")
        except: pass
    threading.Thread(target=open_browser, daemon=True).start()
    print("Portfolio Tracker running at http://127.0.0.1:8081 - browser will open automatically. Do not close this window.")
    app.run(host="0.0.0.0", port=8081, debug=False)
