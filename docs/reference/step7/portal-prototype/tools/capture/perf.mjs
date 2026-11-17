import puppeteer from 'puppeteer-core';
const BASE='file:///home/box/shared/cos/chassis/portal-prototype/index.html';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--enable-gpu-rasterization'],defaultViewport:{width:1440,height:900}});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const sampler=()=>{window.__ft=[];let last=performance.now();const f=t=>{window.__ft.push(t-last);last=t;if(window.__run)requestAnimationFrame(f)};window.__run=true;requestAnimationFrame(f)};
const stats=a=>{a=a.slice(2).sort((x,y)=>x-y);const avg=a.reduce((s,x)=>s+x,0)/a.length;const p=q=>a[Math.min(a.length-1,Math.floor(a.length*q))];return {frames:a.length,avg:+avg.toFixed(2),p50:+p(.5).toFixed(2),p95:+p(.95).toFixed(2),max:+a[a.length-1].toFixed(2),over25ms:a.filter(x=>x>25).length,fps:+(1000/avg).toFixed(1)}};
async function run(label,url,fn){
  for(const theme of ['dark','light']){
  const p=await b.newPage();await p.goto(BASE+url.replace('THEME',theme),{waitUntil:'networkidle0'});await sleep(1500);
  await p.tracing.start({path:`/tmp/trace-${label}-${theme}.json`,categories:['devtools.timeline']});
  await p.evaluate(sampler);await fn(p);const ft=await p.evaluate(()=>{window.__run=false;return window.__ft});
  await p.tracing.stop();
  const tr=JSON.parse(require_fs().readFileSync(`/tmp/trace-${label}-${theme}.json`,'utf8'));
  const ev=(tr.traceEvents||tr).filter(e=>e.ph==='X'||e.ph==='B');
  const sum=n=>ev.filter(e=>e.name===n).reduce((s,e)=>s+(e.dur||0),0)/1000;
  const cnt=n=>ev.filter(e=>e.name===n).length;
  console.log(label,theme,JSON.stringify(stats(ft)),'Layout count',cnt('Layout'),'ms',sum('Layout').toFixed(1),'| UpdateLayoutTree ms',sum('UpdateLayoutTree').toFixed(1),'| Paint ms',sum('Paint').toFixed(1));
  await p.close();}
}
import fs from 'fs';function require_fs(){return fs}
await run('tile-tilt','?theme=THEME&tilt=force#/',async p=>{const bb=await (await p.$('.tile')).boundingBox();
  for(let i=0;i<150;i++){const a=i/150*Math.PI*4;await p.mouse.move(bb.x+bb.width*(.5+.4*Math.cos(a)),bb.y+bb.height*(.5+.4*Math.sin(a)));await sleep(12)}
  const bb2=await (await p.$$('.tile'))[1].boundingBox();for(let i=0;i<40;i++){await p.mouse.move(bb2.x+bb2.width*(i/40),bb2.y+bb2.height/2);await sleep(12)}});
await run('map-hover','?theme=THEME#/map',async p=>{const ns=await p.$$('.node');
  for(let r=0;r<3;r++)for(const n of ns){const bb=await n.boundingBox();for(let k=0;k<8;k++){await p.mouse.move(bb.x+20+k*20,bb.y+bb.height/2);await sleep(12)}}});
await b.close();
