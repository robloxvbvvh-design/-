const { chromium } = require('playwright');
const path=require('path');
(async()=>{
  const [,,out,fps,dur,only]=process.argv;
  const b=await chromium.launch();
  const pg=await b.newPage({viewport:{width:540,height:960},deviceScaleFactor:2});
  const errs=[];pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto('file://'+path.resolve(__dirname,'scene.html'));
  const times = only? only.split(',').map(Number) : null;
  const n = times? times.length : Math.round(dur*fps);
  for(let i=0;i<n;i++){
    const t = times? times[i] : i/fps;
    await pg.evaluate(t=>render(t),t);
    await pg.screenshot({path:`${out}/f${String(i).padStart(5,'0')}.png`});
  }
  if(errs.length) console.log('ERR',errs);
  await b.close();
})();
