import type { FC } from 'react';
import { useCallback, useEffect, useState } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import 'leaflet/dist/leaflet.css';
import {
  cleanMapData,
  createMarker,
  deleteMarker,
  getMarkers,
  getViewport,
  putViewport,
  updateMarker,
  type MapMarker,
  type Viewport,
} from '../api/client';
import { AppShell } from '../components/AppShell';

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface MapClickHandlerProps {
  enabled: boolean;
  onAdd: (lat: number, lon: number) => void;
}

const MapClickHandler: FC<MapClickHandlerProps> = ({ enabled, onAdd }) => {
  useMapEvents({
    click(event) {
      if (!enabled) {
        return;
      }
      onAdd(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
};

interface FlyToProps {
  target: { lat: number; lon: number } | null;
}

const FlyTo: FC<FlyToProps> = ({ target }) => {
  const map = useMap();
  useEffect(() => {
    if (!target) {
      return;
    }
    map.flyTo([target.lat, target.lon], Math.max(map.getZoom(), 10), { duration: 0.8 });
  }, [target, map]);
  return null;
};

interface ViewportTrackerProps {
  onChange: (viewport: Viewport) => void;
}

const ViewportTracker: FC<ViewportTrackerProps> = ({ onChange }) => {
  const map = useMapEvents({
    moveend() {
      const center = map.getCenter();
      onChange({ lat: center.lat, lon: center.lng, zoom: map.getZoom() });
    },
    zoomend() {
      const center = map.getCenter();
      onChange({ lat: center.lat, lon: center.lng, zoom: map.getZoom() });
    },
  });
  return null;
};

export const MapPage: FC = () => {
  const [markers, setMarkers] = useState<MapMarker[]>([]);
  const [viewport, setViewport] = useState<Viewport | null>(null);
  const [adding, setAdding] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState('Status: idle');
  const [flyTarget, setFlyTarget] = useState<{ lat: number; lon: number } | null>(null);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async () => {
    const [markerData, view] = await Promise.all([getMarkers(), getViewport()]);
    setMarkers(markerData.markers);
    setViewport(view);
    setReady(true);
  }, []);

  useEffect(() => {
    void refresh().catch((err: Error) => setStatus(`Error: ${err.message}`));
  }, [refresh]);

  async function handleAdd(lat: number, lon: number) {
    const text = window.prompt('Enter description:');
    if (!text || !text.trim()) {
      setAdding(false);
      setStatus('Marker creation cancelled');
      return;
    }
    try {
      const { marker } = await createMarker(lat, lon, text.trim());
      setMarkers((prev) => [...prev, marker]);
      setStatus(`Placed marker at ${lat.toFixed(5)}, ${lon.toFixed(5)}`);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    } finally {
      setAdding(false);
    }
  }

  async function handleEdit() {
    if (!selectedId) {
      setStatus('Select a marker to edit');
      return;
    }
    const current = markers.find((m) => m.id === selectedId);
    if (!current) {
      return;
    }
    const text = window.prompt('New text:', current.text);
    if (text === null) {
      return;
    }
    try {
      const { marker } = await updateMarker(selectedId, text);
      setMarkers((prev) => prev.map((m) => (m.id === marker.id ? marker : m)));
      setStatus('Marker updated');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  }

  async function handleDelete() {
    if (!selectedId) {
      setStatus('Select a marker to delete');
      return;
    }
    if (!window.confirm('Delete selected marker?')) {
      return;
    }
    try {
      await deleteMarker(selectedId);
      setMarkers((prev) => prev.filter((m) => m.id !== selectedId));
      setSelectedId(null);
      setStatus('Marker deleted');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  }

  async function handleSave() {
    if (!viewport) {
      return;
    }
    try {
      await putViewport(viewport);
      setStatus('Saved.');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  }

  async function handleLoad() {
    try {
      await refresh();
      setStatus('Loaded markers');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  }

  async function handleClean() {
    if (!window.confirm('Delete saved map files?')) {
      return;
    }
    try {
      await cleanMapData();
      setMarkers([]);
      setViewport({ lat: 50.45, lon: 30.52, zoom: 6 });
      setStatus('Data cleared');
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    }
  }

  return (
    <AppShell title="System map">
      <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-8rem)] min-h-[420px]">
        <div className="flex-1 riat-panel overflow-hidden min-h-[280px]">
          {ready && viewport ? (
            <MapContainer
              center={[viewport.lat, viewport.lon]}
              zoom={viewport.zoom}
              className="h-full w-full"
              style={{ background: '#000010' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapClickHandler enabled={adding} onAdd={(lat, lon) => void handleAdd(lat, lon)} />
              <FlyTo target={flyTarget} />
              <ViewportTracker onChange={setViewport} />
              {markers.map((marker) => (
                <Marker
                  key={marker.id}
                  position={[marker.lat, marker.lon]}
                  eventHandlers={{
                    click: () => setSelectedId(marker.id),
                  }}
                >
                  <Popup>{marker.text}</Popup>
                </Marker>
              ))}
            </MapContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-riat-dim">Loading map...</div>
          )}
        </div>

        <aside className="w-full lg:w-64 flex flex-col gap-3">
          <div className="tracking-[0.2em] text-sm">===[ SYSTEM MAP ]===</div>
          <button
            type="button"
            className={`riat-btn ${adding ? 'border-riat-fg' : ''}`}
            onClick={() => {
              setAdding(true);
              setStatus('Click on the map to place marker');
            }}
          >
            Add marker
          </button>

          <div className="text-riat-dim text-xs uppercase tracking-widest">Markers</div>
          <ul className="riat-panel flex-1 overflow-y-auto min-h-40 p-2 space-y-1 text-sm">
            {markers.length === 0 ? (
              <li className="text-riat-dim">No markers</li>
            ) : (
              markers.map((marker, index) => (
                <li key={marker.id}>
                  <button
                    type="button"
                    className={`w-full text-left px-2 py-1 hover:bg-riat-fg/10 ${
                      selectedId === marker.id ? 'bg-riat-fg/15 border border-riat-border' : ''
                    }`}
                    onClick={() => setSelectedId(marker.id)}
                    onDoubleClick={() => setFlyTarget({ lat: marker.lat, lon: marker.lon })}
                  >
                    {index + 1}: {marker.text || `Marker #${index + 1}`}
                  </button>
                </li>
              ))
            )}
          </ul>

          <div className="flex gap-2">
            <button type="button" className="riat-btn flex-1" onClick={() => void handleEdit()}>
              Edit
            </button>
            <button type="button" className="riat-btn flex-1" onClick={() => void handleDelete()}>
              Delete
            </button>
          </div>
          <button type="button" className="riat-btn" onClick={() => void handleSave()}>
            Save
          </button>
          <button type="button" className="riat-btn" onClick={() => void handleLoad()}>
            Load
          </button>
          <button type="button" className="riat-btn riat-btn-danger" onClick={() => void handleClean()}>
            Clean data
          </button>
          <div className="text-xs text-riat-dim">{status}</div>
        </aside>
      </div>
    </AppShell>
  );
};
