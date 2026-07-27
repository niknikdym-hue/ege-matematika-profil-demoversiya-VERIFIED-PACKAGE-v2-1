import fs from 'node:fs';
import assert from 'node:assert/strict';
import { JSDOM, VirtualConsole } from 'jsdom';

const html = fs.readFileSync('ege-matematika-profil-demoversiya-PREVIEW.html', 'utf8');
assert(!html.includes('Локальный пакет проверен'));
assert(html.includes('самопроверки, не входят в официальный результат'));

const errors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', error => errors.push(String(error)));
virtualConsole.on('error', error => errors.push(String(error)));

const dom = new JSDOM(html, {
  url: 'https://eksamio.ru/ege/matematika-profil/demoversiya/',
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  virtualConsole,
  beforeParse(window) {
    window.confirm = () => true;
    window.scrollTo = () => {};
  },
});

await new Promise(resolve => setTimeout(resolve, 150));
const { document } = dom.window;
const api = dom.window.__emprofTest;
assert(api, 'test API is missing');
assert.equal(api.tasks.length, 55);
assert.equal(api.selfAssessmentAffectsOfficialTotal, false);

for (const [number, variant, phrases] of [
  [13, 1, ['верный ответ в пункте а', 'всех шагов решения обоих пунктов']],
  [13, 2, ['верный ответ в пункте а', 'всех шагов решения обоих пунктов']],
  [14, 1, ['Получен обоснованный ответ в пункте б', 'пункт а не выполнен']],
  [14, 2, ['Получен обоснованный ответ в пункте б', 'пункт а не выполнен']],
  [16, 1, ['Верно построена математическая модель']],
  [16, 2, ['Верно построена математическая модель']],
  [17, 1, ['Получен обоснованный ответ в пункте б', 'пункт а не выполнен']],
  [17, 2, ['Получен обоснованный ответ в пункте б', 'пункт а не выполнен']],
  [18, 2, ['a = −√2', 'a = √2', 'a = −√33/4', 'a = √33/4']],
]) {
  const criteria = api.getTask(number, variant).criteriaHtml;
  for (const phrase of phrases) assert(criteria.includes(phrase), `${number}/${variant}: ${phrase}`);
}

api.start();
for (let number = 1; number <= 12; number += 1) {
  const task = api.tasks.find(item => item.number === number);
  api.setTask(number, task.variant);
  const input = document.getElementById('emprof-answer');
  input.value = String(task.answer);
  input.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
}
api.finish();
assert.equal(document.getElementById('emprof-short-score').textContent, '12');

for (const select of document.querySelectorAll('#emprof-self select')) {
  const values = [...select.options].map(option => Number(option.value)).filter(Number.isFinite);
  select.value = String(Math.max(...values));
  select.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
}
assert.equal(document.getElementById('emprof-ext-score').textContent, '20');
assert.equal(document.getElementById('emprof-total-score').textContent, '—');

const meaningfulErrors = errors.filter(message => !message.includes('Not implemented: window.scrollTo'));
assert.deepEqual(meaningfulErrors, []);
console.log('Profile mathematics browser smoke test: PASS');
