import { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';
import idleRoom from '../../contracts/examples/idle-room.json';
import occupiedRoom from '../../contracts/examples/occupied-room.json';
import classSoon from '../../contracts/examples/class-soon.json';
import staleSensor from '../../contracts/examples/stale-sensor.json';
import './style.css';

// Read the actual shared fixtures. Do not maintain a separate copy of API data.
const examples = {
  'idle-room': idleRoom,
  'occupied-room': occupiedRoom,
  'class-soon': classSoon,
  'stale-sensor': staleSensor,
};
type ScenarioId = keyof typeof examples;

function App() {
  const [scenario, setScenario] = useState<ScenarioId>('idle-room');
  const snapshot = examples[scenario];
  return (
    <main>
      <p className="label">Simulation only · Common foundation</p>
      <h1>Campus Energy Optimizer</h1>
      <p>Preview the shared contract examples without running the backend.</p>
      <label htmlFor="scenario">Simulation scenario</label>
      <select id="scenario" value={scenario} onChange={(event) => {
        const value = event.currentTarget.value;
        if (value in examples) setScenario(value as ScenarioId);
      }}>
        {Object.keys(examples).map((id) => <option key={id} value={id}>{id}</option>)}
      </select>
      <p role="status">
        Estimated potential savings: {snapshot.summary.potentialSavingsKwh} kWh
        {' / MYR '}{snapshot.summary.potentialSavingsMyr.toFixed(2)} over{' '}
        {snapshot.analysisWindowMinutes} minutes. These are simulated estimates.
      </p>
      <p>AI: not connected. Gemini Enterprise access is pending.</p>
      <details open>
        <summary>Shared snapshot JSON</summary>
        <pre>{JSON.stringify(snapshot, null, 2)}</pre>
      </details>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
