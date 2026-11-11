// frontend/src/RoomGrid.tsx
import React from 'react';

interface RoomGridProps {
  rooms: any[];
}

export const RoomGrid: React.FC<RoomGridProps> = ({ rooms }) => {
  if (!rooms || rooms.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>No classroom data available.</div>;
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem', padding: '1rem 0' }}>
      {rooms.map((room) => {
        const needsReview = room.analysis?.status === 'review';
        const isUnknown = room.analysis?.status === 'unknown';
        const borderColor = needsReview ? '#f59e0b' : isUnknown ? '#ef4444' : '#10b981';
        
        const badgeBg = needsReview ? '#fef3c7' : isUnknown ? '#fee2e2' : '#d1fae5';
        const badgeColor = needsReview ? '#92400e' : isUnknown ? '#991b1b' : '#065f46';

        return (
          <div
            key={room.roomId}
            style={{
              border: `2px solid ${borderColor}`,
              borderRadius: '10px',
              padding: '1.25rem',
              backgroundColor: '#ffffff',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 'bold', color: '#1f2937' }}>
                  Classroom {room.roomId}
                </h3>
                <span
                  style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    backgroundColor: badgeBg,
                    color: badgeColor,
                    textTransform: 'uppercase',
                  }}
                >
                  {room.analysis?.status}
                </span>
              </div>

              <div style={{ fontSize: '0.9rem', color: '#4b5563', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <div>
                  <strong>Occupancy:</strong>{' '}
                  {room.occupancy !== null && room.occupancy !== undefined ? `${room.occupancy} people` : `Unknown (Stale Sensor)`}
                </div>
                <div>
                  <strong>Sensor Status:</strong>{' '}
                  <span style={{ color: room.sensorStatus === 'fresh' ? '#059669' : '#dc2626', fontWeight: 600 }}>
                    {room.sensorStatus}
                  </span>
                </div>
                <div>
                  <strong>Class in Session:</strong> {room.classInSession ? 'Yes 🟢' : 'No 🔴'}
                </div>
                <div>
                  <strong>Next Class:</strong>{' '}
                  {room.minutesToNextClass !== null && room.minutesToNextClass !== undefined ? `in ${room.minutesToNextClass} mins` : 'N/A'}
                </div>
              </div>

              <div style={{ marginTop: '0.75rem', padding: '0.6rem', background: '#f9fafb', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.25rem', color: '#374151' }}>
                  Devices Status:
                </div>
                <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                  <span>❄️ AC: <strong>{room.devices?.acOn ? 'ON' : 'OFF'}</strong></span>
                  <span>💡 Lights: <strong>{room.devices?.lightsOn ? 'ON' : 'OFF'}</strong></span>
                </div>
              </div>
            </div>
            <div style={{ marginTop: '1rem', borderTop: '1px solid #e5e7eb', paddingTop: '0.75rem' }}>
              <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.2rem' }}>Recommendation:</div>
              <code
                style={{
                  display: 'inline-block',
                  background: '#f3f4f6',
                  color: '#1f2937',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                }}
              >
                {room.analysis?.recommendationCode}
              </code>

              {room.analysis?.potentialSavingsKwh > 0 && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#059669', fontWeight: 'bold' }}>
                  Potential Savings: {room.analysis.potentialSavingsKwh} kWh
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};