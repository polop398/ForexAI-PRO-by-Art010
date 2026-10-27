FOREX AI ASSISTANT - XAUUSD (advisory only)

1) Keep forex_ai_assistant.py and เปิด_Forex_AI_Assistant.bat in the same folder.
2) Double-click เปิด_Forex_AI_Assistant.bat.
3) For live terminal data:
   - Open MetaTrader 5 and log into a DEMO account.
   - In CMD, install the optional connector with: py -m pip install MetaTrader5
   - Click "วิเคราะห์จาก MT5". The app reads CLOSED M15/H1 candles only.
   - If the MetaTrader5 package does not install under your Python version, use a supported Python version or CSV import.
4) For CSV:
   - Click "เลือกไฟล์ CSV" and choose mt5_XAUUSD_M15_candles_indicators.csv, then click "วิเคราะห์ CSV".
   - CSV results are historical, not live.
5) Optional refresh: tick "รีเฟรช MT5 ทุก 60 วินาที". This only refreshes analysis; it never trades.
6) The program never sends, modifies, or closes orders.
7) Signals are rule-based educational suggestions, not guarantees. Test on demo; verify symbol name, spread, contract size, and risk.
