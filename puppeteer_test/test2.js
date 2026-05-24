const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    
    await page.goto('http://localhost:8000', {waitUntil: 'networkidle0'});
    console.log("Page loaded. Clicking Arena...");
    await page.evaluate(() => {
        document.getElementById('nav-arena').click();
    });
    
    await new Promise(r => setTimeout(r, 2000));
    
    const equityText = await page.evaluate(() => {
        return document.getElementById('arena-total-equity').textContent;
    });
    console.log("EQUITY TEXT:", equityText);
    
    const activeTab = await page.evaluate(() => {
        const el = document.querySelector('.page.active');
        return el ? el.id : 'NONE';
    });
    console.log("ACTIVE TAB ID:", activeTab);

    console.log("Done.");
    await browser.close();
})();
