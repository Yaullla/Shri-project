// Portable static preview: node build-preview.mjs
// Only the existing browser demo and its licensed animation dependency are exported.
import { mkdir, readFile, writeFile, copyFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
const root=fileURLToPath(new URL('.',import.meta.url));
const output=join(root,'dist');
await rm(output,{recursive:true,force:true});
await mkdir(join(output,'vendor'),{recursive:true});
let html=await readFile(join(root,'index.html'),'utf8');
if(!html.includes('<head>')||!html.includes('<body>'))throw Error('Unexpected prototype format');
html=html.replace('<head>','<head><meta name="robots" content="noindex,nofollow">');
html=html.replace('<body>','<body><div role="status" style="background:#edf2fa;color:#193251;padding:8px 14px;text-align:center;font:13px/1.4 system-ui">Техническая демонстрация. Только тестовые данные; реальные заказы и оплата недоступны.</div>');
await writeFile(join(output,'index.html'),html,'utf8');
for(const file of ['anime-4.5.0.min.js','anime-LICENSE.md']) await copyFile(join(root,'vendor',file),join(output,'vendor',file));
await mkdir(join(output,'marketing'),{recursive:true});
await copyFile(join(root,'marketing.html'),join(output,'marketing.html'));
for(const file of ['communities.json','campaign-new-year.txt'])await copyFile(join(root,'marketing',file),join(output,'marketing',file));
await writeFile(join(output,'robots.txt'),'User-agent: *\nDisallow: /\n');
console.log('Static preview prepared in dist; no server files or database included.');
