// All requests use Vite's existing /api proxy. Never fall back to fixture data.
export async function fetchSnapshot<T>(
  scenario: string,
  signal?: AbortSignal,
  request: typeof fetch = fetch,
): Promise<T> {
  const response = await request(
    `/api/v1/snapshot?scenario=${encodeURIComponent(scenario)}`,
    { signal },
  );
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`API returned an unreadable response (HTTP ${response.status}). Check that the backend is running.`);
  }
  if (!response.ok) {
    const message = typeof payload === 'object' && payload !== null && 'error' in payload
      && typeof payload.error === 'object' && payload.error !== null && 'message' in payload.error
      && typeof payload.error.message === 'string'
      ? payload.error.message : 'Request failed.';
    throw new Error(`HTTP ${response.status}: ${message}`);
  }
  return payload as T;
}
