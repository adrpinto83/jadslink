import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icon issue with webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

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

  return (
    <MapContainer center={position} zoom={5} style={{ height: '100%', width: '100%' }} className="rounded-lg">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {nodes.map(node => (
        node.location && node.location.lat && node.location.lng ? (
          <Marker key={node.id} position={[node.location.lat, node.location.lng]}>
            <Popup>
              <strong>{node.name}</strong>
            </Popup>
          </Marker>
        ) : null
      ))}
    </MapContainer>
  );
};

export default NodeMap;
