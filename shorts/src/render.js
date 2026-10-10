const {chromium}=require('playwright');
const {spawn}=require('child_process');const fs=require('fs');
(async()=>{
  const [,,html,mode,out]=process.argv;
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  p.on('console',m=>console.log('console:',m.text()));p.on('pageerror',e=>console.log('ERR',e.message));
  await p.goto('file://'+html+'?render=1');await p.evaluate(()=>window.ready);
  const total=await p.evaluate(()=>TOTAL),fps=30;
  const grab=t=>p.evaluate(t=>{renderFrame(t);return document.getElementById('c').toDataURL('image/jpeg',.94).split(',')[1]},t);
  if(mode==='stills'){const ts=process.argv.slice(5).map(Number);fs.mkdirSync(out,{recursive:true});
    for(const t of ts){fs.writeFileSync(`${out}/s_${t.toFixed(1)}.jpg`,Buffer.from(await grab(t),'base64'));}
    console.log('total',total);}
  else{const n=Math.round(total*fps);
    const ff=spawn('ffmpeg',['-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','-movflags','+faststart',out],{stdio:['pipe','ignore','inherit']});
    for(let i=0;i<n;i++){const buf=Buffer.from(await grab(i/fps),'base64');if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%300===0)console.log('frame',i,'/',n);}
    ff.stdin.end();await new Promise(r=>ff.on('close',r));console.log('done',n);}
  await b.close();})();
