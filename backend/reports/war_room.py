"""
Agent Alpha v4.0 - The War Room
Generates a weekly PDF strategy brief using fpdf2 + matplotlib.
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

# Fix imports if running independently
sys.path.insert(0, str(Path(__file__).parent.parent))
import database as db
from analysis.regime import get_current_market_regime
from arena.championship import get_leaderboard
from reports.charts import generate_equity_curve, generate_model_accuracy_bar
from bot.daily_job import send_telegram_sync

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent / "weekly"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class WarRoomPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(59, 130, 246) # Blue
        self.cell(0, 10, 'AGENT ALPHA v4.0 - THE WAR ROOM', 0, 1, 'C')
        
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f'Weekly Intelligence Briefing | Date: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_war_room_pdf():
    """Generates the weekly War Room PDF using fpdf2 and matplotlib."""
    logger.info("🏛️ Entering The War Room. Compiling weekly briefing...")
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = REPORTS_DIR / f"war_room_{timestamp}.pdf"
    
    pdf = WarRoomPDF()
    pdf.add_page()
    
    # --- SECTION 1: Arena Performance ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, '1. The Arena Performance (Paper Trading)', 0, 1)
    
    # Generate Chart
    # In reality we would fetch portfolio state from DB here
    portfolio_data = [] 
    try:
        rows = db.db_execute("SELECT * FROM paper_portfolio ORDER BY id DESC LIMIT 5")
        if rows:
            portfolio_data = [{"date": r[1], "total_equity": r[4], "benchmark_nifty_return_pct": r[9]} for r in reversed(rows)]
    except Exception:
        pass
        
    chart_path = generate_equity_curve(portfolio_data)
    pdf.image(chart_path, x=15, w=180)
    pdf.ln(5)
    
    # --- SECTION 2: Trade Log ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '2. Weekly Trade Log (Autopsy)', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    
    try:
        trades = db.db_execute("SELECT symbol, trade_type, status, net_pnl, autopsy_json FROM paper_trades ORDER BY id DESC LIMIT 5")
        if trades:
            for t in trades:
                pnl = t["net_pnl"] if t["net_pnl"] else 0
                autopsy = ""
                if t["autopsy_json"]:
                    import json
                    try:
                        autopsy = " | Autopsy: " + json.loads(t["autopsy_json"]).get("summary", "")
                    except: pass
                text = f"{t['trade_type']} {t['symbol']} - Status: {t['status']} | PnL: Rs. {pnl:.2f}{autopsy}"
                # Handle cell text wrapping since autopsy can be long
                pdf.multi_cell(0, 6, text.encode('latin-1', 'replace').decode('latin-1'))
                pdf.ln(2)
        else:
            pdf.cell(0, 6, "No trades executed this week.", 0, 1)
    except Exception:
        pdf.cell(0, 6, "Trade log data unavailable.", 0, 1)
    pdf.ln(5)
    
    # --- SECTION 3: Model Championship ---
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '3. Model Championship Leaderboard', 0, 1)
    
    champs = []
    try:
        champs = get_leaderboard()
    except Exception:
        pass
        
    bar_chart_path = generate_model_accuracy_bar(champs)
    pdf.image(bar_chart_path, x=15, w=180)
    pdf.ln(5)
    
    # --- SECTION 4: Regime Analysis ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '4. Market Regime Analysis', 0, 1)
    pdf.set_font('Helvetica', '', 11)
    try:
        from analysis.regime import detect_market_regime
        regime_data = detect_market_regime()
        regime = regime_data.get("regime", "UNKNOWN").replace("_", " ").title()
        vix = regime_data.get("vix_level", 0.0)
        prob = regime_data.get("crisis_probability_tomorrow_pct", 10.0)
        pdf.multi_cell(0, 8, f"The overall market is currently operating in a {regime} regime. VIX level is at {vix:.2f} (Trending). Crisis Probability is currently modeled at {prob:.1f}%.")
    except Exception:
        pdf.multi_cell(0, 8, "Regime data unavailable.")
    pdf.ln(5)
    
    # --- SECTION 5: Sentinel Highlights ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '5. Sentinel Highlights (Top News)', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    try:
        import sqlite3
        conn = sqlite3.connect(str(Path(__file__).parent.parent.parent / "sentinel" / "sentinel_alerts.db"))
        c = conn.cursor()
        c.execute("SELECT category, severity, headline FROM alerts ORDER BY id DESC LIMIT 5")
        alerts = c.fetchall()
        conn.close()
        
        if alerts:
            for a in alerts:
                text = f"[{a[0]} - Sev {a[1]}] {a[2]}"
                clean_text = text.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 6, clean_text, 0, 1)
        else:
            pdf.cell(0, 6, "No major Sentinel alerts triggered this week.", 0, 1)
    except Exception:
        pdf.cell(0, 6, "Sentinel database unavailable. Is the daemon running?", 0, 1)
    pdf.ln(5)
    
    # --- SECTION 6: Next Week Outlook ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '6. Next Week Outlook', 0, 1)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, "Upcoming Macro Calendar: RBI Policy Minutes, US CPI Data (Estimated).")
    pdf.ln(3)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "Agent Alpha Top Watchlist for Next Week:", 0, 1)
    pdf.set_font('Helvetica', '', 11)
    
    try:
        conn = db.get_db()
        c = conn.cursor()
        c.execute("SELECT symbol, confidence, rationale FROM signals WHERE type='LONG' ORDER BY confidence DESC LIMIT 3")
        top_longs = c.fetchall()
        conn.close()
        
        if top_longs:
            for s in top_longs:
                sym = s["symbol"]
                conf = s["confidence"]
                rat = s["rationale"][:60] + "..." if len(s["rationale"]) > 60 else s["rationale"]
                pdf.cell(0, 6, f"• {sym} (Confidence: {conf}%): {rat}", 0, 1)
        else:
            pdf.cell(0, 6, "• No high-conviction LONG signals currently generated.", 0, 1)
    except Exception as e:
        pdf.cell(0, 6, "• Could not retrieve watchlist from database.", 0, 1)
    
    # Output PDF
    pdf.output(str(filename))
    logger.info(f"War Room PDF generated successfully: {filename}")
    
    # Auto-send to Telegram
    try:
        # We need to send document, but send_telegram_sync sends text.
        # Let's import requests and manually POST the document.
        import requests
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
            with open(filename, 'rb') as doc:
                res = requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': '🏛️ Your Weekly War Room Briefing is here.'}, files={'document': doc})
                if res.status_code == 200:
                    logger.info("War Room PDF sent to Telegram successfully.")
                else:
                    logger.warning(f"Failed to send PDF to Telegram: {res.text}")
    except Exception as e:
        logger.error(f"Error sending PDF to Telegram: {e}")
        
    return str(filename)

if __name__ == "__main__":
    generate_war_room_pdf()
