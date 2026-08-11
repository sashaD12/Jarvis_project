const API_BASE = '';

export interface PowerState {
  enabled: boolean;
}

export interface ProcessResponse {
  results: Array<{ message: string; ok: boolean }>;
  status: string[];
}

export interface CipherState {
  keyplus: number;
  keyminus: number | null;
  alfabet: string;
  b: number;
}

export interface NewsResponse {
  text: string;
}

export interface MapMarker {
  id: string;
  lat: number;
  lon: number;
  text: string;
}

export interface Viewport {
  lat: number;
  lon: number;
  zoom: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) {
        detail = data.detail;
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function getPower(): Promise<PowerState> {
  return request<PowerState>('/api/jarvis/power');
}

export function setPower(enabled: boolean): Promise<PowerState> {
  return request<PowerState>('/api/jarvis/power', {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  });
}

export function processJarvis(text: string, execute = true): Promise<ProcessResponse> {
  return request<ProcessResponse>('/api/jarvis/process', {
    method: 'POST',
    body: JSON.stringify({ text, execute }),
  });
}

export function getCipherState(): Promise<CipherState> {
  return request<CipherState>('/api/cipher/state');
}

export function adjustCipherKey(delta: 1 | -1): Promise<CipherState> {
  return request<CipherState>('/api/cipher/key', {
    method: 'POST',
    body: JSON.stringify({ delta }),
  });
}

export function processCipher(text: string, mode: 'encode' | 'decode'): Promise<{ result: string }> {
  return request<{ result: string }>('/api/cipher/process', {
    method: 'POST',
    body: JSON.stringify({ text, mode }),
  });
}

export function recoverCipher(numbers: number[]): Promise<{ result: string }> {
  return request<{ result: string }>('/api/cipher/recover', {
    method: 'POST',
    body: JSON.stringify({ numbers }),
  });
}

export function getNews(): Promise<NewsResponse> {
  return request<NewsResponse>('/api/news');
}

export function getMarkers(): Promise<{ markers: MapMarker[] }> {
  return request<{ markers: MapMarker[] }>('/api/map/markers');
}

export function createMarker(lat: number, lon: number, text: string): Promise<{ marker: MapMarker }> {
  return request<{ marker: MapMarker }>('/api/map/markers', {
    method: 'POST',
    body: JSON.stringify({ lat, lon, text }),
  });
}

export function updateMarker(id: string, text: string): Promise<{ marker: MapMarker }> {
  return request<{ marker: MapMarker }>(`/api/map/markers/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ text }),
  });
}

export function deleteMarker(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/api/map/markers/${id}`, {
    method: 'DELETE',
  });
}

export function getViewport(): Promise<Viewport> {
  return request<Viewport>('/api/map/viewport');
}

export function putViewport(viewport: Viewport): Promise<Viewport> {
  return request<Viewport>('/api/map/viewport', {
    method: 'PUT',
    body: JSON.stringify(viewport),
  });
}

export function cleanMapData(): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>('/api/map/data', {
    method: 'DELETE',
  });
}

export function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>('/api/health');
}
