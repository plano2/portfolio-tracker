
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os, datetime, threading, requests
from pathlib import Path

# Try matplotlib
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except:
    HAS_MPL = False

DATA_FILE = Path(__file__).parent / "portfolio.json"
USD_TO_TOMAN = 60000  # default, user can change - 1 USD = 60000 Toman approx

SYMBOLS = {
    "BTC": ("bitcoin", "Bitcoin"),
    "ETH": ("ethereum", "Ethereum"),
    "PAXG": ("pax-gold", "PAX Gold"),
    "USDT": ("tether", "Tether"),
    "BNB": ("binancecoin", "BNB"),
    "SOL": ("solana", "Solana"),
    "GOLD": ("pax-gold", "Gold (via PAXG)"),
    "USD": (None, "US Dollar Cash"),
}

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except: pass
    return {
        "assets": [
            {"symbol": "BTC", "amount": 0.05, "avg_price": 65000},
            {"symbol": "ETH", "amount": 1.2, "avg_price": 2500},
            {"symbol": "PAXG", "amount": 2, "avg_price": 2000},
        ],
        "cash": {"USD": 500, "TOMAN": 0},
        "transactions": [],
        "alerts": [],
        "history": [],
        "usd_to_toman": USD_TO_TOMAN
    }

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def fetch_prices(symbols):
    ids = []
    mapping = {}
    for s in symbols:
        if s in SYMBOLS and SYMBOLS[s][0]:
            ids.append(SYMBOLS[s][0])
            mapping[SYMBOLS[s][0]] = s
    if not ids:
        return {}
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(set(ids))}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        j = r.json()
        out = {}
        for cid, sym in mapping.items():
            if cid in j:
                out[sym] = j[cid]["usd"]
        # USD cash =1, GOLD use PAXG
        if "PAXG" in out:
            out["GOLD"] = out["PAXG"]
        out["USD"] = 1
        out["USDT"] = 1
        return out
    except Exception as e:
        print("price fetch error", e)
        return {}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Portfolio Tracker - Abbas | سبک و شخصی")
        self.geometry("1050x680")
        self.data = load_data()
        self.prices = {}
        self.create_widgets()
        self.refresh_prices()

    def create_widgets(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        self.total_label = ttk.Label(top, text="در حال محاسبه...", font=("Vazir", 14, "bold"))
        self.total_label.pack(side="left")
        ttk.Button(top, text="🔄 بروزرسانی قیمت", command=self.refresh_prices).pack(side="right", padx=5)
        ttk.Button(top, text="💾 ذخیره", command=lambda: [save_data(self.data), messagebox.showinfo("ذخیره", "ذخیره شد")]).pack(side="right")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_assets = ttk.Frame(nb); nb.add(self.tab_assets, text="💰 دارایی‌ها و ⚖️ Allocation")
        self.tab_tx = ttk.Frame(nb); nb.add(self.tab_tx, text="🧾 معاملات")
        self.tab_chart = ttk.Frame(nb); nb.add(self.tab_chart, text="📉 نمودار")
        self.tab_alert = ttk.Frame(nb); nb.add(self.tab_alert, text="🔔 هشدار")
        self.tab_report = ttk.Frame(nb); nb.add(self.tab_report, text="📅 گزارش و 💵 Cash")

        self.build_assets_tab()
        self.build_tx_tab()
        self.build_chart_tab()
        self.build_alert_tab()
        self.build_report_tab()

    def build_assets_tab(self):
        f = self.tab_assets
        cols = ("symbol", "amount", "avg_price", "cur_price", "value", "pnl", "alloc")
        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=12)
        for c, w, t in [("symbol",80,"نماد"),("amount",100,"مقدار"),("avg_price",110,"میانگین خرید $"),("cur_price",110,"قیمت فعلی $"),("value",120,"ارزش $"),("pnl",110,"سود/زیان $"),("alloc",80,"سهم %")]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        btnf = ttk.Frame(f); btnf.pack(fill="x", padx=10, pady=5)
        ttk.Button(btnf, text="➕ افزودن دارایی", command=self.add_asset).pack(side="left", padx=5)
        ttk.Button(btnf, text="✏️ ویرایش", command=self.edit_asset).pack(side="left", padx=5)
        ttk.Button(btnf, text="🗑️ حذف", command=self.delete_asset).pack(side="left", padx=5)
        ttk.Button(btnf, text="📊 محاسبه Allocation", command=self.update_assets_view).pack(side="right", padx=5)

        # Allocation canvas
        self.alloc_label = ttk.Label(f, text="", font=("Vazir", 10))
        self.alloc_label.pack(pady=5)

    def build_tx_tab(self):
        f = self.tab_tx
        form = ttk.LabelFrame(f, text="ثبت معامله (خرید/فروش/انتقال)", padding=10)
        form.pack(fill="x", padx=10, pady=10)
        self.tx_symbol = ttk.Combobox(form, values=list(SYMBOLS.keys()), width=10); self.tx_symbol.set("BTC"); self.tx_symbol.grid(row=0,column=0,padx=5)
        self.tx_type = ttk.Combobox(form, values=["خرید","فروش","انتقال"], width=10); self.tx_type.set("خرید"); self.tx_type.grid(row=0,column=1,padx=5)
        self.tx_amount = ttk.Entry(form, width=12); self.tx_amount.insert(0,"0.01"); self.tx_amount.grid(row=0,column=2,padx=5)
        ttk.Label(form, text="مقدار").grid(row=0,column=2,sticky="s")
        self.tx_price = ttk.Entry(form, width=12); self.tx_price.insert(0,"70000"); self.tx_price.grid(row=0,column=3,padx=5)
        self.tx_fee = ttk.Entry(form, width=10); self.tx_fee.insert(0,"0"); self.tx_fee.grid(row=0,column=4,padx=5)
        ttk.Button(form, text="ثبت", command=self.add_transaction).grid(row=0,column=5,padx=10)

        self.tx_tree = ttk.Treeview(f, columns=("date","type","symbol","amount","price","fee"), show="headings", height=10)
        for c,t in [("date","تاریخ"),("type","نوع"),("symbol","نماد"),("amount","مقدار"),("price","قیمت"),("fee","کارمزد")]:
            self.tx_tree.heading(c, text=t); self.tx_tree.column(c, width=110, anchor="center")
        self.tx_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_tx_view()

    def build_chart_tab(self):
        f = self.tab_chart
        if not HAS_MPL:
            ttk.Label(f, text="matplotlib نصب نیست - نمودار غیرفعال").pack(pady=20)
            return
        self.fig = Figure(figsize=(8,3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("تغییرات ارزش پورتفولیو", fontfamily="DejaVu Sans")
        self.canvas = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Button(f, text="📈 رسم از تاریخچه", command=self.draw_chart).pack(pady=5)

    def build_alert_tab(self):
        f = self.tab_alert
        form = ttk.Frame(f); form.pack(fill="x", padx=10, pady=10)
        self.alert_symbol = ttk.Combobox(form, values=list(SYMBOLS.keys()), width=12); self.alert_symbol.set("BTC"); self.alert_symbol.pack(side="left", padx=5)
        self.alert_price = ttk.Entry(form, width=15); self.alert_price.insert(0,"80000"); self.alert_price.pack(side="left", padx=5)
        ttk.Label(form, text="قیمت هدف $").pack(side="left")
        ttk.Button(form, text="🔔 افزودن هشدار", command=self.add_alert).pack(side="left", padx=10)
        self.alert_tree = ttk.Treeview(f, columns=("symbol","target","cur","status"), show="headings", height=10)
        for c,t in [("symbol","نماد"),("target","هدف $"),("cur","فعلی $"),("status","وضعیت")]:
            self.alert_tree.heading(c, text=t); self.alert_tree.column(c, width=120, anchor="center")
        self.alert_tree.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Button(f, text="حذف هشدار", command=self.delete_alert).pack(pady=5)

    def build_report_tab(self):
        f = self.tab_report
        cashf = ttk.LabelFrame(f, text="💵 موجودی نقدی و 💱 نرخ تبدیل", padding=10)
        cashf.pack(fill="x", padx=10, pady=10)
        ttk.Label(cashf, text="نقد USD $:").grid(row=0,column=0,padx=5)
        self.cash_usd = ttk.Entry(cashf, width=15); self.cash_usd.insert(0, str(self.data["cash"].get("USD",0))); self.cash_usd.grid(row=0,column=1,padx=5)
        ttk.Label(cashf, text="نرخ USD به تومان:").grid(row=0,column=2,padx=5)
        self.rate_entry = ttk.Entry(cashf, width=15); self.rate_entry.insert(0, str(self.data.get("usd_to_toman", USD_TO_TOMAN))); self.rate_entry.grid(row=0,column=3,padx=5)
        ttk.Button(cashf, text="ذخیره نرخ/نقد", command=self.save_cash).grid(row=0,column=4,padx=10)

        self.report_text = tk.Text(f, height=15, wrap="word")
        self.report_text.pack(fill="both", expand=True, padx=10, pady=10)
        btnf = ttk.Frame(f); btnf.pack(fill="x", padx=10, pady=5)
        ttk.Button(btnf, text="📅 گزارش روزانه", command=lambda: self.generate_report("daily")).pack(side="left", padx=5)
        ttk.Button(btnf, text="📅 گزارش هفتگی", command=lambda: self.generate_report("weekly")).pack(side="left", padx=5)
        ttk.Button(btnf, text="📋 کپی گزارش", command=self.copy_report).pack(side="left", padx=5)

    # Logic
    def refresh_prices(self):
        def run():
            syms = list({a["symbol"] for a in self.data["assets"]} | {"BTC","ETH","PAXG","USD"})
            self.prices = fetch_prices(syms)
            self.after(0, self.update_assets_view)
            self.after(0, self.check_alerts)
        threading.Thread(target=run, daemon=True).start()
        self.total_label.config(text="در حال دریافت قیمت...")

    def update_assets_view(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        total = self.data["cash"].get("USD",0)
        vals = []
        for a in self.data["assets"]:
            sym = a["symbol"]
            cur = self.prices.get(sym, 0) or 0
            val = a["amount"] * cur
            vals.append(val)
            total += val
        # Update total label in USD, Toman, Rial
        try: rate = float(self.rate_entry.get())
        except: rate = USD_TO_TOMAN
        toman = total * rate
        rial = toman * 10
        # PnL
        total_cost = sum(a["amount"]*a["avg_price"] for a in self.data["assets"])
        total_pnl = total - total_cost - self.data["cash"].get("USD",0) + self.data["cash"].get("USD",0)  # simplify
        # Actually total includes cash, so pnl = (asset values - cost) 
        asset_value = sum(vals)
        pnl = asset_value - total_cost
        self.total_label.config(text=f"ارزش کل: ${total:,.2f} | {toman:,.0f} تومان | {rial:,.0f} ریال | سود/زیان دارایی‌ها: ${pnl:,.2f}")

        # Save history
        today = datetime.date.today().isoformat()
        if not self.data["history"] or self.data["history"][-1].get("date") != today:
            self.data["history"].append({"date": today, "total": total})
            if len(self.data["history"]) > 365:
                self.data["history"] = self.data["history"][-365:]
            save_data(self.data)

        for a, val in zip(self.data["assets"], vals):
            sym = a["symbol"]
            cur = self.prices.get(sym, 0) or 0
            pnl_a = (cur - a["avg_price"]) * a["amount"]
            alloc = (val/total*100) if total else 0
            self.tree.insert("", "end", values=(sym, a["amount"], f"{a['avg_price']:,.2f}", f"{cur:,.2f}", f"{val:,.2f}", f"{pnl_a:,.2f}", f"{alloc:.1f}%"))

        alloc_text = " | ".join([f"{a['symbol']}: { (vals[i]/total*100) if total else 0:.1f}%" for i,a in enumerate(self.data["assets"])])
        self.alloc_label.config(text=f"⚖️ Allocation: {alloc_text}")
        self.refresh_alert_view()
        if HAS_MPL:
            self.draw_chart()

    def add_asset(self):
        sym = simpledialog.askstring("نماد", "نماد (BTC, ETH, PAXG, GOLD, USD...):")
        if not sym: return
        sym = sym.upper().strip()
        amt = simpledialog.askfloat("مقدار", f"مقدار {sym}:", minvalue=0)
        if amt is None: return
        avg = simpledialog.askfloat("میانگین خرید", f"میانگین قیمت خرید {sym} به دلار:", minvalue=0)
        if avg is None: avg = self.prices.get(sym, 0)
        self.data["assets"].append({"symbol": sym, "amount": amt, "avg_price": avg or 0})
        save_data(self.data); self.update_assets_view()

    def edit_asset(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("انتخاب", "یک دارایی را انتخاب کن")
        idx = self.tree.index(sel[0])
        a = self.data["assets"][idx]
        amt = simpledialog.askfloat("ویرایش مقدار", f"مقدار جدید {a['symbol']}:", initialvalue=a["amount"])
        if amt is not None:
            a["amount"] = amt
        avg = simpledialog.askfloat("ویرایش میانگین", f"میانگین جدید {a['symbol']}:", initialvalue=a["avg_price"])
        if avg is not None:
            a["avg_price"] = avg
        save_data(self.data); self.update_assets_view()

    def delete_asset(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        if messagebox.askyesno("حذف", f"حذف {self.data['assets'][idx]['symbol']}؟"):
            self.data["assets"].pop(idx)
            save_data(self.data); self.update_assets_view()

    def add_transaction(self):
        try:
            sym = self.tx_symbol.get().upper()
            typ = self.tx_type.get()
            amt = float(self.tx_amount.get())
            price = float(self.tx_price.get())
            fee = float(self.tx_fee.get())
        except: return messagebox.showerror("خطا", "مقادیر عددی را درست وارد کن")
        # Update assets
        found = next((a for a in self.data["assets"] if a["symbol"]==sym), None)
        if typ=="خرید":
            if found:
                total_cost = found["amount"]*found["avg_price"] + amt*price + fee
                total_amt = found["amount"]+amt
                found["avg_price"] = total_cost/total_amt if total_amt else 0
                found["amount"] = total_amt
            else:
                self.data["assets"].append({"symbol": sym, "amount": amt, "avg_price": price + (fee/amt if amt else 0)})
        elif typ=="فروش":
            if found:
                found["amount"] = max(0, found["amount"]-amt)
                # cash increase
                self.data["cash"]["USD"] = self.data["cash"].get("USD",0) + amt*price - fee
            else:
                messagebox.showwarning("هشدار", "دارایی برای فروش یافت نشد")
                return
        else: # انتقال
            if found:
                found["amount"] = max(0, found["amount"]-amt)
        tx = {"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "type": typ, "symbol": sym, "amount": amt, "price": price, "fee": fee}
        self.data["transactions"].append(tx)
        save_data(self.data)
        self.update_assets_view()
        self.refresh_tx_view()
        messagebox.showinfo("ثبت شد", f"{typ} {amt} {sym} ثبت شد")

    def refresh_tx_view(self):
        for i in self.tx_tree.get_children(): self.tx_tree.delete(i)
        for t in self.data["transactions"][-50:][::-1]:
            self.tx_tree.insert("", "end", values=(t["date"], t["type"], t["symbol"], t["amount"], t["price"], t["fee"]))

    def draw_chart(self):
        if not HAS_MPL: return
        self.ax.clear()
        hist = self.data.get("history", [])
        if len(hist) < 2:
            # fake history from assets if not enough
            self.ax.text(0.5,0.5, "با هر بروزرسانی، تاریخچه ساخته می‌شود\nحداقل ۲ روز داده نیاز است", ha="center", transform=self.ax.transAxes)
        else:
            dates = [h["date"][-5:] for h in hist]
            vals = [h["total"] for h in hist]
            self.ax.plot(dates, vals, marker="o")
            self.ax.set_ylabel("$")
            self.ax.tick_params(axis="x", rotation=30)
        self.ax.set_title("ارزش پورتفولیو در طول زمان")
        self.fig.tight_layout()
        self.canvas.draw()

    def add_alert(self):
        try:
            sym = self.alert_symbol.get().upper()
            target = float(self.alert_price.get())
        except: return messagebox.showerror("خطا","قیمت را درست وارد کن")
        self.data["alerts"].append({"symbol": sym, "target": target})
        save_data(self.data); self.refresh_alert_view()

    def refresh_alert_view(self):
        for i in self.alert_tree.get_children(): self.alert_tree.delete(i)
        for a in self.data["alerts"]:
            cur = self.prices.get(a["symbol"], 0) or 0
            status = "🔔 رسید!" if (cur and ((cur >= a["target"] and cur) or (cur <= a["target"]))) else "⏳ منتظر"
            # simple: if cur >= target then reached (for upper), else check lower - we just show reached if cur >= target
            if cur and cur >= a["target"]:
                status = "🔔 رسید (بالا)"
            elif cur and cur <= a["target"] and cur !=0:
                # ambiguous, show distance
                diff = cur - a["target"]
                status = f"فاصله {diff:,.0f}$"
            self.alert_tree.insert("", "end", values=(a["symbol"], a["target"], f"{cur:,.2f}" if cur else "-", status))

    def delete_alert(self):
        sel = self.alert_tree.selection()
        if not sel: return
        idx = self.alert_tree.index(sel[0])
        self.data["alerts"].pop(idx)
        save_data(self.data); self.refresh_alert_view()

    def check_alerts(self):
        for a in self.data["alerts"]:
            cur = self.prices.get(a["symbol"], 0)
            if cur and cur >= a["target"]:
                self.bell()
                break

    def save_cash(self):
        try:
            self.data["cash"]["USD"] = float(self.cash_usd.get())
            self.data["usd_to_toman"] = float(self.rate_entry.get())
            save_data(self.data)
            self.update_assets_view()
            messagebox.showinfo("ذخیره", "نقد و نرخ ذخیره شد")
        except: messagebox.showerror("خطا","عدد را درست وارد کن")

    def generate_report(self, period):
        total = sum(a["amount"]*self.prices.get(a["symbol"],0) for a in self.data["assets"]) + self.data["cash"].get("USD",0)
        cost = sum(a["amount"]*a["avg_price"] for a in self.data["assets"])
        pnl = sum((self.prices.get(a["symbol"],0)-a["avg_price"])*a["amount"] for a in self.data["assets"])
        hist = self.data.get("history", [])
        change = 0
        if period=="daily" and len(hist)>=2:
            change = total - hist[-2]["total"]
        elif period=="weekly" and len(hist)>=7:
            change = total - hist[-7]["total"]
        txt = f"📅 گزارش {'روزانه' if period=='daily' else 'هفتگی'} - {datetime.date.today()}\n"
        txt += f"ارزش کل: ${total:,.2f}\n"
        txt += f"سود/زیان کل: ${pnl:,.2f}\n"
        txt += f"تغییر {'روز' if period=='daily' else 'هفته'}: ${change:,.2f}\n"
        txt += f"دارایی‌ها:\n"
        for a in self.data["assets"]:
            cur = self.prices.get(a["symbol"],0)
            txt += f" - {a['symbol']}: {a['amount']} × ${cur:,.0f} = ${a['amount']*cur:,.0f} (میانگین ${a['avg_price']:,.0f})\n"
        txt += f"نقد USD: ${self.data['cash'].get('USD',0):,.0f}\n"
        self.report_text.delete("1.0","end")
        self.report_text.insert("1.0", txt)

    def copy_report(self):
        txt = self.report_text.get("1.0","end")
        self.clipboard_clear(); self.clipboard_append(txt)

if __name__ == "__main__":
    App().mainloop()
