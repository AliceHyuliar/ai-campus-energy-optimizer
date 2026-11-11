import type { ScenarioOption } from './api';

interface HeaderProps {
  scenarios: ScenarioOption[];
  scenario: string;
  setScenario: (scenario: string) => void;
}

export function Header({ scenarios, scenario, setScenario }: HeaderProps) {
  return (
    <header className="dashboard-header">
      <div>
        <h1 style={{ margin: 0, fontSize: '24px', color: '#38bdf8' }}>⚡ AI Campus Energy Optimizer</h1>
        <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '14px' }}>Hackathon 2026 - Frontend Dashboard</p>
      </div>

      <div>
        <label htmlFor="scenario">Scenario:</label>
        <select
          id="scenario"
          value={scenario}
          disabled={scenarios.length === 0}
          onChange={(event) => setScenario(event.target.value)}
          style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #475569', backgroundColor: '#1e293b', color: '#fff', fontSize: '14px', cursor: 'pointer' }}
        >
          {scenarios.length === 0 && <option value="">No scenarios loaded</option>}
          {scenarios.map(({ id, name }) => <option key={id} value={id}>{name}</option>)}
        </select>
      </div>
    </header>
  );
}
