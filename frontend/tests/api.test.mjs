import assert from 'node:assert/strict';
import test from 'node:test';
import { fetchSnapshot } from '../src/api.ts';

test('scenario value is expanded and safely encoded into the proxy URL', async () => {
  let requestedUrl;
  const snapshot = { scenarioId: 'idle-room', rooms: [] };
  const request = async (url) => {
    requestedUrl = url;
    return Response.json(snapshot);
  };
  assert.deepEqual(await fetchSnapshot('idle-room', undefined, request), snapshot);
  assert.equal(requestedUrl, '/api/v1/snapshot?scenario=idle-room');
  await fetchSnapshot('unknown & id', undefined, request);
  assert.equal(requestedUrl, '/api/v1/snapshot?scenario=unknown%20%26%20id');
});

test('HTTP 404 envelope becomes a visible error instead of snapshot data', async () => {
  const request = async () => Response.json({ error: {
    code: 'UNKNOWN_SCENARIO', message: 'Unknown scenario. See /api/v1/scenarios.',
  } }, { status: 404 });
  await assert.rejects(fetchSnapshot('unknown', undefined, request), /HTTP 404: Unknown scenario/);
});

test('HTTP 500 without an envelope uses the safe error fallback', async () => {
  await assert.rejects(fetchSnapshot('idle-room', undefined,
    async () => Response.json({}, { status: 500 })), /HTTP 500: Request failed/);
});

test('an unavailable Vite proxy returning non-JSON produces a readable error', async () => {
  await assert.rejects(fetchSnapshot('idle-room', undefined,
    async () => new Response('', { status: 502 })), /HTTP 502.*backend is running/);
});

test('network failures are propagated rather than replaced with fixture data', async () => {
  await assert.rejects(fetchSnapshot('idle-room', undefined,
    async () => { throw new TypeError('Failed to fetch'); }), /Failed to fetch/);
});

test('abort signal is passed through so stale scenario requests can be cancelled', async () => {
  const controller = new AbortController();
  const request = async (_url, options) => {
    assert.equal(options.signal, controller.signal);
    controller.abort();
    options.signal.throwIfAborted();
  };
  await assert.rejects(fetchSnapshot('idle-room', controller.signal, request), { name: 'AbortError' });
});

test('null occupancy and disconnected AI are returned without coercion', async () => {
  const snapshot = { rooms: [{ occupancy: null }], ai: { status: 'not_connected', explanation: null } };
  const result = await fetchSnapshot('stale-sensor', undefined, async () => Response.json(snapshot));
  assert.equal(result.rooms[0].occupancy, null);
  assert.deepEqual(result.ai, snapshot.ai);
});
