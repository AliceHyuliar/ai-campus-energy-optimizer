import { useState, useEffect } from 'react';
import { Header } from './Header';
import { KpiCards } from './KpiCards';
import { RoomGrid } from './RoomGrid';
import { fetchSnapshot } from './api';

interface Room {
  roomId: string;
  occupancy: number | null;
  sensorStatus: string;
  classInSession: boolean;
  minutesToNextClass: number | null;
  devices: {
    acOn: boolean;
    lightsOn: boolean;
  };
  analysis: {
    status: string;
    recommendationCode: string;
    potentialSavingsKwh: number;
  };
}

interface SnapshotData {
  scenarioId: string;
  dataSource: 'simulation';
  analysisWindowMinutes: number;
  ai: { status: 'not_connected'; explanation: null };
  summary: {
    roomsMonitored: number;
    roomsNeedingReview: number;
    potentialSavingsKwh: number;
    potentialSavingsMyr: number;
  };
  rooms: Room[];
}

export function App() {
  const [scenario, setScenario] = useState<string>('idle-room');
  const [data, setData] = useState<SnapshotData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setData(null);
    setError(null);
    fetchSnapshot<SnapshotData>(scenario, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Unable to load simulation data.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [scenario, retry]);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', backgroundColor: '#0f172a', color: '#f8fafc', minHeight: '100vh' }}>
      <Header scenario={scenario} setScenario={setScenario} />
      <p>Simulation only. All energy savings are estimated potential savings, not measured savings.</p>
      <p>Recommendations are advisory only. No equipment control.</p>

      {loading && <p role="status" style={{ color: '#38bdf8' }}>Loading metrics...</p>}
      {error && (
        <div role="alert">
          <p>Unable to load simulation data: {error}</p>
          <button type="button" onClick={() => setRetry((value) => value + 1)}>Retry</button>
        </div>
      )}

      {!loading && !error && data && data.scenarioId === scenario && (
        <>
          <p>Data source: {data.dataSource} · Analysis window: {data.analysisWindowMinutes} minutes</p>
          <p>AI status: {data.ai.status}. Gemini Enterprise access is pending.</p>
          <KpiCards summary={data.summary} />
          <RoomGrid rooms={data.rooms} />
        </>
      )}
    </div>
  );
}

export default App;
