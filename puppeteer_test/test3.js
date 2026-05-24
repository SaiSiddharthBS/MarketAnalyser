const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:8000', {waitUntil: 'networkidle0'});
    await page.evaluate(() => { document.getElementById('nav-arena').click(); });
    
    await new Promise(r => setTimeout(r, 2000));
    
    const profitText = await page.evaluate(() => document.getElementById('arena-total-profit').textContent);
    const lossText = await page.evaluate(() => document.getElementById('arena-total-loss').textContent);
    
    console.log("PROFIT TEXT:", profitText);
    console.log("LOSS TEXT:", lossText);

    await browser.close();
})();
