import puppeteer from 'puppeteer-core';
const BASE='file:///home/box/shared/cos/chassis/portal-prototype/index.html';
const OUT='/home/box/shared/cos/chassis/portal-prototype/screens/';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--hide-scrollbars'],defaultViewport:{width:1440,height:900}});
for(const [f,u] of [['02-venture','#/v/venture-ridgeview'],['02b-venture-acme','#/v/venture-acme'],['03-initiative','#/i/initiative-maintenance'],['03b-initiative-acme-masked','#/i/initiative-d2c-launch'],['04-map','#/map'],['05-ask','#/?ask=What%20is%20blocking%20Ridgeview%3F'],['06-restricted-detail','#/i/initiative-d2c-launch?task=restricted-1']]){
 const p=await b.newPage();await p.goto(BASE+'?static&theme=dark'+u,{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,400));await p.screenshot({path:OUT+f+'.png'});await p.close();}
for(const theme of ['dark','light'])for(const r of ['#/v/venture-ridgeview','#/v/venture-acme','#/i/initiative-d2c-launch','#/map']){
 const p=await b.newPage();await p.goto(BASE+`?static&theme=${theme}`+r,{waitUntil:'networkidle0'});
 const o=await p.evaluate(()=>({counts:[...document.querySelectorAll('main [data-count]')].map(e=>e.textContent).join('/'),inits:document.querySelectorAll('.init').length,rows:document.querySelectorAll('.task').length,masked:document.querySelectorAll('.task.restricted,.node.restricted').length,nodes:document.querySelectorAll('.node').length,edges:document.querySelectorAll('.edgeg').length,blocked:document.querySelectorAll('.edge.blocked').length}));
 console.log(theme,r,JSON.stringify(o));await p.close();}
await b.close();
