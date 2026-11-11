import { useState, useEffect } from 'react';
import { Header } from './Header';
import { KpiCards } from './KpiCards';
import { RoomGrid } from './RoomGrid';
import { fetchScenarios, fetchSnapshot, type CampusSnapshot, type ScenarioOption } from './api';

export function App() {
  const [scenarios, setScenarios] = useState<ScenarioOption[]>([]);
  const [scenario, setScenario] = useState('');
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [catalogRetry, setCatalogRetry] = useState(0);
  const [data, setData] = useState<CampusSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setCatalogError(null);
    fetchScenarios(controller.signal)
      .then((options) => {
        if (controller.signal.aborted) return;
        setScenarios(options);
        setScenario((current) => options.some(({ id }) => id === current) ? current : options[0].id);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setCatalogError(err instanceof Error ? err.message : 'Scenario catalog unavailable.');
        }
      });
    return () => controller.abort();
  }, [catalogRetry]);

  useEffect(() => {
    if (!scenario) return;
    const controller = new AbortController();
    setLoading(true);
    setData(null);
    setError(null);
    fetchSnapshot(scenario, controller.signal)
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
      <Header scenarios={scenarios} scenario={scenario} setScenario={setScenario} />
      <p>Simulation only. All energy savings are estimated potential savings, not measured savings.</p>
      <p>Recommendations are advisory only. No equipment control.</p>

      {scenarios.length === 0 && !catalogError && (
        <p role="status" style={{ color: '#38bdf8' }}>Loading scenarios...</p>
      )}
      {catalogError && (
        <div role="alert">
          <p>Unable to load scenarios: {catalogError}</p>
          <button type="button" onClick={() => setCatalogRetry((value) => value + 1)}>Retry scenarios</button>
        </div>
      )}
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
