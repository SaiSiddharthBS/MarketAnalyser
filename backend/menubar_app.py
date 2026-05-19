import rumps
import requests
import psutil
import subprocess
import threading
import json
import time
import asyncio
import websockets
from pathlib import Path

# Configuration
API_BASE = "http://127.0.0.1:8000/api"
PROJECT_ROOT = Path(__file__).parent.parent
ICON_PATH = str(PROJECT_ROOT / "frontend" / "images" / "favicon-32-v7.png")
VENV_PYTHON = str(PROJECT_ROOT / "venv" / "bin" / "python3")

class AgentAlphaTrayApp(rumps.App):
    def __init__(self):
        super(AgentAlphaTrayApp, self).__init__(name="Agent Alpha", icon=ICON_PATH)
        self.menu = [
            rumps.MenuItem("Regime: ⏳ Loading...", callback=None),
            None,
            rumps.MenuItem("📊 Top Longs", callback=None),
            rumps.MenuItem("  - Long 1 Loading...", callback=None),
            rumps.MenuItem("  - Long 2 Loading...", callback=None),
            rumps.MenuItem("  - Long 3 Loading...", callback=None),
            rumps.MenuItem("📉 Top Shorts", callback=None),
            rumps.MenuItem("  - Short 1 Loading...", callback=None),
            rumps.MenuItem("  - Short 2 Loading...", callback=None),
            rumps.MenuItem("  - Short 3 Loading...", callback=None),
            None,
            rumps.MenuItem("🚀 Run Screener Now", callback=self.run_screener),
            rumps.MenuItem("📲 Send Telegram Briefing", callback=self.send_telegram),
            rumps.MenuItem("📋 Copy Latest Intel", callback=self.copy_intel),
            None,
            ("⚙️ Settings", [
                rumps.MenuItem("Show Ticker in Menu Bar", callback=self.toggle_ticker),
                rumps.MenuItem("Auto-Launch on Login", callback=self.toggle_autolaunch)
            ]),
            rumps.MenuItem("Turn Server ON", callback=self.turn_server_on),
            rumps.MenuItem("Turn Server OFF", callback=self.turn_server_off),
            None,
            rumps.MenuItem("🚨 HALT SYSTEM (Kill Switch)", callback=self.kill_switch)
        ]
        
        # Initialize Settings state
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.agentalpha.menubar.plist"
        self.menu["⚙️ Settings"]["Auto-Launch on Login"].state = plist_path.exists()
        
        self.show_ticker = False
        self.server_process = None
        self.long_keys = ["  - Long 1 Loading...", "  - Long 2 Loading...", "  - Long 3 Loading..."]
        self.short_keys = ["  - Short 1 Loading...", "  - Short 2 Loading...", "  - Short 3 Loading..."]
        
        # Initialize server status visually
        self.update_server_status()
        
        # Sentinel Integration
        self.sentinel_alerts = 0
        self.ws_thread = threading.Thread(target=self._start_ws_client, daemon=True)
        self.ws_thread.start()
        
    def _start_ws_client(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._ws_listener())
        
    async def _ws_listener(self):
        # Adjust IP as needed to point to Windows laptop
        uri = "ws://192.168.1.100:9090" # Example IP
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    while True:
                        msg = await websocket.recv()
                        alert = json.loads(msg)
                        self.sentinel_alerts += 1
                        
                        # Store alert locally on Mac
                        try:
                            import sqlite3
                            conn = sqlite3.connect(str(PROJECT_ROOT / "mac_alerts.db"))
                            c = conn.cursor()
                            c.execute('''CREATE TABLE IF NOT EXISTS mac_alerts 
                                         (id INTEGER PRIMARY KEY, category TEXT, headline TEXT, raw_json TEXT)''')
                            c.execute("INSERT INTO mac_alerts (category, headline, raw_json) VALUES (?, ?, ?)",
                                      (alert.get("category", ""), alert.get("headline", ""), msg))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            print(f"Failed to store Mac alert: {e}")
                        
                        cat = alert.get("category", "ALERT")
                        headline = alert.get("headline", "News")
                        rumps.notification(f"🚨 SENTINEL: {cat}", "Agent Alpha", headline)
                        self._update_title()
            except Exception:
                await asyncio.sleep(10) # Reconnect delay

    def _update_title(self):
        title = ""
        if self.show_ticker:
            title += " α"
        if self.sentinel_alerts > 0:
            title += f" [🚨 {self.sentinel_alerts}]"
        
        self.title = title if title else None
        
    @rumps.timer(60)
    def update_data(self, _):
        """Polls the backend API for live data every 60 seconds"""
        if not self.is_server_running():
            self.menu["🟢 Server: Online"].title = "🔴 Server: Offline (Click to Start)"
            self._update_title()
            self.menu["Regime: ⏳ Loading..."].title = "Regime: 🔴 Server Offline"
            return
            
        self.menu["🟢 Server: Online"].title = "🟢 Server: Online (Click to Stop)"
        
        # 1. Fetch Regime
        try:
            res = requests.get(f"{API_BASE}/market/regime", timeout=5)
            if res.status_code == 200:
                data = res.json()
                regime = data.get("current_regime", "Unknown")
                icon = "🟢" if "Bull" in regime else "🔴" if "Bear" in regime else "⚠️" if "Crisis" in regime else "🟡"
                self.menu["Regime: ⏳ Loading..."].title = f"{icon} Regime: {regime}"
        except Exception:
            pass

        # 2. Fetch Top Picks
        try:
            res = requests.get(f"{API_BASE}/screener/top", timeout=5)
            if res.status_code == 200:
                data = res.json()
                longs = data.get("longs", [])[:3]
                shorts = data.get("shorts", [])[:3]
                
                # Update longs
                for i in range(3):
                    key = self.long_keys[i]
                    menu_item = self.menu[key]
                    if i < len(longs):
                        sym = longs[i].get('symbol', '').replace('.NS', '')
                        new_title = f"  🟢 {sym}  ▃▅▆▇"
                        menu_item.title = new_title
                        self.long_keys[i] = new_title  # update key reference
                    else:
                        menu_item.title = f"  - Long {i+1} N/A"
                        self.long_keys[i] = f"  - Long {i+1} N/A"
                        
                # Update shorts
                for i in range(3):
                    key = self.short_keys[i]
                    menu_item = self.menu[key]
                    if i < len(shorts):
                        sym = shorts[i].get('symbol', '').replace('.NS', '')
                        new_title = f"  🔴 {sym}  ▇▆▅▃"
                        menu_item.title = new_title
                        self.short_keys[i] = new_title
                    else:
                        menu_item.title = f"  - Short {i+1} N/A"
                        self.short_keys[i] = f"  - Short {i+1} N/A"

        except Exception:
            pass
            
        # 3. Update Menu Bar Ticker (Optional)
        # 3. Update Menu Bar Ticker (Optional)
        title = ""
        if self.show_ticker:
            try:
                res = requests.get(f"{API_BASE}/market/index/^NSEI", timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    pct = data.get("regularMarketChangePercent", 0)
                    sign = "+" if pct >= 0 else ""
                    title = f" α NIFTY {sign}{pct:.2f}%"
                else:
                    title = " α"
            except Exception:
                title = " α"
                
        if self.sentinel_alerts > 0:
            title += f" [🚨 {self.sentinel_alerts}]"
            
        self.title = title if title else None

    def run_screener(self, _):
        rumps.notification("Agent Alpha", "Screener Started", "Executing walk-forward machine learning ensemble...")
        def _run():
            try:
                requests.get(f"{API_BASE}/signals/generate", timeout=60)
                rumps.notification("Agent Alpha", "Screener Complete", "New signals generated successfully.")
            except Exception as e:
                rumps.notification("Agent Alpha", "Screener Failed", str(e))
        threading.Thread(target=_run).start()

    def send_telegram(self, _):
        rumps.notification("Agent Alpha", "Telegram Alert", "Compiling daily briefing...")
        def _run():
            try:
                requests.post(f"{API_BASE}/bot/alert", timeout=60)
                rumps.notification("Agent Alpha", "Telegram Alert", "Briefing dispatched successfully.")
            except Exception as e:
                rumps.notification("Agent Alpha", "Telegram Alert Failed", str(e))
        threading.Thread(target=_run).start()
        
    def copy_intel(self, _):
        import subprocess
        # Get latest intel and copy to clipboard via pbcopy
        try:
            res = requests.get(f"{API_BASE}/market/regime", timeout=5)
            intel = json.dumps(res.json(), indent=2)
            subprocess.run("pbcopy", universal_newlines=True, input=intel)
            rumps.notification("Agent Alpha", "Intel Copied", "Latest market intel copied to clipboard.")
        except Exception:
            rumps.notification("Agent Alpha", "Copy Failed", "Could not reach backend server.")

    def toggle_ticker(self, sender):
        sender.state = not sender.state
        self.show_ticker = sender.state
        if not self.show_ticker:
            self.title = None
        self.update_data(None)

    def toggle_autolaunch(self, sender):
        sender.state = not sender.state
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.agentalpha.menubar.plist"
        
        if sender.state:
            # Enable auto-launch
            python_path = str(PROJECT_ROOT / "venv" / "bin" / "python3")
            script_path = str(PROJECT_ROOT / "backend" / "menubar_app.py")
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agentalpha.menubar</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>/tmp/agentalpha.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/agentalpha.out</string>
</dict>
</plist>"""
            try:
                plist_path.parent.mkdir(parents=True, exist_ok=True)
                with open(plist_path, "w") as f:
                    f.write(plist_content)
                subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)
                rumps.notification("Agent Alpha", "Auto-Launch Enabled", "Agent Alpha will now start automatically when you log in.")
            except Exception as e:
                rumps.notification("Agent Alpha", "Auto-Launch Failed", f"Could not enable auto-launch: {e}")
                sender.state = False
        else:
            # Disable auto-launch
            try:
                if plist_path.exists():
                    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
                    plist_path.unlink()
                rumps.notification("Agent Alpha", "Auto-Launch Disabled", "Agent Alpha will no longer start automatically.")
            except Exception as e:
                rumps.notification("Agent Alpha", "Disable Failed", f"Could not disable auto-launch: {e}")
                sender.state = True

    def is_server_running(self):
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'uvicorn' in ' '.join(proc.info['cmdline']) and 'main:app' in ' '.join(proc.info['cmdline']):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def update_server_status(self):
        running = self.is_server_running()
        self.menu["Turn Server ON"].state = running
        self.menu["Turn Server OFF"].state = not running

    def turn_server_off(self, _):
        if self.is_server_running():
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'uvicorn' in ' '.join(proc.info['cmdline']):
                        proc.kill()
                except Exception:
                    pass
            rumps.notification("Agent Alpha", "Server Offline", "Backend services have been shut down.")
        self.update_server_status()

    def turn_server_on(self, _):
        if not self.is_server_running():
            rumps.notification("Agent Alpha", "Server Starting", "Booting up Uvicorn ASGI server...")
            subprocess.Popen([VENV_PYTHON, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], cwd=str(PROJECT_ROOT / "backend"))
            time.sleep(3)
        self.update_server_status()

    def kill_switch(self, _):
        # Emergency halt!
        rumps.notification("🚨 EMERGENCY HALT", "Agent Alpha", "Killing all active processes and stopping server.")
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                cmd = ' '.join(proc.info.get('cmdline', []))
                if 'uvicorn' in cmd or 'python' in cmd and ('daily_job.py' in cmd or 'main.py' in cmd):
                    proc.kill()
            except Exception:
                pass
        self.update_data(None)

if __name__ == "__main__":
    app = AgentAlphaTrayApp()
    app.run()
