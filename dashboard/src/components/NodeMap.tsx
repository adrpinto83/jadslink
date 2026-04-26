import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Create a custom marker icon using SVG
const createCustomIcon = () => {
  return L.divIcon({
    html: `
      <svg width="32" height="40" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M16 0C9.92487 0 5 4.92487 5 11C5 19 16 40 16 40C16 40 27 19 27 11C27 4.92487 22.0751 0 16 0Z" fill="#3b82f6" stroke="#1e40af" stroke-width="2"/>
        <circle cx="16" cy="11" r="4" fill="white"/>
      </svg>
    `,
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -40],
    className: 'custom-marker'
  });
};

interface Node {
  id: string;
  name: string;
  location: {
    lat: number | null;
    lng: number | null;
  } | null;
}

interface NodeMapProps {
  nodes: Node[];
}

const NodeMap: React.FC<NodeMapProps> = ({ nodes }) => {
  const position: [number, number] = [6.4238, -66.5897]; // Default to Venezuela center
  const customIcon = createCustomIcon();

  return (
    <MapContainer
      center={position}
      zoom={5}
      style={{ height: '100%', width: '100%', zIndex: 0 }}
      className="rounded-lg relative z-0"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {nodes.map(node => (
        node.location && node.location.lat && node.location.lng ? (
          <Marker key={node.id} position={[node.location.lat, node.location.lng]} icon={customIcon}>
            <Popup>
              <div className="text-sm">
                <strong>{node.name}</strong>
                {node.location?.address && <p className="text-xs text-gray-600">{node.location.address}</p>}
              </div>
            </Popup>
          </Marker>
        ) : null
      ))}
    </MapContainer>
  );
};

export default NodeMap;
