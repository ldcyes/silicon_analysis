#!/usr/bin/env node
// Reproduce paper experiments using the trusted repository's actual model.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const paperDir = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(resolve(paperDir, '../index.html'), 'utf8');
const elements = new Map();
const attrs = text => Object.fromEntries(
  [...text.matchAll(/([\w-]+)="([^"]*)"/g)].map(m => [m[1], m[2]])
);
for (const match of html.matchAll(/<input\b([^>]*)>/g)) {
  const a = attrs(match[1]);
  if (a.id) elements.set(a.id, { value: a.value ?? '', checked: /\bchecked\b/.test(match[1]) });
}
for (const match of html.matchAll(/<select\b([^>]*)>([\s\S]*?)<\/select>/g)) {
  const a = attrs(match[1]);
  const options = [...match[2].matchAll(/<option\b([^>]*)>/g)];
  const selected = options.find(m => /\bselected\b/.test(m[1])) ?? options[0];
  if (a.id) elements.set(a.id, { value: selected ? attrs(selected[1]).value : '' });
}
const context = vm.createContext({ document: { getElementById: id => elements.get(id) ?? null } });
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1, 'Expected the single embedded application script');
const bootstrap = 'initSelects(); initTrendFoundryFilters(); bind(); updateDataTable(); update();';
assert.equal(scripts[0][1].split(bootstrap).length, 2, 'Application bootstrap changed; review extraction');
vm.runInContext(scripts[0][1].replace(bootstrap, '') + `
  initSelects();
  globalThis.model = { DATA, FOUND_ORD, availableNodes, getInput, calc, grossDies,
    calcWaferMap, syncWaferFromTarget, seededRand };
`, context, { filename: 'index.html' });
const { DATA, FOUND_ORD, availableNodes, getInput, calc, grossDies, calcWaferMap } = context.model;
const baseline = { ...getInput() };
const fields = ['logicArea', 'sramArea', 'totalArea', 'freq', 'powerSame', 'powerConv',
  'gd', 'd0', 'dieYield', 'baseYield', 'finalYield', 'waferUnitCost', 'waferMult',
  'yieldStacks', 'dieMfgCost', 'cost'];
const compact = r => Object.fromEntries([
  ['foundry', r.foundry], ['node', r.node], ['label', r.info.label], ['confidence', r.info.conf],
  ...fields.map(k => [k, r[k]])
]);
const run = (foundry, node, changes = {}) => calc(foundry, node, { ...baseline, ...changes });
const coverage = FOUND_ORD.map(foundry => ({
  foundry, nodes: [...availableNodes(foundry)],
  confidence: Object.fromEntries(['high', 'medium', 'roadmap'].map(c =>
    [c, availableNodes(foundry).filter(n => DATA[foundry][n].conf === c).length]))
}));
const sweep = availableNodes('TSMC').map(n => compact(run('TSMC', n)));
const mixed = availableNodes('TSMC').map(n => compact(run('TSMC', n, {
  sramMbit: 256, sramPower: 2, otherArea: 40
})));
const sensitivity = [];
for (const [parameter, values] of Object.entries({
  d0Mult: [0.5, 1, 2], costMult: [0.5, 1, 2], areaOverhead: [0.8, 1, 1.2],
  freqRealization: [0.8, 1, 1.2], powerGuard: [0.8, 1, 1.2]
})) for (const value of values) sensitivity.push({ parameter, value, ...compact(run('TSMC', 6, { [parameter]: value })) });
const costBases = ['intro', 'mfg'].map(costBasis => ({ costBasis, ...compact(run('TSMC', 6, { costBasis })) }));
const stacks = [2, 3].map(taoStackLayers => compact(run('Huawei τ', 6, { taoStackLayers })));
const mapFields = ['dieW', 'dieH', 'waferDia', 'edge', 'd0', 'alpha', 'lineYield', 'ppm',
  'bondYield', 'waferUnitCost', 'edgeBoost', 'seed', 'yieldStacks', 'total', 'good', 'bad',
  'expYield', 'simYield', 'expectedCost', 'simCost'];
