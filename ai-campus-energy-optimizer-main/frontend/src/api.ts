// frontend/src/api.ts

export interface DeviceStatus {
  acOn: boolean;
  lightsOn: boolean;
}

export interface RoomAnalysis {
  status: 'normal' | 'review' | 'unknown';
  recommendationCode: string;
  potentialSavingsKwh: number;
}

export interface RoomData {
  roomId: string;
  occupancy: number | null;
  sensorStatus: 'fresh' | 'stale';
  classInSession: boolean;
  minutesToNextClass: number | null;
  devices: DeviceStatus;
  analysis: RoomAnalysis;
}

export interface CampusSummary {
  roomsMonitored: number;
  roomsNeedingReview: number;
  potentialSavingsKwh: number;
  potentialSavingsMyr: number;
}

export interface AiStatus {
  status: string;
  explanation: string | null;
}

export interface CampusSnapshot {
  apiVersion: string;
  scenarioId: string;
  dataSource: string;
  snapshotAt: string;
  analysisWindowMinutes: number;
  tariffMyrPerKwh: number;
  summary: CampusSummary;
  rooms: RoomData[];
  ai: AiStatus;
}

export async function fetchCampusSnapshot(scenarioId: string = 'campus-overview'): Promise<CampusSnapshot> {
  const activeId = scenarioId;
  const response = await fetch('/api/v1/snapshot?scenario=' + activeId);

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  return response.json();
}