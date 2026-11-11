export interface ScenarioOption {
  id: string;
  name: string;
  description: string;
}

export interface RoomData {
  roomId: string;
  occupancy: number | null;
  sensorStatus: 'fresh' | 'stale' | 'missing';
  classInSession: boolean;
  minutesToNextClass: number | null;
  devices: { acOn: boolean; lightsOn: boolean };
  analysis: {
    status: 'normal' | 'review' | 'unknown';
    recommendationCode: string;
    potentialSavingsKwh: number;
  };
}

export interface CampusSummary {
  roomsMonitored: number;
  roomsNeedingReview: number;
  potentialSavingsKwh: number;
  potentialSavingsMyr: number;
}

export interface CampusSnapshot {
  apiVersion: '1.0';
  scenarioId: string;
  dataSource: 'simulation';
  snapshotAt: string;
  analysisWindowMinutes: number;
  tariffMyrPerKwh: number;
  summary: CampusSummary;
  rooms: RoomData[];
  ai: { status: 'not_connected'; explanation: null };
}

// All requests use Vite's existing /api proxy. Never fall back to fixture data.
async function fetchJson(
  path: string,
  signal?: AbortSignal,
  request: typeof fetch = fetch,
): Promise<unknown> {
  const response = await request(path, { signal });
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
  return payload;
}

export async function fetchSnapshot<T = CampusSnapshot>(
  scenario: string,
  signal?: AbortSignal,
  request?: typeof fetch,
): Promise<T> {
  return await fetchJson(`/api/v1/snapshot?scenario=${encodeURIComponent(scenario)}`, signal, request) as T;
}

function isScenarioOption(value: unknown): value is ScenarioOption {
  return typeof value === 'object' && value !== null
    && 'id' in value && typeof value.id === 'string' && value.id.trim().length > 0
    && 'name' in value && typeof value.name === 'string' && value.name.trim().length > 0
    && 'description' in value && typeof value.description === 'string';
}

export async function fetchScenarios(signal?: AbortSignal, request?: typeof fetch): Promise<ScenarioOption[]> {
  const catalog = await fetchJson('/api/v1/scenarios', signal, request);
  if (typeof catalog !== 'object' || catalog === null
    || !('apiVersion' in catalog) || catalog.apiVersion !== '1.0'
    || !('dataSource' in catalog) || catalog.dataSource !== 'simulation'
    || !('scenarios' in catalog) || !Array.isArray(catalog.scenarios)
    || catalog.scenarios.length === 0 || !catalog.scenarios.every(isScenarioOption)
    || new Set(catalog.scenarios.map(({ id }) => id)).size !== catalog.scenarios.length) {
    throw new Error('The API returned an invalid scenario catalog.');
  }
  return catalog.scenarios;
}
