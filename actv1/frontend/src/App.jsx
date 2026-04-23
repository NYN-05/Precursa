import { useCallback, useEffect, useMemo, useState } from 'react'
import MapView from './components/MapView'
import SidePanel from './components/SidePanel'
import {
  approveReroute,
  detectShipmentChanges,
  fetchDashboardShipments,
  initializeSimulation,
  rejectRecommendation,
  requestShipmentDetails,
  simulateMovement,
} from './api/client'
import './App.css'

function App() {
  const [shipmentList, setShipmentList] = useState([])
  const [selectedShipment, setSelectedShipment] = useState(null)
  const [usingFallback, setUsingFallback] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [actionState, setActionState] = useState({ type: '', message: '' })
  const [shipmentChanges, setShipmentChanges] = useState(new Map())

  const topRiskList = useMemo(
    () => [...shipmentList].sort((a, b) => b.dri - a.dri).slice(0, 5),
    [shipmentList],
  )

  const refreshShipments = useCallback(async () => {
    const result = await fetchDashboardShipments()
    
    // Detect changes before updating
    const changes = detectShipmentChanges(result.shipments, shipmentList)
    setShipmentChanges(changes)
    
    // Initialize simulation on first load
    if (shipmentList.length === 0) {
      initializeSimulation(result.shipments)
    }

    setShipmentList(result.shipments)
    setUsingFallback(result.usingFallback)
    setLastUpdated(new Date())
    setSelectedShipment((current) => {
      const refreshed = current ? result.shipments.find((shipment) => shipment.id === current.id) : null
      return refreshed || current || result.shipments[0] || null
    })
  }, [shipmentList])

  // Data refresh loop (5 seconds)
  useEffect(() => {
    const refreshTimer = window.setTimeout(refreshShipments, 0)
    const interval = window.setInterval(refreshShipments, 5000)
    return () => {
      window.clearTimeout(refreshTimer)
      window.clearInterval(interval)
    }
  }, [refreshShipments])

  // Movement simulation loop (1 second)
  useEffect(() => {
    if (shipmentList.length === 0) return

    const movementInterval = window.setInterval(() => {
      setShipmentList((prevShipments) => {
        const movedShipments = simulateMovement(prevShipments)
        
        // Detect changes from movement + events
        const changes = detectShipmentChanges(movedShipments, prevShipments)
        setShipmentChanges(changes)

        return movedShipments
      })
    }, 1000)

    return () => window.clearInterval(movementInterval)
  }, [shipmentList.length])

  const handleSelectShipment = useCallback((shipment) => {
    setSelectedShipment(shipment)
    setActionState({ type: '', message: '' })
  }, [])

  const handleAction = useCallback(async (action) => {
    if (!selectedShipment) return

    const actionLabels = {
      approve: 'Approved reroute',
      reject: 'Rejected recommendation',
      details: 'Loaded backend details',
    }

    setActionState({ type: 'pending', message: `${actionLabels[action]} request in progress...` })

    try {
      if (action === 'approve') {
        await approveReroute(selectedShipment.id)
      } else if (action === 'reject') {
        await rejectRecommendation(selectedShipment.id)
      } else {
        const response = await requestShipmentDetails(selectedShipment.id)
        setActionState({
          type: 'success',
          message: response.data?.explanation || 'Backend copilot details loaded for this shipment.',
        })
        return
      }

      setActionState({
        type: 'success',
        message: `${actionLabels[action]} for ${selectedShipment.id}. Backend endpoint accepted the action.`,
      })
      refreshShipments()
    } catch (error) {
      setActionState({
        type: 'error',
        message:
          error?.response?.data?.detail ||
          `Could not complete ${actionLabels[action].toLowerCase()} for ${selectedShipment.id}.`,
      })
    }
  }, [refreshShipments, selectedShipment])

  return (
    <div className="app-shell">
      <main className="map-pane">
        <MapView
          shipments={shipmentList}
          selectedShipment={selectedShipment}
          onSelectShipment={handleSelectShipment}
          shipmentChanges={shipmentChanges}
        />
      </main>
      <aside className="panel-pane">
        <SidePanel
          selectedShipment={selectedShipment}
          shipmentList={shipmentList}
          topRiskList={topRiskList}
          usingFallback={usingFallback}
          lastUpdated={lastUpdated}
          actionState={actionState}
          onSelectShipment={handleSelectShipment}
          onAction={handleAction}
          shipmentChanges={shipmentChanges}
        />
      </aside>
    </div>
  )
}

export default App
