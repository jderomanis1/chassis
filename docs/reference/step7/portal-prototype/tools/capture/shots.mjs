import puppeteer from 'puppeteer-core';
const BASE='file:///home/box/shared/cos/chassis/portal-prototype/index.html';
const OUT='/home/box/shared/cos/chassis/portal-prototype/screens/';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--hide-scrollbars'],defaultViewport:{width:1440,height:900}});
const errs=[];
async function pg(url){const p=await b.newPage();p.on('pageerror',e=>errs.push(url+' '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push(url+' console '+m.text())});await p.goto(BASE+url,{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,600));return p}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let p;
p=await pg('?static&theme=dark#/');await p.screenshot({path:OUT+'01-home.png'});await p.close();
p=await pg('?static&theme=light#/');await p.screenshot({path:OUT+'07-light-home.png'});await p.close();
p=await pg('?static&theme=light#/i/initiative-maintenance');await p.screenshot({path:OUT+'08-light-initiative.png'});await p.close();
p=await pg('?static&theme=light#/map');await p.screenshot({path:OUT+'09-light-map.png'});await p.close();
p=await pg('?static&theme=dark#/map');{const n=await p.$('.node[data-task="task-maintenance-quotes"]');const bb=await n.boundingBox();await p.mouse.move(bb.x+bb.width/2,bb.y+bb.height/2);await sleep(300);}await p.screenshot({path:OUT+'10-dark-map-hover.png'});await p.close();
p=await pg('?static&theme=light#/i/initiative-maintenance');{const n=await p.$('.task[data-task="task-maintenance-plan"]');const bb=await n.boundingBox();await p.mouse.move(bb.x+420,bb.y+bb.height/2);await sleep(300);}await p.screenshot({path:OUT+'11-light-hovercard.png'});await p.close();
p=await pg('?theme=dark&tilt=force#/');await sleep(1800);{const n=await p.$('.tile');const bb=await n.boundingBox();await p.mouse.move(bb.x+bb.width*.5,bb.y+bb.height*.5);for(let i=0;i<12;i++){await p.mouse.move(bb.x+bb.width*(.5+i*.035),bb.y+bb.height*(.5-i*.03));await sleep(16)}await sleep(500);}await p.screenshot({path:OUT+'12-dark-tile-hover.png'});
const tf=await p.$eval('.tile',e=>getComputedStyle(e).transform);console.log('tile transform',tf);await p.close();
// extra: light restricted + light ask + map restricted hover card
p=await pg('?static&theme=light#/i/initiative-d2c-launch');{const n=await p.$('.task.restricted');const bb=await n.boundingBox();await p.mouse.move(bb.x+400,bb.y+20);await sleep(200);}await p.screenshot({path:OUT+'13-light-restricted-hovercard.png'});await p.close();
p=await pg('?static&theme=light#/?ask=What%20is%20blocking%20Ridgeview%3F');await p.screenshot({path:OUT+'14-light-ask.png'});await p.close();
console.log('errors',JSON.stringify(errs));await b.close();
