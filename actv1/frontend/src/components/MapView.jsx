import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import axios from 'axios'
import { useEffect, useState } from 'react'
import { API_PREFIX, authHeaders, ensureAccessToken } from '../api/client'

const center = [1.264, 103.819]


// 🎯 DRI color
function getColor(dri) {
  if (dri > 75) return 'red'
  if (dri > 40) return 'orange'
  return 'green'
}

// 🌦 Weather color
function getWeatherColor(risk) {
  if (risk > 60) return 'red'
  if (risk > 30) return 'yellow'
  return 'green'
}


export default function MapView() {
  const [shipments, setShipments] = useState([])
  const [vessels, setVessels] = useState([])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const token = await ensureAccessToken()
      // Fetching snapshots which have position in feature_vector or derived from port names
      const s = await axios.get(`${API_PREFIX}/state/snapshots`, {
        headers: authHeaders(token),
      })
      
      // Basic port mapping for demo purposes
      const portCoords = {
        "Mumbai": [18.9220, 72.8347],
        "Rotterdam": [51.9225, 4.4792],
        "Shanghai": [31.2304, 121.4737],
        "Los Angeles": [33.7291, -118.2620],
        "Singapore": [1.3521, 103.8198],
        "Hamburg": [53.5753, 9.9920],
        "Chennai": [13.0827, 80.2707],
        "Felixstowe": [51.9614, 1.3514],
        "Jebel Ali": [24.9857, 55.0272],
        "Antwerp": [51.2194, 4.4025],
        "Colombo": [6.9271, 79.8612],
        "Busan": [35.1796, 129.0756],
        "Savannah": [32.0809, -81.0912],
      };

      const mappedShipments = s.data.map(item => {
        const fv = item.feature_vector || {};
        const originPort = fv.origin_port || "Singapore";
        const coords = portCoords[originPort] || center;
        
        return {
          id: item.shipment_key,
          lat: coords[0] + (Math.random() - 0.5) * 2, // Slight randomization for map clarity
          lon: coords[1] + (Math.random() - 0.5) * 2,
          dri: item.provisional_dri,
          weather_risk: fv.delay_hours || (Math.random() * 100),
          rerouted: fv.status === 'rerouted' || item.provisional_dri > 75
        };
      });

      setShipments(mappedShipments)
      
      // For now, return some mock vessels near Singapore
      setVessels([
        { lat: 1.2, lon: 103.8 },
        { lat: 1.3, lon: 104.0 },
        { lat: 1.1, lon: 103.5 },
      ])
    } catch (err) {
      console.error("API ERROR:", err)
    }
  }

  return (
    <MapContainer center={center} zoom={5} style={{ height: '100vh', width: '100%' }}>
      
      {/* 🌍 DARK MAP */}
      <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />

      {/* 🚢 AIS VESSELS */}
      {vessels.map((v, i) => (
        <CircleMarker
          key={"vessel-" + i}
          center={[v.lat, v.lon]}
          radius={4}
          pathOptions={{ color: '#22c55e' }}
        />
      ))}

      {/* 📦 SHIPMENTS */}
      {shipments.map((s, i) => (
        <CircleMarker
          key={"shipment-" + i}
          center={[s.lat, s.lon]}
          radius={8}
          pathOptions={{
            color: getColor(s.dri),
            fillColor: getColor(s.dri)
          }}
        >
          <Popup>
            <strong>{s.id}</strong><br />
            DRI: {s.dri}<br />
            Weather: {Math.round(s.weather_risk)}<br />
            {s.rerouted ? "⚠️ High Risk" : "✅ Stable"}
          </Popup>
        </CircleMarker>
      ))}

      {/* 🌦 WEATHER ZONES */}
      {shipments.map((s, i) => (
        <CircleMarker
          key={"weather-" + i}
          center={[s.lat, s.lon]}
          radius={25}
          pathOptions={{
            color: getWeatherColor(s.weather_risk),
            fillColor: getWeatherColor(s.weather_risk),
            fillOpacity: 0.15
          }}
        >
          <Popup>
            🌦 Weather Risk: {Math.round(s.weather_risk)}
          </Popup>
        </CircleMarker>
      ))}

    </MapContainer>
  )
}