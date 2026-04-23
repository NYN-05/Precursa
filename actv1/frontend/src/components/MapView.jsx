import { useEffect, useMemo, useState } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet'

const center = [18.5, 87.5]

function getColor(dri) {
  if (dri > 75) return '#EF4444'
  if (dri > 40) return '#F59E0B'
  return '#10B981'
}

function markerRadius(dri) {
  if (dri > 75) return 7
  if (dri >= 40) return 6
  return 5
}

function statusLabel(dri) {
  if (dri > 75) return 'High Risk'
  if (dri > 40) return 'Medium Risk'
  return 'Low Risk'
}

function MapSelectionFocus({ selectedShipment }) {
  const map = useMap()

  useEffect(() => {
    if (!selectedShipment) return

    const targetLat = Number(selectedShipment.lat)
    const targetLon = Number(selectedShipment.lon)
    if (!Number.isFinite(targetLat) || !Number.isFinite(targetLon)) return

    const targetZoom = Math.max(map.getZoom(), 5)
    map.flyTo([targetLat, targetLon], targetZoom, { duration: 0.65 })
  }, [map, selectedShipment])

  return null
}

export default function MapView({ shipments, selectedShipment, onSelectShipment, shipmentChanges = new Map(), fleetCoverage }) {
  const [hoveredId, setHoveredId] = useState(null)
  const selectedId = selectedShipment?.id || null

  const markerStates = useMemo(() => {
    return new Map(
      shipments.map((shipment) => {
        const isSelected = selectedId === shipment.id
        const isHovered = hoveredId === shipment.id
        const color = getColor(shipment.dri)

        return [
          shipment.id,
          {
            color,
            radius: markerRadius(shipment.dri) + (isSelected ? 4 : isHovered ? 2 : 0),
            isSelected,
            isHighRisk: shipment.dri > 75,
            status: statusLabel(shipment.dri),
          },
        ]
      }),
    )
  }, [hoveredId, selectedId, shipments])

  return (
    <div className="map-wrap">
      <div className="map-status-bar">
        <div>
          <span className="status-dot status-high" />
          High Risk
        </div>
        <div>
          <span className="status-dot status-medium" />
          Medium Risk
        </div>
        <div>
          <span className="status-dot status-low" />
          Low Risk
        </div>
        <div className="status-divider">
          <span className="pulse-dot" />
          Live Updates
        </div>
        {fleetCoverage && (
          <div className="status-divider">
            <span className="pulse-dot" />
            Fleet {fleetCoverage.visible}/{fleetCoverage.total}
          </div>
        )}
      </div>

      <MapContainer center={center} zoom={4} minZoom={2} className="decision-map">
        <MapSelectionFocus selectedShipment={selectedShipment} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {shipments.map((shipment) => {
          const markerState = markerStates.get(shipment.id)
          if (!markerState) return null

          const change = shipmentChanges.get(shipment.id)
          const hasRecentEvent = Boolean(change?.eventTriggered)

          return (
            <CircleMarker
              key={shipment.id}
              center={[shipment.lat, shipment.lon]}
              radius={markerState.radius}
              pathOptions={{
                color: markerState.isSelected ? '#E5E7EB' : markerState.color,
                fillColor: markerState.color,
                fillOpacity: markerState.isSelected ? 1 : 0.88,
                opacity: 1,
                weight: markerState.isSelected ? 2.8 : 1.2,
              }}
              className={`shipment-marker ${markerState.isHighRisk ? 'high-risk-pulse' : ''} ${hasRecentEvent ? 'event-triggered' : ''}`}
              eventHandlers={{
                click: () => {
                  onSelectShipment(shipment)
                },
                mouseover: (event) => {
                  setHoveredId(shipment.id)
                  event.target.openTooltip()
                },
                mouseout: () => {
                  setHoveredId((current) => (current === shipment.id ? null : current))
                },
              }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={1} className="map-tooltip-shell">
                <div className="marker-tooltip-card">
                  <div className="marker-tooltip-head">
                    <strong>{shipment.id}</strong>
                    <span className="tooltip-dri">DRI {shipment.dri}</span>
                  </div>
                  <div className="marker-tooltip-status">{markerState.status}</div>
                </div>
              </Tooltip>
            </CircleMarker>
          )
        })}
      </MapContainer>
    </div>
  )
}
