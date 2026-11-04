const {chromium}=require('C:/Users/spraman/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:800,height:1200}}),errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('file:///'+path.resolve(__dirname,'viewer_preview.html').replaceAll('\\','/'));
 const frame=page.frameLocator('iframe');
 await frame.locator('#cp-status').filter({hasText:'D8_0004'}).waitFor();
 await frame.locator('#cp-canvas').evaluate(async c=>{await new Promise(r=>setTimeout(r,300));if(!c.getContext('2d').getImageData(200,200,1,1).data[3])throw Error('Blank image');});
 const a=await frame.locator('#cp-canvas').evaluate(c=>c.toDataURL());
 await frame.locator('#cp-variant').selectOption('default');
 const b=await frame.locator('#cp-canvas').evaluate(c=>c.toDataURL());
 if(a===b)throw Error('Mask comparison did not change');
 if(!(await frame.locator('#cp-status').textContent()).includes('DAPI + GFP ·'))throw Error('Wrong input label');
 await frame.locator('#cp-blend').fill('100');
 if(b===await frame.locator('#cp-canvas').evaluate(c=>c.toDataURL()))throw Error('Blend did not change');
 await frame.locator('#cp-field').selectOption('4');
 if(!(await frame.locator('#cp-status').textContent()).includes('Weak GFP'))throw Error('D9 warning missing');
 await frame.locator('#cp-field').selectOption('0');await frame.locator('#cp-variant').selectOption('selected');await frame.locator('#cp-blend').fill('0');
 // Restore the left-side view after the field-change control centered it.
 const canvas=frame.locator('#cp-canvas'),box=await canvas.boundingBox();
 await page.mouse.move(box.x+box.width*.25,box.y+box.height*.5);await page.mouse.down();await page.mouse.move(box.x+box.width*.75,box.y+box.height*.5);await page.mouse.up();
 await page.screenshot({path:path.resolve(__dirname,'viewer_desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:1000});
 if(await frame.locator('#cellpose-third-channel-review').evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2))throw Error('Horizontal overflow');
 if(errors.length)throw Error(errors.join('\n'));
 console.log('Comparison, blend, field controls, pan and narrow layout passed');await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
