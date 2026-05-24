import rumps
import subprocess
import threading
import json
import asyncio
import websockets
from pathlib import Path
import psutil

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
_CUSTOM_LOGO = PROJECT_ROOT / "frontend" / "images" / "logo.png"
ICON_PATH = str(_CUSTOM_LOGO) if _CUSTOM_LOGO.exists() else None
IP_FILE = PROJECT_ROOT / "sentinel_ip.txt"

class AgentAlphaTrayApp(rumps.App):
    def __init__(self):
        super(AgentAlphaTrayApp, self).__init__(name="Agent Alpha", icon=ICON_PATH, quit_button=None)
        
        # UI Elements referencing
        self.item_status = rumps.MenuItem("🛡️ Sentinel: 🔴 Offline")
        self.item_link = rumps.MenuItem("🔗 Link Windows Sentinel...", callback=self.link_sentinel)
        self.item_alerts = rumps.MenuItem("🚨 Total Alerts: 0", callback=self.clear_alerts)
        
        self.item_start_docker = rumps.MenuItem("▶ Start Mac Docker Bot")
        self.item_start_docker.set_callback(self.start_docker)
        
        self.item_stop_docker = rumps.MenuItem("⏹ Stop Mac Docker Bot")
        self.item_stop_docker.set_callback(self.stop_docker)
        
        self.item_settings = rumps.MenuItem("⚙️ Settings")
        self.item_autolaunch = rumps.MenuItem("Auto-Launch on Login", callback=self.toggle_autolaunch)
        self.item_settings.add(self.item_autolaunch)
        
        self.item_quit = rumps.MenuItem("Quit Agent Alpha", callback=rumps.quit_application)
        
        self.menu = [
            self.item_status,
            self.item_link,
            self.item_alerts,
            None,
            self.item_start_docker,
            self.item_stop_docker,
            None,
            self.item_settings,
            self.item_quit
        ]
        
        self.sentinel_ip = self.load_ip()
        self.sentinel_alerts = 0
        self.ws_connected = False
        self.loop = asyncio.new_event_loop()
        
        # Start background WebSocket listener
        self.ws_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.ws_thread.start()
        
        # Status poller (Docker checks)
        self.timer = rumps.Timer(self.check_system_status, 3)
        self.timer.start()

    def load_ip(self):
        if IP_FILE.exists():
            return IP_FILE.read_text().strip()
        return None

    def save_ip(self, ip):
        IP_FILE.write_text(ip)
        self.sentinel_ip = ip

    def clear_alerts(self, _):
        self.sentinel_alerts = 0
        self._update_ui()

    def link_sentinel(self, _):
        window = rumps.Window(
            message="Enter the IPv4 Address of your Windows Laptop (e.g. 192.168.1.10):",
            title="Link Sentinel Uplink",
            default_text=self.sentinel_ip if self.sentinel_ip else "",
            cancel="Cancel",
            dimensions=(300, 22)
        )
        response = window.run()
        if response.clicked:
            ip = response.text.strip()
            if ip:
                self.save_ip(ip)
                rumps.notification("Agent Alpha", "Uplink Configured", f"Connecting to {ip}...")

    def _run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._ws_listener())

    async def _ws_listener(self):
        while True:
            if not self.sentinel_ip:
                self.ws_connected = False
                self._update_ui()
                await asyncio.sleep(3)
                continue
                
            uri = f"ws://{self.sentinel_ip}:9090"
            try:
                async with websockets.connect(uri, ping_timeout=None) as websocket:
                    self.ws_connected = True
                    self._update_ui()
                    rumps.notification("Agent Alpha", "Uplink Established", "Successfully connected to Windows Sentinel!")
                    
                    while True:
                        msg = await websocket.recv()
                        alert = json.loads(msg)
                        self.sentinel_alerts += 1
                        self._update_ui()
                        
                        cat = alert.get("category", "ALERT")
                        headline = alert.get("headline", "News")
                        rumps.notification(f"🚨 SENTINEL: {cat}", "Agent Alpha", headline)
                        
            except Exception:
                if self.ws_connected:
                    rumps.notification("Agent Alpha", "Uplink Lost", "Connection to Windows Sentinel dropped. Retrying...")
                self.ws_connected = False
                self._update_ui()
                await asyncio.sleep(5)

    def _update_ui(self):
        # Update connection status
        status = "🟢 Connected" if self.ws_connected else "🔴 Offline"
        self.item_status.title = f"🛡️ Sentinel: {status}"
        
        # Update alerts counter
        self.item_alerts.title = f"🚨 Total Alerts: {self.sentinel_alerts}"
        
        # Update top menu bar icon
        title = ""
        if self.sentinel_alerts > 0:
            title += f" [🚨 {self.sentinel_alerts}]"
        self.title = title if title else None

    def check_system_status(self, _):
        # Update Docker Status visually
        try:
            res = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
            if "agent_alpha_bot" in res.stdout:
                self.item_start_docker.title = "▶ Mac Docker Bot: 🟢 RUNNING"
            else:
                self.item_start_docker.title = "▶ Start Mac Docker Bot"
        except Exception:
            pass

    def start_docker(self, _):
        rumps.notification("Agent Alpha", "Starting Engine", "Booting Docker container...")
        def _run():
            subprocess.run(["docker-compose", "up", "-d"], cwd=str(PROJECT_ROOT))
        threading.Thread(target=_run).start()

    def stop_docker(self, _):
        rumps.notification("Agent Alpha", "Stopping Engine", "Shutting down Docker container...")
        def _run():
            subprocess.run(["docker-compose", "down"], cwd=str(PROJECT_ROOT))
        threading.Thread(target=_run).start()

    def toggle_autolaunch(self, sender):
        sender.state = not sender.state
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.agentalpha.menubar.plist"
        if sender.state:
            python_path = str(PROJECT_ROOT / "venv" / "bin" / "python3")
            script_path = str(PROJECT_ROOT / "backend" / "menubar_app.py")
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
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
</dict>
</plist>'''
            try:
                plist_path.parent.mkdir(parents=True, exist_ok=True)
                with open(plist_path, "w") as f:
                    f.write(plist_content)
                subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)
            except Exception:
                pass
        else:
            try:
                if plist_path.exists():
                    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
                    plist_path.unlink()
            except Exception:
                pass

if __name__ == "__main__":
    app = AgentAlphaTrayApp()
    app.run()
