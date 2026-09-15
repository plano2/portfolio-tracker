#!/bin/bash
pip install -r requirements.txt flask pyinstaller
pyinstaller --onefile --noconsole --name PortfolioTracker web_app.py
