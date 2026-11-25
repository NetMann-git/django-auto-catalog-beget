const fs = require('fs');
const vm = require('vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('config/static/js/site-tooltips.js', 'utf8');
const start = source.indexOf('    function label(el)');
const end = source.indexOf('    function hide()', start);
const context = {URL, location: {href: 'https://carstar-rnd.ru/catalog/', origin:'https://carstar-rnd.ru'}, clean: v => (v || '').replace(/\s+/g,' ').trim()};
vm.createContext(context);
vm.runInContext(source.slice(start,end),context);
function el(text, href=null, classes=[], active=false, explicit=null) {
 return {innerText:text,value:'',target:'', classList:{contains:x=>x==='active'&&active},getAttribute:k=>({'href':href,'data-tooltip':explicit}[k]??null),matches:s=>s==='a[href]'?href!==null:s.split(',').some(x=>classes.includes(x.trim()))};
}
const checks = [
 [el('Каталог','/catalog/'),'подобрать автомобиль'],
 [el('BMW','/catalog/?brand=4'),'только автомобили этой марки'],
 [el('Сравнение 3','/catalog/comparison/'),'Сопоставить характеристики'],
 [el('Audi A3','/catalog/audi-a3-3/'),'комплектацию'],
 [el('SUV',null),''],
 [el('Сравнить',null,['.compare-btn']),'сопоставления характеристик'],
 [el('Убрать',null,['.compare-btn'],true),'Исключить'],
 [el('Жду звонка',null,['.footer-callback__submit']),'Дождитесь'],
 [el('Связаться с нами ↗','/#callback',['[data-footer-callback]']),'Открыть форму'],
 [el('Новая кнопка',null,[],false,'Точное пояснение'),'Точное пояснение'],
 [el('Каталог','/catalog/',[],false,''),''],
 [el('Удалить','/catalog/delete/7/'),'удалению'],
 [el('Отмена','/catalog/manage/'),'список автомобилей'],
 [el('Название','/unknown/'),'']
];
for(const [input, expected] of checks) {
 const result=context.label(input);
 if(expected==='') assert.equal(result,''); else assert.ok(result.includes(expected), result);
 assert.notEqual(result,input.innerText);
}
console.log(`${checks.length} tooltip resolver checks passed`);
