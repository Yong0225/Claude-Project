// node render.js <fps> <workerIndex> <workers> <outdir>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path=require('path');
const FF=process.env.FFMPEG||'ffmpeg';
(async()=>{
  const [fps,wi,wn,out]=[+process.argv[2],+process.argv[3],+process.argv[4],process.argv[5]];
  const b=await chromium.launch({args:['--allow-file-access-from-files']});
  const p=await b.newPage({viewport:{width:1080,height:1920}});
  p.on('pageerror',e=>console.log('pageerror:',e.message));
  await p.goto('file://'+path.resolve('comp/index.html'));
  await p.evaluate(()=>window.ready);
  const END=await p.evaluate(()=>T.END);
  let N=Math.round(END*fps), per=Math.ceil(N/wn), f0=wi*per, f1=Math.min(N,f0+per);
  if(process.env.R0){const a=+process.env.R0,b=+process.env.R1,pp=Math.ceil((b-a)/wn);f0=a+wi*pp;f1=Math.min(b,f0+pp);}
  const ff=spawn(FF,['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','png','-i','-','-c:v','libx264','-preset','medium','-crf','14','-pix_fmt','yuv420p','-x264-params','keyint=60',`${out}/${process.env.PRE||'seg'}${wi}.mp4`],{stdio:['pipe','inherit','inherit']});
  const cdp=await p.context().newCDPSession(p);
  const t0=Date.now();
  for(let f=f0;f<f1;f++){
    await p.evaluate(t=>frame(t),f/fps);
    const buf=Buffer.from((await cdp.send('Page.captureScreenshot',{format:'png',optimizeForSpeed:true})).data,'base64');
    if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r));
    if((f-f0)%300===0) console.log(`w${wi} ${f-f0}/${f1-f0} ${((Date.now()-t0)/1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r=>ff.on('close',r));
  await b.close();
})();
