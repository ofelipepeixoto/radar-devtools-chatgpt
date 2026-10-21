// Local audit harness. Reads pinned upstream sources; uses only synthetic data.
// TypeScript types/import/export syntax are removed for Node vm execution.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import assert from 'node:assert/strict';
const root = path.resolve(process.argv[2] ?? '../it-tools-upstream');
function load(relative, names, extra = '') {
  let source = fs.readFileSync(path.join(root, relative), 'utf8');
  source = source.replace(/^import .*;\s*$/gm, '').replace(/^export\s*\{[^}]+\};?/gm, '').replace(/export function/g, 'function');
  source = stripTypeScriptTypes(source, { mode: 'strip' });
  const sandbox = { Math: Object.create(Math) };
  vm.createContext(sandbox);
  new vm.Script(`${extra}\n${source}\nglobalThis.result = { ${names.join(',')} };`, { filename: relative }).runInContext(sandbox, { timeout: 500 });
  return { ...sandbox.result, sandbox };
}
const rows = [];
function check(name, fn) {
  fn();
  rows.push({ name, status: 'reproduced' });
}
const regexModule = load('src/tools/regex-tester/regex-tester.service.ts', ['matchRegex']);
const { matchRegex } = regexModule;
check('regex-unmatched-optional-capture-throws', () => {
  assert.throws(() => matchRegex('(?<a>a)?b', 'b', 'dg'), /undefined/);
  assert.equal(/(?<a>a)?b/dg.exec('b')[0], 'b');
});
check('regex-main-thread-work-not-bounded', () => {
  assert.throws(() => vm.runInContext("result.matchRegex('^(a+)+$', 'a'.repeat(28)+'!', 'd')", regexModule.sandbox, { timeout:200 }), /Script execution timed out/);
});
const { convertArrayToCsv } = load('src/tools/json-to-csv/json-to-csv.service.ts', ['convertArrayToCsv']);
check('csv-quotes-use-backslash-not-rfc4180-doubling', () => {
  const actual = convertArrayToCsv({ array: [{ a: 'hello "world", test' }] });
  assert.equal(actual, 'a\n"hello \\"world\\", test"');
  assert.notEqual(actual, 'a\n"hello ""world"", test"');
});
check('csv-header-with-comma-changes-column-count', () => {
  assert.equal(convertArrayToCsv({ array: [{ 'a,b': 'value' }] }), 'a,b\nvalue');
});
check('csv-formula-cells-are-preserved', () => {
  assert.equal(convertArrayToCsv({ array: [{ sample: '=1+1' }] }), 'sample\n=1+1');
});
const randomSource = stripTypeScriptTypes(fs.readFileSync(path.join(root, 'src/utils/random.ts'), 'utf8').replace(/export\s*\{[^}]+\};?/g, ''), { mode: 'strip' });
const { createToken, sandbox } = load('src/tools/token-generator/token-generator.service.ts', ['createToken'], randomSource);
check('token-output-follows-Math.random-source', () => {
  sandbox.Math.random = () => 0;
  assert.equal(createToken({ length: 20 }), createToken({ length: 20 }));
});
check('token-default-alphabet-omits-N-and-n', () => {
  const source = fs.readFileSync(path.join(root, 'src/tools/token-generator/token-generator.service.ts'), 'utf8');
  assert.ok(source.includes('ABCDEFGHIJKLMOPQRSTUVWXYZ'));
  assert.ok(source.includes('abcdefghijklmopqrstuvwxyz'));
});
check('svg-custom-text-interpolated-as-markup', () => {
  const source = fs.readFileSync(path.join(root, 'src/tools/svg-placeholder-generator/svg-placeholder-generator.vue'), 'utf8');
  // Extract and evaluate only the upstream computed() body; no Vue/browser APIs.
  const body = source.split('const svgString = computed(() => {')[1].split('\n});')[0];
  const context = { width:{value:600}, height:{value:350}, fontSize:{value:26}, bgColor:{value:'#ccc'}, fgColor:{value:'#333'}, useExactSize:{value:true}, customText:{value:'</text><rect id="audit-marker" width="1" height="1"/><text>'} };
  const svg = vm.runInNewContext(`(function(){${body}})()`, context, { timeout:500 });
  assert.ok(svg.includes('<rect id="audit-marker"'));
});
console.log(JSON.stringify({ upstream:'d505845f918e946ec300af7b36efc107e2f66e9e', node:process.version, synthetic_only:true, results:rows }, null, 2));
