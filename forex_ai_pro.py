# -*- coding: utf-8 -*-
"""Forex AI Assistant PRO - MT5 read-only dashboard. No trading execution."""
import tkinter as tk
from tkinter import ttk, messagebox
import threading, queue, time, os, sys, json, urllib.request, urllib.error, subprocess, zipfile
from datetime import datetime, timezone

try:
    import MetaTrader5 as mt5
except Exception:
    mt5 = None
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Rectangle
except Exception:
    Figure = FigureCanvasTkAgg = Rectangle = None

from forex_ai_assistant import analyze, enrich

BG = '#050b14'; PANEL = '#0b1726'; PANEL2 = '#12243a'; TEXT = '#f3f6fc'
MUTED = '#a9bad0'; BLUE = '#168cff'; GREEN = '#16d995'; RED = '#ff5364'; GOLD = '#f8bd45'
THAI_FONT = 'Leelawadee UI'
APP_VERSION = '1.2.3'
GITHUB_REPO = 'polop398/ForexAI-PRO-by-Art010'
UPDATE_ASSET = 'ForexAI_PRO_Update.zip'

class ForexAIPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('ForexAI PRO | สร้างด้วย by Art010')
        self.geometry('1360x900'); self.minsize(900,620); self.configure(bg=BG)
        try:
            import os, sys
            base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon = os.path.join(base, 'ForexAI_PRO.ico')
            if os.path.exists(icon): self.iconbitmap(icon)
        except Exception: pass
        self._make_scroll_area()
        self.symbol = tk.StringVar(value='XAUUSD')
        self.auto = tk.BooleanVar(value=True)
        self.interval = tk.IntVar(value=5)
        self.q = queue.Queue(); self.busy = False; self.last_rows = []; self.last_h1=[]
        self._style(); self._build()
        self.after(500, self.refresh); self.after(1000, self.poll_queue)

    def _make_scroll_area(self):
        """Place the dashboard in a vertically scrollable frame."""
        self._outer = tk.Frame(self, bg=BG)
        self._outer.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(self._outer, bg=BG, highlightthickness=0, borderwidth=0)
        self._scrollbar = ttk.Scrollbar(self._outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self._canvas, bg=BG)
        self._body_window = self._canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfigure(self._body_window, width=e.width))
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind("<Destroy>", self._cleanup_scroll, add="+")

    def _on_mousewheel(self, event):
        # Scroll only while pointer is over this app's dashboard.
        try:
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget and (widget == self._canvas or str(widget).startswith(str(self.body))):
                self._canvas.yview_scroll(int(-event.delta / 120), "units")
        except Exception:
            pass

    def _cleanup_scroll(self, _event=None):
        try:
            self._canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass

    def _style(self):
        s=ttk.Style(self); s.theme_use('clam')
        s.configure('TFrame', background=BG); s.configure('Panel.TFrame', background=PANEL)
        s.configure('TLabel', background=PANEL, foreground=TEXT, font=(THAI_FONT,10))
        s.configure('Muted.TLabel', background=PANEL, foreground=MUTED, font=(THAI_FONT,9))
        s.configure('Title.TLabel', background=BG, foreground=TEXT, font=(THAI_FONT,22,'bold'))
        s.configure('TButton', font=(THAI_FONT,10,'bold'), padding=8)
        s.configure('Accent.TButton', background=BLUE, foreground='#07111f')
        s.map('Accent.TButton', background=[('active','#78b8ff')])

    def card(self, parent, title):
        f=ttk.Frame(parent, style='Panel.TFrame', padding=12)
        ttk.Label(f,text=title,font=('Segoe UI',10,'bold')).pack(anchor='w')
        return f

    def _build(self):
        header=tk.Frame(self.body,bg=BG); header.pack(fill='x',padx=18,pady=(14,8))
        logo=tk.Canvas(header,width=58,height=58,bg=BG,highlightthickness=0); logo.pack(side='left',padx=(0,10))
        logo.create_oval(3,3,55,55,outline=GOLD,width=2); logo.create_text(29,27,text='A',fill=GOLD,font=('Segoe UI',31,'bold')); logo.create_text(29,46,text='PRO',fill=TEXT,font=('Segoe UI',8,'bold'))
        titlebox=tk.Frame(header,bg=BG); titlebox.pack(side='left',fill='x')
        tk.Label(titlebox,text='FOREXAI PRO',font=('Segoe UI',25,'bold'),fg=GOLD,bg=BG).pack(anchor='w')
        tk.Label(titlebox,text='ผู้ช่วยวิเคราะห์ทองคำ XAUUSD  •  สร้างด้วย by Art010',font=(THAI_FONT,10,'bold'),fg=MUTED,bg=BG).pack(anchor='w')
        self.connection=tk.Label(header,text='● ตรวจสอบ MT5...',font=('Segoe UI',10,'bold'),fg=GOLD,bg=PANEL,padx=14,pady=10)
        self.connection.pack(side='right')
        bar=tk.Frame(self.body,bg=PANEL,padx=12,pady=10); bar.pack(fill='x',padx=18,pady=5)
        tk.Label(bar,text='สินทรัพย์',bg=PANEL,fg=MUTED,font=(THAI_FONT,9,'bold')).pack(side='left',padx=(0,8))
        tk.Entry(bar,textvariable=self.symbol,width=12,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',11)).pack(side='left',ipady=7,padx=(0,10))
        ttk.Button(bar,text='วิเคราะห์ตอนนี้',style='Accent.TButton',command=self.refresh).pack(side='left',padx=4)
        ttk.Button(bar,text='ตรวจสอบอัปเดต',command=self.check_for_updates).pack(side='left',padx=4)
        ttk.Checkbutton(bar,text='อัปเดตอัตโนมัติ',variable=self.auto).pack(side='left',padx=12)
        tk.Label(bar,text='อัปเดตทุก 5 วินาที • โหมดอ่านข้อมูล ไม่ส่งคำสั่งเทรด',bg=PANEL,fg=MUTED,font=(THAI_FONT,9)).pack(side='right')

        top=tk.Frame(self.body,bg=BG); top.pack(fill='x',padx=18,pady=7)
        self.signal_card=self.card(top,'สัญญาณล่าสุด'); self.signal_card.pack(side='left',fill='both',expand=True,padx=(0,6))
        self.sig=tk.Label(self.signal_card,text='WAIT',bg=PANEL,fg=GOLD,font=('Segoe UI',25,'bold')); self.sig.pack(anchor='w',pady=5)
        self.sig_reason=tk.Label(self.signal_card,text='รอข้อมูลจาก MT5',bg=PANEL,fg=MUTED,font=('Segoe UI',10),wraplength=560,justify='left'); self.sig_reason.pack(anchor='w')
        self.price_card=self.card(top,'ราคาล่าสุด'); self.price_card.pack(side='left',fill='both',expand=True,padx=6)
        self.price=tk.Label(self.price_card,text='—',bg=PANEL,fg=TEXT,font=('Segoe UI',24,'bold')); self.price.pack(anchor='w',pady=5)
        self.updated=tk.Label(self.price_card,text='ยังไม่มีข้อมูล',bg=PANEL,fg=MUTED,font=('Segoe UI',9)); self.updated.pack(anchor='w')
        self.trend_card=self.card(top,'แนวโน้มหลายกรอบเวลา'); self.trend_card.pack(side='left',fill='both',expand=True,padx=(6,0))
        self.trends=tk.Label(self.trend_card,text='M5  —\nM15 —\nH1  —',bg=PANEL,fg=TEXT,font=('Segoe UI',11,'bold'),justify='left'); self.trends.pack(anchor='w',pady=5)

        chartwrap=tk.Frame(self.body,bg=PANEL); chartwrap.pack(fill='both',expand=True,padx=18,pady=7)
        charthead=tk.Frame(chartwrap,bg=PANEL); charthead.pack(fill='x',padx=12,pady=(9,0))
        tk.Label(charthead,text='กราฟราคาเรียลไทม์  •  XAUUSD',bg=PANEL,fg=GOLD,font=(THAI_FONT,11,'bold')).pack(side='left')
        self.chart_tf=tk.StringVar(value='M5')
        for tf in ('M5','M15','H1'):
            ttk.Radiobutton(charthead,text=tf,value=tf,variable=self.chart_tf,command=self._redraw_selected).pack(side='right',padx=4)
        if Figure:
            self.fig=Figure(figsize=(10,4.2),dpi=100,facecolor=PANEL)
            self.ax=self.fig.add_subplot(111); self._chart_style()
            self.chart=FigureCanvasTkAgg(self.fig,master=chartwrap); self.chart.get_tk_widget().pack(fill='both',expand=True,padx=5,pady=4)
        else:
            self.fig=None
            tk.Label(chartwrap,text='ไม่พบ Matplotlib กรุณาติดตั้งด้วย pip install matplotlib',bg=PANEL,fg=GOLD).pack(pady=60)

        bottom=tk.Frame(self.body,bg=BG); bottom.pack(fill='x',padx=18,pady=(0,12))
        self.metrics=self.card(bottom,'ตัวชี้วัดทางเทคนิค'); self.metrics.pack(side='left',fill='both',expand=True,padx=(0,6))
        self.metric_text=tk.Label(self.metrics,text='RSI: —   MACD: —   EMA20/50/200: —',bg=PANEL,fg=TEXT,font=('Consolas',10),justify='left',wraplength=570); self.metric_text.pack(anchor='w',pady=7)
        self.risk=self.card(bottom,'แผนและคำเตือน'); self.risk.pack(side='left',fill='both',expand=True,padx=(6,0))
        self.risk_text=tk.Label(self.risk,text='Entry: —   SL: —   TP: —\nสัญญาณเป็นข้อมูลประกอบ ไม่รับประกันผลลัพธ์',bg=PANEL,fg=MUTED,font=('Segoe UI',10),justify='left',wraplength=570); self.risk_text.pack(anchor='w',pady=7)
        self.status=tk.Label(self.body,text='พร้อมใช้งาน',bg=BG,fg=MUTED,anchor='w',font=('Segoe UI',9)); self.status.pack(fill='x',padx=20,pady=(0,8))

    def _chart_style(self):
        self.ax.set_facecolor(PANEL); self.ax.tick_params(colors=MUTED,labelsize=8)
        for sp in self.ax.spines.values(): sp.set_color('#2a3b54')
        self.ax.grid(True,color='#26364d',linewidth=.5,alpha=.8)

    def _app_root(self):
        if getattr(sys, 'frozen', False): return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def check_for_updates(self):
        self.status.config(text='กำลังตรวจสอบเวอร์ชันจาก GitHub...')
        threading.Thread(target=self._check_update_worker, daemon=True).start()

    def _check_update_worker(self):
        try:
            url=f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
            req=urllib.request.Request(url, headers={'User-Agent':'ForexAI-PRO-Updater','Accept':'application/vnd.github+json'})
            with urllib.request.urlopen(req, timeout=12) as response:
                release=json.loads(response.read().decode('utf-8'))
            tag=str(release.get('tag_name','')).lstrip('v')
            assets=release.get('assets',[])
            asset=next((a for a in assets if a.get('name')==UPDATE_ASSET),None)
            if not tag:
                raise RuntimeError('Release ล่าสุดไม่มี tag version')
            if self._version_tuple(tag) <= self._version_tuple(APP_VERSION):
                self.after(0, lambda: (self.status.config(text=f'ใช้งานเวอร์ชันล่าสุดแล้ว • v{APP_VERSION}'), messagebox.showinfo('ForexAI PRO','คุณใช้เวอร์ชันล่าสุดแล้ว')))
                return
            if not asset:
                self.after(0, lambda: (self.status.config(text='พบเวอร์ชันใหม่ แต่ Release ยังไม่มีไฟล์อัปเดต'), messagebox.showwarning('พบอัปเดต',f'มีเวอร์ชัน {tag} แต่ยังไม่มีไฟล์ {UPDATE_ASSET} ใน GitHub Release')))
                return
            self.after(0, lambda: self._offer_update(tag, asset['browser_download_url']))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                msg = (
                    'ยังไม่พบ GitHub Release ล่าสุดสำหรับโปรแกรมนี้.\\n\\n'
                    'โปรดเผยแพร่ Release ใน GitHub ก่อนทดสอบอัปเดต\\n'
                    f'https://github.com/{GITHUB_REPO}/releases'
                )
                self.after(0, lambda msg=msg: (
                    self.status.config(text='ยังไม่มี GitHub Release'),
                    messagebox.showwarning('ยังไม่มี GitHub Release', msg)
                ))
            else:
                msg=f'GitHub ตอบกลับ HTTP {e.code}: {e.reason}'
                self.after(0, lambda msg=msg: (
                    self.status.config(text='ตรวจสอบอัปเดตไม่สำเร็จ'),
                    messagebox.showerror('ตรวจสอบอัปเดต', msg)
                ))
        except Exception as e:
            msg=str(e)
            self.after(0, lambda: (self.status.config(text='ตรวจสอบอัปเดตไม่สำเร็จ'), messagebox.showerror('ตรวจสอบอัปเดต',f'เชื่อมต่อ GitHub ไม่สำเร็จ\\n{msg}')))

    @staticmethod
    def _version_tuple(value):
        try: return tuple(int(part) for part in value.split('.')[:3])
        except Exception: return (0,)

    def _offer_update(self, version, url):
        if messagebox.askyesno('พบอัปเดต ForexAI PRO',f'พบเวอร์ชันใหม่ v{version}\nต้องการดาวน์โหลดและติดตั้งหรือไม่?\nโปรแกรมจะปิดและเปิดใหม่หลังติดตั้ง'):
            self.status.config(text=f'กำลังดาวน์โหลดอัปเดต v{version}...')
            threading.Thread(target=self._download_update_worker,args=(version,url),daemon=True).start()

    def _download_update_worker(self, version, url):
        try:
            root=self._app_root(); updates=os.path.join(root,'updates'); os.makedirs(updates,exist_ok=True)
            bundle=os.path.join(updates,'update.zip'); temp=bundle+'.download'
            req=urllib.request.Request(url,headers={'User-Agent':'ForexAI-PRO-Updater'})
            with urllib.request.urlopen(req,timeout=60) as response, open(temp,'wb') as out:
                while True:
                    chunk=response.read(1024*256)
                    if not chunk: break
                    out.write(chunk)
            with zipfile.ZipFile(temp,'r') as z:
                for name in z.namelist():
                    part=__import__('pathlib').Path(name)
                    if part.is_absolute() or '..' in part.parts or name.startswith(('\\','/')): raise ValueError('ไฟล์อัปเดตมีเส้นทางไม่ปลอดภัย')
                if not z.namelist(): raise ValueError('แพ็กเกจอัปเดตว่างเปล่า')
            os.replace(temp,bundle)
            helper=os.path.join(root,'ForexAI_Updater.exe')
            if not os.path.isfile(helper):
                raise RuntimeError('ไม่พบ ForexAI_Updater.exe กรุณาสร้างตัวติดตั้งเวอร์ชันที่มีตัวช่วยอัปเดตก่อน')
            subprocess.Popen([helper,'--apply','--pid',str(os.getpid()),'--root',root,'--bundle',bundle],cwd=root,close_fds=True)
            self.after(0,self.destroy)
        except Exception as e:
            try:
                if 'temp' in locals() and os.path.exists(temp): os.remove(temp)
            except Exception: pass
            msg=str(e)
            self.after(0,lambda: (self.status.config(text='ติดตั้งอัปเดตไม่สำเร็จ'),messagebox.showerror('อัปเดตไม่สำเร็จ',msg)))

    def refresh(self):
        if self.busy: return
        if mt5 is None:
            self.connection.config(text='● ต้องติดตั้ง MetaTrader5',fg=RED)
            self.status.config(text='ติดตั้ง dependencies ด้วยไฟล์ install_requirements.bat แล้วเปิด MT5 ก่อนวิเคราะห์')
            return
        self.busy=True; self.status.config(text='กำลังอ่านราคาจาก MT5...')
        sym=self.symbol.get().strip() or 'XAUUSD'
        threading.Thread(target=self._fetch,args=(sym,),daemon=True).start()

    def _fetch(self,sym):
        try:
            if not mt5.initialize(): raise RuntimeError(f'MT5 initialize ไม่สำเร็จ: {mt5.last_error()}')
            if not mt5.symbol_select(sym,True): raise RuntimeError(f'ไม่พบสัญลักษณ์ {sym}; ตรวจชื่อใน Market Watch')
            def get(tf,n):
                rates=mt5.copy_rates_from_pos(sym,tf,1,n) # closed candles only
                if rates is None or len(rates)==0: raise RuntimeError(f'ไม่มีข้อมูลแท่งเทียน: {mt5.last_error()}')
                rows=[]
                for x in rates:
                    rows.append({'time_utc':datetime.fromtimestamp(int(x['time']),timezone.utc).isoformat(), 'open':float(x['open']),'high':float(x['high']),'low':float(x['low']),'close':float(x['close'])})
                return enrich(rows)
            m5=get(mt5.TIMEFRAME_M5,180); m15=get(mt5.TIMEFRAME_M15,350); h1=get(mt5.TIMEFRAME_H1,350)
            tick=mt5.symbol_info_tick(sym)
            self.q.put(('ok',sym,m5,m15,h1,(float(tick.bid),float(tick.ask)) if tick else None))
        except Exception as e: self.q.put(('error',str(e)))
        finally:
            try: mt5.shutdown()
            except Exception: pass

    def poll_queue(self):
        try:
            while True:
                item=self.q.get_nowait(); self.busy=False
                if item[0]=='error':
                    self.connection.config(text='● MT5 ไม่พร้อม',fg=RED); self.status.config(text=item[1])
                else: self.render(*item[1:])
        except queue.Empty: pass
        if self.auto.get(): self.after(5000,self.refresh)
        self.after(500,self.poll_queue)

    def render(self,sym,m5,m15,h1,tick):
        self.last_rows=m5; self.last_m15=m15; self.last_h1=h1; self.live_tick=tick
        a5=analyze(m5,'M5'); a15=analyze(m15,'M15'); ah=analyze(h1,'H1')
        self.connection.config(text='● MT5 CONNECTED',fg=GREEN)
        self.price.config(text=(f'{tick[0]:,.2f} / {tick[1]:,.2f}' if tick else f"{m5[-1]['close']:,.2f}"))
        self.updated.config(text='Bid / Ask • '+datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        # Use M15 as primary, but require trend alignment for a directional call.
        sig=a15['signal']; reason='; '.join(a15['reasons'])
        if sig in ('BUY','SELL') and ah['signal'] not in ('WAIT',sig):
            sig='WAIT'; reason='M15 กับ H1 ไม่ยืนยันตรงกัน จึงรอ'
        self.sig.config(text=sig,fg=GREEN if sig=='BUY' else RED if sig=='SELL' else GOLD)
        self.sig_reason.config(text=reason)
        self.trends.config(text=f"M5   {a5['trend']} / {a5['signal']}\nM15  {a15['trend']} / {a15['signal']}\nH1    {ah['trend']} / {ah['signal']}")
        r=m15[-1]
        self.metric_text.config(text=f"RSI14: {r.get('RSI14',0):.2f}     MACD Hist: {r.get('MACD_histogram',0):.4f}\nEMA20: {r.get('EMA20',0):.2f}   EMA50: {r.get('EMA50',0):.2f}   EMA200: {r.get('EMA200',0):.2f}   ATR14: {r.get('ATR14',0):.3f}")
        if sig in ('BUY','SELL') and a15.get('entry') is not None:
            self.risk_text.config(text=f"Entry อ้างอิง: {a15['entry']:.2f}\nStop Loss: {a15['sl']:.2f}    Take Profit: {a15['tp']:.2f}    R:R 1.5:1\nเป็นระดับตาม ATR ไม่ใช่คำสั่งซื้อขาย")
        else: self.risk_text.config(text='Entry: —   Stop Loss: —   Take Profit: —\nยังไม่มีสัญญาณผ่านเกณฑ์ หรือกรอบเวลาไม่ยืนยันกัน')
        self.draw_chart({'M5':m5,'M15':m15,'H1':h1}.get(self.chart_tf.get(),m5), tick[0] if tick else m5[-1]['close'])
        self.status.config(text=f'อัปเดตสำเร็จ • {sym} • ใช้แท่งที่ปิดแล้ว • {len(m5)} แท่ง M5 • ไม่ส่งคำสั่งซื้อขาย')

    def _redraw_selected(self):
        rows = {'M5':getattr(self,'last_rows',[]),'M15':getattr(self,'last_m15',[]),'H1':getattr(self,'last_h1',[])}.get(self.chart_tf.get(),[])
        tick = getattr(self,'live_tick',None)
        if rows: self.draw_chart(rows, tick[0] if tick else rows[-1]['close'])

    def draw_chart(self,rows,live_price=None):
        if not self.fig: return
        rows=rows[-100:]; ax=self.ax; ax.clear(); self._chart_style()
        xs=list(range(len(rows)))
        for i,r in zip(xs,rows):
            o,h,l,c=r['open'],r['high'],r['low'],r['close']; color=GREEN if c>=o else RED
            ax.vlines(i,l,h,color=color,linewidth=1)
            body=max(abs(c-o),0.015)
            ax.add_patch(Rectangle((i-.28,min(o,c)),.56,body,facecolor=color,edgecolor=color,linewidth=.5))
        def ema_line(period):
            vals=[r.get(f'EMA{period}') for r in rows]
            ax.plot(xs,vals,linewidth=1.1,label=f'EMA {period}')
        for p in (20,50,200): ema_line(p)
        if live_price is not None:
            ax.axhline(live_price,color=GOLD,linewidth=1.0,linestyle='--',alpha=.9,label=f'Live {live_price:,.2f}')
        ax.set_xlim(-1,len(rows)); ax.set_ylabel('ราคา',color=MUTED); ax.tick_params(axis='x',bottom=False,labelbottom=False)
        ax.legend(loc='upper left',facecolor=PANEL,labelcolor=TEXT,framealpha=.85,ncol=4,fontsize=8)
        self.fig.tight_layout(); self.chart.draw_idle()

if __name__=='__main__':
    app=ForexAIPro(); app.mainloop()
