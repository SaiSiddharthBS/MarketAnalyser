from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    # Capture console logs
    page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
    
    print("Navigating...")
    page.goto("http://localhost:8000")
    page.wait_for_timeout(2000)
    
    print("Clicking Arena...")
    page.click("#nav-arena")
    page.wait_for_timeout(3000)
    
    print("Done.")
    browser.close()
