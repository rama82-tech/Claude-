const { chromium } = require('playwright');
(async()=>{
const b = await chromium.launch(); const p = await b.newPage({ viewport:{width:1920,height:1080}, deviceScaleFactor:1 });
p.on('console', m => console.log('console:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
await p.goto('file://' + process.cwd() + '/frame.html'); await p.waitForFunction(() => document.title === 'ready', null, {timeout: 15000});
await p.screenshot({ path: process.argv[2] || 'styleframe.png' }); await b.close();})();
