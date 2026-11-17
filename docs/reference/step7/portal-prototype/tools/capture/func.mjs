import puppeteer from 'puppeteer-core';
const BASE='file:///home/box/shared/cos/chassis/portal-prototype/index.html';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox'],defaultViewport:{width:1440,height:900}});
const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const st=()=>p.evaluate(()=>({theme:document.documentElement.dataset.theme,stored:localStorage.getItem('chassis-theme'),label:document.getElementById('themeToggle').getAttribute('aria-label'),pressed:document.getElementById('themeToggle').getAttribute('aria-pressed')}));
await p.emulateMediaFeatures([{name:'prefers-color-scheme',value:'light'}]);
await p.goto(BASE+'#/');await p.evaluate(()=>localStorage.clear());await p.reload();console.log('no storage, OS light:',JSON.stringify(await st()));
await p.emulateMediaFeatures([{name:'prefers-color-scheme',value:'dark'}]);await sleep(500);console.log('OS live -> dark:',JSON.stringify(await st()));
await p.goto(BASE+'?theme=light#/');await sleep(200);console.log('?theme=light:',JSON.stringify(await st()));
await p.click('#themeToggle');await sleep(600);console.log('after toggle:',JSON.stringify(await st()));
await p.goto(BASE+'#/');await p.reload();console.log('reload no param:',JSON.stringify(await st()));
await p.emulateMediaFeatures([{name:'prefers-color-scheme',value:'light'}]);await sleep(300);console.log('OS light but stored dark:',JSON.stringify(await st()));
// keyboard: Ctrl+K, focus node -> chain highlight, Esc
await p.goto(BASE+'#/map');await sleep(800);
await p.keyboard.down('Control');await p.keyboard.press('k');await p.keyboard.up('Control');console.log('ctrl+k focus:',await p.evaluate(()=>document.activeElement.id));
await p.focus('.node[data-task="task-maintenance-plan"]');await sleep(100);
console.log('focus chain lit:',await p.evaluate(()=>[...document.querySelectorAll('.node.lit')].map(n=>n.dataset.task).join(',')),'| world.focus',await p.evaluate(()=>document.getElementById('world').classList.contains('focus')),'| hovercard:',await p.evaluate(()=>document.getElementById('hcard').textContent.replace(/\s+/g,' ').trim()));
await p.focus('.node.restricted');await sleep(100);console.log('restricted hovercard:',await p.evaluate(()=>document.getElementById('hcard').textContent.trim()));
// reduced motion: answer immediate
await p.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);await p.goto(BASE+'#/?ask=x');await p.reload();await sleep(200);
console.log('reduced: answer words hidden?',await p.evaluate(()=>document.querySelectorAll('.w:not(.on)').length),'| typing class',await p.evaluate(()=>!!document.querySelector('.typing')),'| first count',await p.evaluate(()=>document.querySelector('[data-count]').textContent));
await p.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'no-preference'}]);await p.goto(BASE+'#/?ask=x');await p.reload();await sleep(4500);
console.log('animated ask: hidden words after 4.5s',await p.evaluate(()=>document.querySelectorAll('.w:not(.on)').length),'busy',await p.evaluate(()=>document.getElementById('ans')?.getAttribute('aria-busy')));
console.log('VT supported',await p.evaluate(()=>!!document.startViewTransition),'errors',JSON.stringify(errs));
await b.close();
