import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { after, test } from 'node:test';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

const vite = await createServer({ configFile: false, server: { middlewareMode: true, watch: null, ws: false } });
after(() => vite.close());

test('scenario picker renders the API-provided labels and keeps the selected ID', async () => {
  const { Header } = await vite.ssrLoadModule('/src/Header.tsx');
  const scenarios = [
    { id: 'another-id', name: 'Another simulation', description: '' },
    { id: 'campus-overview', name: 'Campus overview', description: 'Four classrooms.' },
  ];
  const html = renderToStaticMarkup(createElement(Header, { scenarios, scenario: 'campus-overview' }));
  assert.match(html, /<option value="another-id">Another simulation<\/option>/);
  assert.match(html, /<option value="campus-overview" selected="">Campus overview<\/option>/);
  assert.equal((html.match(/<option /g) ?? []).length, scenarios.length);
});

test('campus dashboard displays every room and the backend aggregate', async () => {
  const [{ RoomGrid }, { KpiCards }] = await Promise.all([
    vite.ssrLoadModule('/src/RoomGrid.tsx'), vite.ssrLoadModule('/src/KpiCards.tsx'),
  ]);
  const snapshot = JSON.parse(await readFile(new URL('../../contracts/examples/campus-overview.json', import.meta.url), 'utf8'));
  const rooms = renderToStaticMarkup(createElement(RoomGrid, { rooms: snapshot.rooms }));
  const cards = Array.from(rooms.matchAll(/<article aria-label="Room (A10[1-4])"[^>]*>(.*?)<\/article>/gs));
  assert.deepEqual(cards.map(([, id]) => id), ['A101', 'A102', 'A103', 'A104']);
  for (const [index, [, , card]] of cards.entries()) {
    const room = snapshot.rooms[index];
    assert.ok(card.includes(`${room.analysis.recommendationCode}</code>`));
    assert.ok(card.includes(`<strong>Estimated potential savings:</strong> ${room.analysis.potentialSavingsKwh} kWh`));
  }
  assert.match(cards[3][2], /<strong>Occupancy:<\/strong> Unknown/);
  assert.match(cards[3][2], /<strong>Sensor status:<\/strong> stale/);

  const summary = renderToStaticMarkup(createElement(KpiCards, { summary: snapshot.summary }));
  assert.deepEqual(Array.from(summary.matchAll(/<h2[^>]*>(.*?)<\/h2>/g), ([, value]) => value),
    ['4', '2', '2.2 kWh', 'MYR 1.10']);
});
