import fs from 'node:fs';
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { test } from 'node:test';
import assert from 'node:assert/strict';
function load(name, symbol) {
  const source = stripTypeScriptTypes(fs.readFileSync(new URL(`./upstream-candidates/${name}`, import.meta.url), 'utf8').replace(/^export\s*\{[^}]+\};?/gm, '').replace(/export function/g,'function'), {mode:'strip'});
  return vm.runInNewContext(`(function(){${source};return ${symbol};})()`);
}
const csv = load('csv.service.ts', 'convertArrayToCsv');
const regex = load('regex.service.ts', 'matchRegex');
test('CSV header with comma is one quoted column', () => assert.equal(csv({array:[{'a,b':'value'}]}), '"a,b"\nvalue'));
test('CSV quotes are doubled and cells quoted', () => assert.equal(csv({array:[{a:'hello "world", test'}]}), 'a\n"hello ""world"", test"'));
test('CSV newline is preserved inside quotes', () => assert.equal(csv({array:[{a:'line1\nline2'}]}), 'a\n"line1\nline2"'));
test('CSV null and missing preserve original contract', () => assert.equal(csv({array:[{a:null,b:undefined}]}), 'a,b\nnull,'));
test('CSV heterogeneous rows retain all headers', () => assert.equal(csv({array:[{a:1},{b:2}]}), 'a,b\n1,\n,2'));
test('optional unmatched regex groups do not discard valid match', () => {const matches=regex('(?<a>a)?b','b','dg');assert.equal(matches.length,1);assert.equal(matches[0].value,'b');assert.equal(matches[0].groups.length,0);assert.equal(matches[0].captures.length,0);});
test('matched named capture keeps indices', () => {const matches=regex('(?<a>a)?b','ab','dg');assert.equal(matches[0].groups[0].start,0);assert.equal(matches[0].groups[0].end,1);});
test('helper adds indices flag when missing', () => {assert.equal(regex('(a)','a','g')[0].captures[0].value,'a');});
test('ungrouped regex remains correct', () => {assert.equal(regex('a','aba','g').length,2);});
