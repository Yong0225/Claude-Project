const { chromium } = require('playwright');
const path=require('path');
(async()=>{
  const times=process.argv.slice(2).map(Number);
  const b=await chromium.launch({args:['--allow-file-access-from-files']});
  const p=await b.newPage({viewport:{width:1080,height:1920}});
  p.on('console',m=>{if(m.type()==='error')console.log('console:',m.text())});
  p.on('pageerror',e=>console.log('pageerror:',e.message));
  await p.goto('file://'+path.resolve('comp/index.html'));
  await p.evaluate(()=>window.ready);
  for(const t of times){ await p.evaluate(t=>frame(t),t); await p.screenshot({path:`prev/f${t.toFixed(2)}.png`}); }
  await b.close();
})();
