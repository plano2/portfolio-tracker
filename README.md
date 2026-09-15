# Portfolio Tracker - Abbas

## ویژگی‌ها
- 💰 دارایی‌ها: BTC, ETH, PAXG, GOLD, USD و سایر
- 📊 ارزش کل به دلار، تومان، ریال
- 📈 سود/زیان هر دارایی و کل
- 🧾 معاملات: خرید/فروش/انتقال + کارمزد + میانگین قیمت تمام‌شده
- 📉 نمودار ارزش در طول زمان
- ⚖️ Allocation درصد سهم
- 💵 Cash و نرخ USD->تومان
- 🔔 هشدار قیمت
- 📅 گزارش روزانه/هفتگی
- 🔐 ذخیره محلی portfolio.json

## اجرا (ویندوز/مک/لینوکس)
```bash
python3 -m venv venv
source venv/bin/activate  # ویندوز: venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

## فایل داده
`portfolio.json` کنار app.py ذخیره می‌شود - بکاپ بگیرید.
