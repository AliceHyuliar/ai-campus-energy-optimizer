interface SummaryData {
  roomsMonitored: number;
  roomsNeedingReview: number;
  potentialSavingsKwh: number;
  potentialSavingsMyr: number;
}

interface KpiCardsProps {
  summary: SummaryData;
}

export function KpiCards({ summary }: KpiCardsProps) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
      <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}>
        <span style={{ fontSize: '12px', color: '#94a3b8' }}>Rooms Monitored</span>
        <h2 style={{ margin: '8px 0 0 0', fontSize: '28px' }}>{summary.roomsMonitored}</h2>
      </div>
      <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #f59e0b' }}>
        <span style={{ fontSize: '12px', color: '#94a3b8' }}>Rooms Needing Review</span>
        <h2 style={{ margin: '8px 0 0 0', fontSize: '28px', color: '#f59e0b' }}>{summary.roomsNeedingReview}</h2>
      </div>
      <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #10b981' }}>
        <span style={{ fontSize: '12px', color: '#94a3b8' }}>Estimated Potential Savings (kWh)</span>
        <h2 style={{ margin: '8px 0 0 0', fontSize: '28px', color: '#10b981' }}>{summary.potentialSavingsKwh} kWh</h2>
      </div>
      <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #10b981' }}>
        <span style={{ fontSize: '12px', color: '#94a3b8' }}>Estimated Potential Savings (MYR)</span>
        <h2 style={{ margin: '8px 0 0 0', fontSize: '28px', color: '#10b981' }}>MYR {summary.potentialSavingsMyr.toFixed(2)}</h2>
      </div>
    </div>
  );
}
