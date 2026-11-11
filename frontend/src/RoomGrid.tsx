import type { RoomData } from './api';

interface RoomGridProps {
  rooms: RoomData[];
}

export function RoomGrid({ rooms }: RoomGridProps) {
  return (
    <>
      <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Room Status Overview</h2>
      <div className="room-grid">
        {rooms.map((room) => (
          <article key={room.roomId} aria-label={`Room ${room.roomId}`} className="room-card" data-status={room.analysis.status}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ margin: 0, fontSize: '20px', color: '#f8fafc' }}>Room: {room.roomId}</h3>
              <span className="room-status">
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
            <p><strong>Estimated potential savings:</strong> {room.analysis.potentialSavingsKwh} kWh</p>
          </article>
        ))}
      </div>
    </>
  );
}
