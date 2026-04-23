import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from 'react-leaflet'
import { riskColor } from '../api/client'

const center = [18.5, 87.5]

function markerRadius(dri) {
  if (dri > 75) return 14
  if (dri >= 40) return 11
  return 9
}

function factorLine(factor) {
  return `${factor.label || factor.name} (${factor.impact}%)`
}

export default function MapView({ shipments, selectedShipment, onSelectShipment }) {
  return (
    <div className="map-wrap">
      <div className="map-status-bar">
        <div>
          <span className="status-dot status-high" />
          High
        </div>
        <div>
          <span className="status-dot status-medium" />
          Medium
        </div>
        <div>
          <span className="status-dot status-low" />
          Low
        </div>
      </div>

      <MapContainer center={center} zoom={4} minZoom={2} className="decision-map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {shipments.map((shipment) => {
          const color = riskColor(shipment.status)
          const isSelected = selectedShipment?.id === shipment.id

          return (
            <CircleMarker
              key={shipment.id}
              center={[shipment.lat, shipment.lon]}
              radius={isSelected ? markerRadius(shipment.dri) + 4 : markerRadius(shipment.dri)}
              pathOptions={{
                color: isSelected ? '#ffffff' : color,
                fillColor: color,
                fillOpacity: 0.82,
                opacity: 1,
                weight: isSelected ? 4 : 2,
              }}
              eventHandlers={{
                click: (event) => {
                  onSelectShipment(shipment)
                  event.target.openPopup()
                },
                mouseover: (event) => {
                  event.target.openPopup()
                },
              }}
            >
              <Tooltip direction="top" opacity={0.92} permanent={shipment.dri > 75}>
                <span>{shipment.id} · DRI {shipment.dri}</span>
              </Tooltip>
              <Popup>
                <div className="map-popup">
                  <strong>Shipment: {shipment.id}</strong>
                  <span>DRI: {shipment.dri} ({shipment.statusLabel})</span>
                  <span>
                    Location: {shipment.lat.toFixed(2)}, {shipment.lon.toFixed(2)}
                  </span>
                  <span>Factors:</span>
                  <ul>
                    {shipment.top_factors.slice(0, 2).map((factor) => (
                      <li key={`${shipment.id}-${factor.name}`}>{factorLine(factor)}</li>
                    ))}
                  </ul>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
    </div>
  )
}
