import { useState, useEffect } from 'react';
import { Header } from './Header';
import { KpiCards } from './KpiCards';
import { RoomGrid } from './RoomGrid';

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

  useEffect(() => {
    setLoading(true);
    // @ts-ignore
    fetch('/api/v1/snapshot?scenario=${scenario}')
      .then((res: any) => res.json())
      .then((result: any) => {
        setData(result);
        setLoading(false);
      })
      .catch((err: any) => {
        console.error('Failed to fetch:', err);
        setLoading(false);
      });
  }, [scenario]);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', backgroundColor: '#0f172a', color: '#f8fafc', minHeight: '100vh' }}>
      <Header scenario={scenario} setScenario={setScenario} />

      {loading && <p style={{ color: '#38bdf8' }}>Loading metrics...</p>}

      {data && (
        <>
          <KpiCards summary={data.summary} />
          <RoomGrid rooms={data.rooms} />
        </>
      )}
    </div>
  );
}

export default App;