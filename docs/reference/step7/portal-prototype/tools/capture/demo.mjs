import puppeteer from 'puppeteer-core';
const BASE='file:///home/box/shared/cos/chassis/portal-prototype/index.html';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--hide-scrollbars'],defaultViewport:{width:1440,height:900}});
const p=await b.newPage();const sleep=ms=>new Promise(r=>setTimeout(r,ms));
await p.goto(BASE+'?theme=dark&tilt=force#/',{waitUntil:'networkidle0'});
// demo-only fake cursor (headless has no visible pointer); not part of the prototype file
await p.evaluate(()=>{const c=document.createElement('div');c.style.cssText='position:fixed;left:0;top:0;width:18px;height:18px;border-radius:50%;border:2px solid #fff;background:rgba(67,227,255,.5);z-index:9999;pointer-events:none;transform:translate(-50px,-50px);box-shadow:0 0 10px rgba(0,0,0,.6)';document.body.appendChild(c);document.addEventListener('pointermove',e=>c.style.transform=`translate(${e.clientX-9}px,${e.clientY-9}px)`,{passive:true})});
let mx=720,my=450;
async function glide(x,y,steps=20){for(let i=1;i<=steps;i++){await p.mouse.move(mx+(x-mx)*i/steps,my+(y-my)*i/steps);await sleep(16)}mx=x;my=y}
const rec=await p.screencast({path:'/tmp/demo.webm',fps:30});
await sleep(900);
let bb=await (await p.$('.tile')).boundingBox();
await glide(bb.x+bb.width*.3,bb.y+bb.height*.3,20);
for(let i=0;i<40;i++){const a=i/40*Math.PI*2;await p.mouse.move(bb.x+bb.width*(.5+.35*Math.cos(a)),bb.y+bb.height*(.5+.35*Math.sin(a)));await sleep(16)}
mx=bb.x+bb.width*.85;my=bb.y+bb.height*.5;
await p.mouse.click(bb.x+bb.width*.5,bb.y+60);await sleep(1300);
bb=await (await p.$('.init .btn')).boundingBox();await glide(bb.x+bb.width/2,bb.y+bb.height/2,18);await p.mouse.click(mx,my);await sleep(1100);
bb=await (await p.$('.task[data-task="task-maintenance-plan"]')).boundingBox();await glide(bb.x+430,bb.y+bb.height/2,18);await sleep(900);
bb=await (await p.$('nav.tabs a[data-tab="map"]')).boundingBox();await glide(bb.x+bb.width/2,bb.y+bb.height/2,18);await p.mouse.click(mx,my);await sleep(900);
bb=await (await p.$('.node[data-task="task-maintenance-quotes"]')).boundingBox();await glide(bb.x+bb.width/2,bb.y+bb.height/2,22);await sleep(1300);
await glide(720,820,16);
await p.focus('#ask');await p.keyboard.type('What is blocking Ridgeview?',{delay:22});await p.keyboard.press('Enter');await sleep(3600);
await rec.stop();await b.close();
