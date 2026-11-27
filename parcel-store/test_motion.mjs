// Run: node --test test_motion.mjs (synthetic DOM; no network/browser).
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
const html=readFileSync(new URL('./index.html',import.meta.url),'utf8');
const source=html.match(/<script>([\s\S]*?)<\/script>/)[1];
function harness(reduced){
 const nodes=new Map();let animations=0,loads=0;
 const el=()=>({innerHTML:'',textContent:'',value:'',open:false,offsetWidth:10,classList:{add(){},remove(){}},insertAdjacentHTML(_,h){this.innerHTML+=h},querySelector(){return this},append(){},appendChild(){},remove(){},showModal(){this.open=true},close(){this.open=false}});
 const get=k=>{if(!nodes.has(k))nodes.set(k,el());return nodes.get(k)};
 const document={getElementById:get,createElement:el,body:el(),head:{appendChild(){loads++}},querySelector:()=>el(),visibilityState:'visible',title:''};
 const location={hash:'',search:'',protocol:'https:',hostname:'preview.example'};
 const window={addEventListener(){},scrollTo(){},confirm:()=>true,matchMedia:()=>({matches:reduced}),anime:{animate(){animations++}}};
 const storage=()=>{const x={};return {getItem:k=>x[k]??null,setItem:(k,v)=>x[k]=v}};
 const run=new Function('document','window','location','localStorage','sessionStorage','setTimeout','setInterval',source+
  '\nreturn {go,openCategory,productDetails,change,render,cartCount,submitOrder,currentBatch,used,tabs,setTab,toggleDemo,db,checkoutDraft,get page(){return page},get cat(){return cat},resetCategory(){cat="Все";render()}};');
 return {api:run(document,window,location,storage(),storage(),()=>{},()=>{}),get,stats:()=>({animations,loads})};
}
test('all views and core order flow',()=>{
 const {api:a,get}=harness(false);
 const output=()=>get('app').innerHTML;
 assert.ok(output().includes('Что хочется к столу?'));
 a.openCategory(2);assert.equal(a.page,'catalog');assert.equal(a.cat,'Крупы');assert.ok(output().includes('Мистраль'));
 a.resetCategory();assert.equal((output().match(/class="card product"/g)||[]).length,13);
 a.productDetails('buck');assert.ok(get('productDialog').open);assert.ok(get('productDialog').innerHTML.includes('Состав'));
 a.change('buck',1);assert.equal(a.cartCount(),1);a.go('cart');assert.ok(output().includes('Ваша заявка'));
 a.checkoutDraft.name='Тест';a.checkoutDraft.contact='@demo';a.submitOrder({preventDefault(){}});
 assert.equal(a.db.orders.length,1);assert.equal(a.page,'orders');assert.equal(a.used(a.currentBatch()),920);
 a.go('delivery');assert.ok(output().includes('Наши посылки'));assert.ok(output().includes('EMS API'));
 a.go('admin');for(const tab of a.tabs){a.setTab(tab);assert.ok(output().length>100,tab)}
 a.toggleDemo();assert.ok(a.db.orders.some(o=>o.demo));a.toggleDemo();assert.equal(a.db.orders.length,1);
 a.go('about');assert.ok(output().includes('Как заказать'));a.go('home');assert.equal(a.page,'home');
});
test('reduced motion disables decorative animation',()=>{
 const {api:a,stats}=harness(true);a.go('catalog');a.go('home');assert.deepEqual(stats(),{animations:0,loads:0});
});
