const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
    page.on('response', response => {
        if (!response.ok()) console.log('RESPONSE ERROR:', response.status(), response.url());
    });
    
    await page.goto('http://localhost:8000', {waitUntil: 'networkidle0'});
    console.log("Page loaded. Clicking Arena...");
    await page.evaluate(() => {
        document.getElementById('nav-arena').click();
    });
    
    await new Promise(r => setTimeout(r, 3000));
    
    console.log("Done.");
    await browser.close();
})();
