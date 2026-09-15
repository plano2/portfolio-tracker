@echo off
echo Building PortfolioTracker.exe for Windows...
pip install -r requirements.txt flask pyinstaller
pyinstaller --onefile --noconsole --name PortfolioTracker --add-data "portfolio.json;." web_app.py
echo Done! Find exe in dist\PortfolioTracker.exe
pause
