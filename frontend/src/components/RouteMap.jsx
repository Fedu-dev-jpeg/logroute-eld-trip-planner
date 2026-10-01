import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from "react-leaflet";

function FitRoute({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 1) map.fitBounds(points, { padding: [38, 38] });
  }, [map, points]);
  return null;
}

export default function RouteMap({ plan }) {
  const points = plan.route.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  const locations = [
    { ...plan.locations.current, name: "Current location", color: "#0ea5e9" },
    { ...plan.locations.pickup, name: "Pickup", color: "#f59e0b" },
    { ...plan.locations.dropoff, name: "Drop-off", color: "#16a34a" },
  ];

  return (
    <div className="map-wrap">
      <MapContainer center={points[0]} zoom={6} scrollWheelZoom className="route-map">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Polyline positions={points} pathOptions={{ color: "#0f766e", weight: 5, opacity: 0.9 }} />
        {locations.map((location) => (
          <CircleMarker key={location.name} center={[location.lat, location.lon]} radius={9} pathOptions={{ color: "#fff", weight: 3, fillColor: location.color, fillOpacity: 1 }}>
            <Popup><strong>{location.name}</strong><br />{location.label}</Popup>
          </CircleMarker>
        ))}
        {plan.stops.map((stop, index) => (
          <CircleMarker key={`${stop.kind}-${index}`} center={[stop.coordinate[1], stop.coordinate[0]]} radius={6} pathOptions={{ color: "#fff", weight: 2, fillColor: "#7c3aed", fillOpacity: 1 }}>
            <Popup><strong>{stop.title}</strong><br />Near mile {Math.round(stop.mile)}</Popup>
          </CircleMarker>
        ))}
        <FitRoute points={points} />
      </MapContainer>
      <div className="map-legend">
        <span><i className="dot-start" />Start</span><span><i className="dot-pickup" />Pickup</span><span><i className="dot-drop" />Drop-off</span><span><i className="dot-stop" />HOS stop</span>
      </div>
    </div>
  );
}

