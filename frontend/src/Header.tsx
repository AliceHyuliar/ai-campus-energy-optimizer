interface HeaderProps {
  scenario: string;
  setScenario: (scenario: string) => void;
}

export function Header({ scenario, setScenario }: HeaderProps) {
  return (
    <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid #334155', paddingBottom: '16px' }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '24px', color: '#38bdf8' }}>⚡ AI Campus Energy Optimizer</h1>
        <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '14px' }}>Hackathon 2026 - Frontend Dashboard</p>
      </div>

      <div>
        <label htmlFor="scenario" style={{ marginRight: '10px', fontWeight: 'bold' }}>Scenario: </label>
        <select 
          id="scenario"
          value={scenario} 
          onChange={(e) => setScenario(e.target.value)}
          style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #475569', backgroundColor: '#1e293b', color: '#fff', fontSize: '14px', cursor: 'pointer' }}
        >
          <option value="idle-room">Idle Room (Energy Waste)</option>
          <option value="occupied-room">Occupied Room (Normal)</option>
          <option value="class-soon">Class Soon (Upcoming)</option>
          <option value="stale-sensor">Stale Sensor (Unknown State)</option>
        </select>
      </div>
    </header>
  );
}
