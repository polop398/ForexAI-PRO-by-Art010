# -*- coding: utf-8 -*-
"""
Forex AI Assistant - advisory-only dashboard for XAUUSD.
- Attempts to read closed candles directly from an open MetaTrader 5 terminal
  through the optional MetaTrader5 Python package.
- If unavailable, lets the user load an exported indicators CSV.
- Never places, modifies, or closes trades.
"""
import csv
import math
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timezone
from pathlib import Path

APP_TITLE = "Forex AI Assistant - XAUUSD"
DEFAULT_SYMBOL = "XAUUSD"
DEFAULT_CSV = "mt5_XAUUSD_M15_candles_indicators.csv"

def safe_float(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def ema(values, period):
    out = []
    alpha = 2.0 / (period + 1.0)
    prev = None
    for v in values:
        prev = v if prev is None else alpha * v + (1-alpha) * prev
        out.append(prev)
    return out

def rsi(values, period=14):
    if len(values) < period + 1:
        return [None] * len(values)
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(values)):
        d = values[i] - values[i-1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    out = [None] * len(values)
    avg_g = sum(gains[1:period+1]) / period
    avg_l = sum(losses[1:period+1]) / period
    out[period] = 100.0 if avg_l == 0 else 100 - 100/(1 + avg_g/avg_l)
    for i in range(period+1, len(values)):
        avg_g = (avg_g*(period-1) + gains[i]) / period
        avg_l = (avg_l*(period-1) + losses[i]) / period
        out[i] = 100.0 if avg_l == 0 else 100 - 100/(1 + avg_g/avg_l)
    return out

def atr(highs, lows, closes, period=14):
    trs = []
    for i in range(len(closes)):
        if i == 0:
            trs.append(highs[i] - lows[i])
        else:
            trs.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    out = [None] * len(closes)
    if len(trs) < period:
        return out
    prev = sum(trs[:period]) / period
    out[period-1] = prev
    for i in range(period, len(trs)):
        prev = (prev*(period-1) + trs[i]) / period
        out[i] = prev
    return out

def enrich(rows):
    rows = [r for r in rows if all(safe_float(r.get(k)) is not None for k in ("open","high","low","close"))]
    rows.sort(key=lambda r: str(r.get("time_utc", r.get("time", ""))))
    if not rows:
        raise ValueError("ไม่พบแถวข้อมูลราคา OHLC ที่ถูกต้อง")
    closes = [float(r["close"]) for r in rows]
    highs = [float(r["high"]) for r in rows]
    lows = [float(r["low"]) for r in rows]
    e20, e50, e200 = ema(closes,20), ema(closes,50), ema(closes,200)
    rs, ats = rsi(closes), atr(highs,lows,closes)
    macd_fast, macd_slow = ema(closes,12), ema(closes,26)
    ml = [a-b for a,b in zip(macd_fast,macd_slow)]
    ms = ema(ml,9)
    hist = [a-b for a,b in zip(ml,ms)]
    result=[]
    for i,r in enumerate(rows):
        rr=dict(r)
        rr.update({"EMA20":e20[i],"EMA50":e50[i],"EMA200":e200[i],"RSI14":rs[i],
                   "MACD_line":ml[i],"MACD_signal":ms[i],"MACD_histogram":hist[i],"ATR14":ats[i]})
        result.append(rr)
    return result

def analyze(rows, label="M15"):
    if len(rows) < 200:
        return {"signal":"WAIT","trend":"INSUFFICIENT DATA","reasons":[f"ต้องมีข้อมูลอย่างน้อย 200 แท่ง; ปัจจุบัน {len(rows)} แท่ง"],"entry":None,"sl":None,"tp":None,"row":rows[-1] if rows else {}}
    r=rows[-1]
    close=safe_float(r.get("close"))
    e20=safe_float(r.get("EMA20")); e50=safe_float(r.get("EMA50")); e200=safe_float(r.get("EMA200"))
    rv=safe_float(r.get("RSI14")); ml=safe_float(r.get("MACD_line")); ms=safe_float(r.get("MACD_signal"))
    hist=safe_float(r.get("MACD_histogram")); av=safe_float(r.get("ATR14"))
    if None in (close,e20,e50,e200,rv,ml,ms,hist,av) or av <= 0:
        return {"signal":"WAIT","trend":"DATA INCOMPLETE","reasons":["อินดิเคเตอร์บางค่าคำนวณไม่ได้"],"entry":None,"sl":None,"tp":None,"row":r}
    trend="MIXED"
    if close>e20>e50>e200: trend="BULLISH"
    elif close<e20<e50<e200: trend="BEARISH"
    elif e20>e50 and close>e200: trend="BULLISH BIAS"
    elif e20<e50 and close<e200: trend="BEARISH BIAS"
    bull=sum([close>e20,e20>e50,rv>=52,ml>ms,hist>0])
    bear=sum([close<e20,e20<e50,rv<=48,ml<ms,hist<0])
    signal="WAIT"
    reasons=[]
    if bull>=4 and bull>bear and rv<70:
        signal="BUY"; reasons.append(f"เงื่อนไขฝั่งซื้อสอดคล้อง {bull}/5 ข้อ")
    elif bear>=4 and bear>bull and rv>30:
        signal="SELL"; reasons.append(f"เงื่อนไขฝั่งขายสอดคล้อง {bear}/5 ข้อ")
    else:
        reasons.append(f"สัญญาณยังไม่ตรงกัน (BUY {bull}/5, SELL {bear}/5)")
    if close>e200: reasons.append("ราคาปิดอยู่เหนือ EMA200")
    else: reasons.append("ราคาปิดอยู่ใต้ EMA200")
    reasons.append("RSI %.1f; MACD histogram %.4f" % (rv,hist))
    entry=sl=tp=None
    if signal=="BUY":
        entry=close; sl=close-1.5*av; tp=close+2.25*av
    elif signal=="SELL":
        entry=close; sl=close+1.5*av; tp=close-2.25*av
    return {"signal":signal,"trend":trend,"reasons":reasons,"entry":entry,"sl":sl,"tp":tp,"row":r,
            "bull":bull,"bear":bear,"atr":av}

def read_csv(path):
    with open(path,"r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        rows=list(reader)
    return enrich(rows)

def mt5_rates(symbol, timeframe_name, count=350):
    try:
        import MetaTrader5 as mt5
    except Exception as e:
        raise RuntimeError("ยังไม่มีไลบรารี MetaTrader5 สำหรับ Python ("+str(e)+")")
    if not mt5.initialize():
        err=mt5.last_error()
        raise RuntimeError(f"เชื่อม MT5 ไม่สำเร็จ: {err}. เปิด MT5 และล็อกอินบัญชี Demo ก่อน")
    try:
        tfmap={"M15":mt5.TIMEFRAME_M15,"H1":mt5.TIMEFRAME_H1}
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"ไม่พบ/เลือก symbol {symbol} ไม่สำเร็จ; ตรวจชื่อทองใน Market Watch")
        # Start at position 1 to exclude the still-forming current candle.
        rates=mt5.copy_rates_from_pos(symbol, tfmap[timeframe_name], 1, count)
        if rates is None or len(rates)==0:
            raise RuntimeError(f"MT5 ไม่ส่งแท่งเทียนกลับมา: {mt5.last_error()}")
        rows=[]
        for x in rates:
            rows.append({"time_utc":datetime.fromtimestamp(int(x["time"]),timezone.utc).isoformat(),
                         "open":float(x["open"]),"high":float(x["high"]),
                         "low":float(x["low"]),"close":float(x["close"])})
        return enrich(rows)
    finally:
        mt5.shutdown()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x700")
        self.minsize(780,600)
        self.csv_path=None
        self.auto_var=tk.BooleanVar(value=False)
        self.source_var=tk.StringVar(value="MT5 (พยายามเชื่อมต่อโดยตรง)")
        self.symbol_var=tk.StringVar(value=DEFAULT_SYMBOL)
        self.status_var=tk.StringVar(value="พร้อมใช้งาน — ยังไม่มีการวิเคราะห์")
        self._build()
        self.after(700,self.try_startup)

    def _build(self):
        top=ttk.Frame(self,padding=12); top.pack(fill="x")
        ttk.Label(top,text="FOREX AI ASSISTANT",font=("Segoe UI",18,"bold")).pack(anchor="w")
        ttk.Label(top,text="XAUUSD • วิเคราะห์เพื่อประกอบการตัดสินใจเท่านั้น • ไม่ส่งคำสั่งเทรด").pack(anchor="w",pady=(2,10))
        controls=ttk.Frame(top); controls.pack(fill="x")
        ttk.Label(controls,text="Symbol:").pack(side="left")
        ttk.Entry(controls,textvariable=self.symbol_var,width=12).pack(side="left",padx=(4,12))
        ttk.Button(controls,text="วิเคราะห์จาก MT5",command=self.run_mt5).pack(side="left",padx=3)
        ttk.Button(controls,text="เลือกไฟล์ CSV",command=self.choose_csv).pack(side="left",padx=3)
        ttk.Button(controls,text="วิเคราะห์ CSV",command=self.run_csv).pack(side="left",padx=3)
        ttk.Checkbutton(controls,text="รีเฟรช MT5 ทุก 60 วินาที",variable=self.auto_var,command=self.toggle_auto).pack(side="left",padx=8)
        self.signal_label=ttk.Label(self,text="SIGNAL: WAIT",font=("Segoe UI",18,"bold"),padding=10)
        self.signal_label.pack(fill="x",padx=12,pady=(0,6))
        self.summary=ttk.LabelFrame(self,text="สรุปการวิเคราะห์",padding=10); self.summary.pack(fill="x",padx=12,pady=5)
        self.summary_text=tk.Text(self.summary,height=11,wrap="word",font=("Consolas",10))
        self.summary_text.pack(fill="x")
        self.summary_text.configure(state="disabled")
        self.details=ttk.LabelFrame(self,text="ข้อมูลล่าสุด / อินดิเคเตอร์",padding=10); self.details.pack(fill="both",expand=True,padx=12,pady=5)
        self.details_text=tk.Text(self.details,height=9,wrap="word",font=("Consolas",10))
        self.details_text.pack(fill="both",expand=True)
        self.details_text.configure(state="disabled")
        ttk.Label(self,textvariable=self.status_var,relief="sunken",anchor="w",padding=5).pack(fill="x",side="bottom")

    def put(self,widget,text):
        widget.configure(state="normal"); widget.delete("1.0","end"); widget.insert("1.0",text); widget.configure(state="disabled")

    def try_startup(self):
        # Don't silently connect to an account; user chooses source.
        pass

    def choose_csv(self):
        p=filedialog.askopenfilename(title="เลือกไฟล์แท่งเทียน CSV",filetypes=[("CSV files","*.csv"),("All files","*.*")])
        if p:
            self.csv_path=p
            self.status_var.set("เลือกไฟล์: "+p)

    def run_csv(self):
        if not self.csv_path:
            candidate=Path(__file__).with_name(DEFAULT_CSV)
            if candidate.exists(): self.csv_path=str(candidate)
            else:
                p=filedialog.askopenfilename(title="เลือกไฟล์ CSV ที่ส่งออกจาก MT5",filetypes=[("CSV files","*.csv")])
                if not p: return
                self.csv_path=p
        try:
            rows=read_csv(self.csv_path)
            self.show_analysis(rows,"CSV / historical export")
        except Exception as e:
            messagebox.showerror("อ่าน CSV ไม่สำเร็จ",str(e))

    def run_mt5(self):
        self.status_var.set("กำลังอ่านข้อมูลแท่งที่ปิดแล้วจาก MT5...")
        self.signal_label.configure(text="SIGNAL: CHECKING...")
        def worker():
            try:
                symbol=self.symbol_var.get().strip() or DEFAULT_SYMBOL
                m15=mt5_rates(symbol,"M15",350)
                h1=mt5_rates(symbol,"H1",350)
                self.after(0,lambda:self.show_analysis(m15,"MT5 live connection",h1))
            except Exception as e:
                self.after(0,lambda:messagebox.showerror("เชื่อม MT5 ไม่สำเร็จ",str(e)))
                self.after(0,lambda:self.status_var.set("เชื่อม MT5 ไม่สำเร็จ — ใช้ปุ่มเลือก CSV ได้"))
        threading.Thread(target=worker,daemon=True).start()

    def show_analysis(self,rows,source,h1=None):
        a=analyze(rows,"M15"); r=a["row"]
        dt=str(r.get("time_utc",r.get("time","ไม่ทราบเวลา")))
        lines=[
            f"แหล่งข้อมูล: {source}",
            f"เวลาแท่งล่าสุด (UTC): {dt}",
            f"จำนวนแท่ง: {len(rows)}",
            f"แนวโน้ม M15: {a['trend']}",
            f"คำแนะนำ: {a['signal']}",
            "เหตุผล: "+"; ".join(a["reasons"]),
        ]
        if a["signal"] in ("BUY","SELL"):
            lines += [f"ราคาอ้างอิงเข้า: {a['entry']:.2f}",f"Stop Loss อ้างอิง: {a['sl']:.2f}",
                      f"Take Profit อ้างอิง: {a['tp']:.2f}","อัตราส่วนเป้าหมาย/ความเสี่ยง: 1.5:1"]
        else:
            lines += ["Entry / SL / TP: ยังไม่ระบุ เพราะสัญญาณยังไม่ผ่านเกณฑ์"]
        lines += ["","คำเตือน: เป็นการวิเคราะห์ตามกฎพื้นฐาน ไม่รับประกันผลลัพธ์ ต้องตรวจ spread, contract size และความเสี่ยงก่อนตัดสินใจ"]
        self.put(self.summary_text,"\n".join(lines))
        ind=[
            f"Close: {safe_float(r.get('close'))}",
            f"EMA20: {safe_float(r.get('EMA20'))} | EMA50: {safe_float(r.get('EMA50'))} | EMA200: {safe_float(r.get('EMA200'))}",
            f"RSI14: {safe_float(r.get('RSI14'))}",
            f"MACD: {safe_float(r.get('MACD_line'))} | Signal: {safe_float(r.get('MACD_signal'))} | Histogram: {safe_float(r.get('MACD_histogram'))}",
            f"ATR14: {safe_float(r.get('ATR14'))}",
        ]
        if h1:
            ah=analyze(h1,"H1")
            ind += ["",f"แนวโน้ม H1: {ah['trend']} | สัญญาณ H1: {ah['signal']}",
                    "หมายเหตุ H1: ใช้ยืนยันภาพใหญ่ ไม่ได้เป็นคำสั่งเทรด"]
            # Avoid treating disagreement as a trade confirmation.
            if a["signal"] in ("BUY","SELL") and ah["signal"] not in ("WAIT",a["signal"]):
                ind.append("คำเตือน: สัญญาณ M15 กับ H1 ไม่สอดคล้องกัน ควรลดความมั่นใจ/รอ")
        self.put(self.details_text,"\n".join(ind))
        self.signal_label.configure(text="SIGNAL: "+a["signal"])
        self.status_var.set("วิเคราะห์เสร็จ: "+datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" | ไม่มีการส่งคำสั่งซื้อขาย")

    def toggle_auto(self):
        if self.auto_var.get():
            self.run_mt5()
            self.after(60000,self.auto_tick)
        else:
            self.status_var.set("ปิดการรีเฟรชอัตโนมัติ")

    def auto_tick(self):
        if self.auto_var.get():
            self.run_mt5()
            self.after(60000,self.auto_tick)

if __name__=="__main__":
    App().mainloop()
