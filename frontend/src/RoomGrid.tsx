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

interface RoomGridProps {
  rooms: Room[];
}

export function RoomGrid({ rooms }: RoomGridProps) {
  return (
    <>
      <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Room Status Overview</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {rooms.map((room) => (
          <div key={room.roomId} style={{ backgroundColor: '#1e293b', padding: '20px', borderRadius: '10px', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ margin: 0, fontSize: '20px', color: '#f8fafc' }}>Room: {room.roomId}</h3>
              <span style={{ 
                padding: '4px 10px', 
                borderRadius: '20px', 
                fontSize: '12px', 
                fontWeight: 'bold',
                backgroundColor: room.analysis.status === 'review' ? '#ef4444' : room.analysis.status === 'unknown' ? '#92400e' : '#10b981',
                color: '#fff' 
              }}>
                {room.analysis.status.toUpperCase()}
              </span>
            </div>

            <p style={{ margin: '8px 0', fontSize: '14px', color: room.occupancy === null ? '#f59e0b' : '#cbd5e1' }}>
              <strong>Occupancy:</strong> {room.occupancy === null ? 'Unknown' : room.occupancy + ' People'}
            </p>
            <p><strong>Sensor status:</strong> {room.sensorStatus}</p>
            {room.sensorStatus !== 'fresh' && (
              <p role="status" style={{ color: '#fbbf24' }}>Warning: {room.sensorStatus} sensor data. Occupancy is unknown.</p>
            )}
            <p><strong>Class in session:</strong> {room.classInSession ? 'Yes' : 'No'}</p>
            <p><strong>Next class:</strong> {room.minutesToNextClass === null ? 'Unknown' : `${room.minutesToNextClass} minutes`}</p>

            <p style={{ margin: '8px 0', fontSize: '14px', color: '#cbd5e1' }}>
              <strong>Air Conditioner:</strong> {room.devices.acOn ? '🟢 ON' : '🔴 OFF'}
            </p>
            <p style={{ margin: '8px 0', fontSize: '14px', color: '#cbd5e1' }}>
              <strong>Lighting:</strong> {room.devices.lightsOn ? '🟢 ON' : '🔴 OFF'}
            </p>
            <p style={{ margin: '8px 0', fontSize: '14px', color: '#cbd5e1' }}>
              <strong>Recommendation Code:</strong> <code style={{ backgroundColor: '#0f172a', padding: '2px 6px', borderRadius: '4px', color: '#38bdf8' }}>{room.analysis.recommendationCode}</code>
            </p>
          </div>
        ))}
      </div>
    </>
  );
}
