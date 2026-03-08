const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: "new"
  });
  const page = await browser.newPage();
  
  // Capture console messages
  page.on('console', msg => {
    if (msg.type() === 'error') {
        console.log(`PAGE LOG [${msg.type()}]:`, msg.text());
    }
  });

  page.on('pageerror', err => {
    console.log('PAGE ERROR:', err.message);
  });

  await page.goto('http://localhost:3000');
  
  // Wait a bit
  await new Promise(r => setTimeout(r, 2000));
  
  // Click on "Technical" tab
  // Assuming the text inside the button is Technical
  const tabs = await page.$$('button, a');
  for (let t of tabs) {
      const text = await page.evaluate(el => el.textContent, t);
      if (text && text.includes('Technical')) {
          await t.click();
          break;
      }
  }
  
  await new Promise(r => setTimeout(r, 2000));

  // Find the period dropdown and select 2y
  // Assuming the backend has 1y and we want to change it to something else
  // To simulate going back in time:
  const selects = await page.$$('select');
  if (selects.length >= 3) {
      // Third select is the period dropdown based on TechnicalAnalysis.tsx
      await selects[2].select('2y');
  } else {
      console.log("Could not find period select");
  }
  
  await new Promise(r => setTimeout(r, 1000));
  
  // Click 'Run Full Technical Scan'
  const buttons = await page.$$('button');
  for (let b of buttons) {
      const text = await page.evaluate(el => el.textContent, b);
      if (text && text.includes('Run Full Technical Scan')) {
          await b.click();
          break;
      }
  }
  
  // Wait for load
  await new Promise(r => setTimeout(r, 8000));
  
  await browser.close();
})();