const mapCases = [];
function recordMap(name, inp, r) {
  const m = calcWaferMap(inp, r);
  mapCases.push({ name, ...Object.fromEntries(mapFields.map(k => [k, m[k]])) });
  return m;
}
const target = run('TSMC', 6);
recordMap('initial independent controls', baseline, target);
// Match the exact formatting performed by syncWaferFromTarget, without rendering.
function syncMap(r) {
  const values = {
    mapDieW: Math.sqrt(Math.max(r.totalArea, 0.01)).toFixed(2),
    mapDieH: Math.sqrt(Math.max(r.totalArea, 0.01)).toFixed(2),
    mapWaferDia: baseline.waferDiameter, mapD0: r.d0.toFixed(3),
    mapAlpha: baseline.alpha.toFixed(2), mapLineYield: (baseline.lineYield * 100).toFixed(1),
    mapWaferCost: r.waferUnitCost.toFixed(0),
    mapBondYield: ((r.bondYield || baseline.taoBondYield) * 100).toFixed(2),
    mapStackLayers: r.yieldStacks > 1 ? r.yieldStacks : baseline.taoStackLayers
  };
  for (const [id, value] of Object.entries(values)) elements.get(id).value = String(value);
}
syncMap(target);
const synced = recordMap('target synchronized', baseline, target);
elements.get('mapEdgeBoost').value = '0';
elements.get('mapPpm').value = '0';
recordMap('synchronized; no radial boost or PPM', baseline, target);
elements.get('mapEdgeBoost').value = '0.6';
elements.get('mapPpm').value = '1000';
const seedSamples = [];
for (let seed = 1; seed <= 100; seed++) {
  elements.get('mapSeed').value = String(seed);
  seedSamples.push(calcWaferMap(baseline, target).simYield);
}
elements.get('mapSeed').value = '2026';
for (const layers of [2, 3]) {
  const inp = { ...baseline, taoStackLayers: layers };
  const r = calc('Huawei τ', 6, inp);
  syncMap(r);
  recordMap(`Huawei roadmap; ${layers} layers`, inp, r);
}

// Scientific consistency checks: these establish arithmetic behavior, not silicon accuracy.
let pairs = 0;
for (const sf of FOUND_ORD) for (const sn of availableNodes(sf)) {
  const inp = { ...baseline, currentFoundry: sf, currentNode: sn };
  const identity = calc(sf, sn, inp);
  assert.ok(Math.abs(identity.logicArea - inp.logicArea) < 1e-9);
  assert.ok(Math.abs(identity.freq - inp.frequency) < 1e-9);
  assert.ok(Math.abs(identity.powerConv - inp.logicPower) < 1e-9);
  for (const tf of FOUND_ORD) for (const tn of availableNodes(tf)) {
    const r = calc(tf, tn, inp);
    for (const k of fields) assert.ok(Number.isFinite(r[k]), `${sf}/${sn} -> ${tf}/${tn}: ${k}`);
    assert.ok(r.finalYield >= 0 && r.finalYield <= 1);
    pairs++;
  }
}
assert.equal(grossDies(0, 300), 0);
assert.equal(grossDies(100000, 300), 0);
assert.ok(run('TSMC', 6, { d0Mult: 2 }).cost > target.cost);
assert.ok(run('TSMC', 6, { areaOverhead: 1.2 }).cost > target.cost);
assert.ok(Math.abs(stacks[1].dieMfgCost / stacks[0].dieMfgCost -
  1.5 / (stacks[0].baseYield * baseline.taoBondYield)) < 1e-10);
syncMap(target);
const repeated = calcWaferMap(baseline, target);
assert.equal(repeated.good, synced.good);
assert.equal(repeated.expYield, synced.expYield);
assert.ok(repeated.dies.every(d => Math.abs(d.x) + repeated.dieW / 2 <= repeated.R));
elements.get('mapDieW').value = '1000';
elements.get('mapDieH').value = '1000';
const empty = calcWaferMap(baseline, target);
assert.equal(empty.total, 0);
assert.equal(empty.expectedCost, Infinity);
const mean = seedSamples.reduce((a, b) => a + b, 0) / seedSamples.length;
const sd = Math.sqrt(seedSamples.reduce((a, b) => a + (b - mean) ** 2, 0) / (seedSamples.length - 1));
const output = {
  provenance: { file: 'index.html', sha256: createHash('sha256').update(html).digest('hex'),
    method: 'Actual embedded JavaScript, Node VM, HTML input defaults; rendering suppressed', node: process.version },
  baseline, coverage, sweep, mixed, sensitivity, costBases, stacks, mapCases,
  seedSummary: { seeds: '1..100', count: seedSamples.length, mean, sd, min: Math.min(...seedSamples), max: Math.max(...seedSamples), expected: synced.expYield },
  checks: { sourceTargetPairs: pairs, identityCases: coverage.reduce((s, r) => s + r.nodes.length, 0), status: 'passed' }
};
mkdirSync(resolve(paperDir, 'results'), { recursive: true });
writeFileSync(resolve(paperDir, 'results/experiments.json'), JSON.stringify(output, null, 2) + '\n');
console.log(JSON.stringify({ checks: output.checks, defaultTarget: compact(target), costBases, stacks,
  mapCases, seedSummary: output.seedSummary }, null, 2));
