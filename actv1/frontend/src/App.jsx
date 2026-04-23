import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import MapView from './components/MapView'
import SidePanel from './components/SidePanel'
import {
  approveReroute,
  detectShipmentChanges,
  fetchDashboardShipments,
  generateGlobalShipCatalog,
  initializeSimulation,
  overlayLiveShipments,
  rejectRecommendation,
  requestShipmentDetails,
  snapToSea,
  simulateMovement,
} from './api/client'
import './App.css'

function statusFromDri(dri) {
  if (dri > 75) return 'high'
  if (dri >= 40) return 'medium'
  return 'low'
}

function stableRerouteOffset(seed) {
  const source = `${seed || 'ship'}:reroute`
  let hash = 0
  for (let index = 0; index < source.length; index += 1) {
    hash = (hash * 31 + source.charCodeAt(index)) % 1000
  }
  return (hash / 1000 - 0.5) * 0.8
}

function applyAutoReroute(candidate, driDrop) {
  const lat = Number(candidate.lat)
  const lon = Number(candidate.lon)
  const safeLat = Number.isFinite(lat) ? lat : 0
  const safeLon = Number.isFinite(lon) ? lon : 0

  const destinationLat = Number(candidate.destination_lat)
  const destinationLon = Number(candidate.destination_lon)
  const fallbackOffset = stableRerouteOffset(candidate.id)
  const safeDestinationLat = Number.isFinite(destinationLat) ? destinationLat : safeLat + 3.2 + fallbackOffset
  const safeDestinationLon = Number.isFinite(destinationLon) ? destinationLon : safeLon + 4.1 - fallbackOffset

  let vectorLat = safeDestinationLat - safeLat
  let vectorLon = safeDestinationLon - safeLon
  let magnitude = Math.hypot(vectorLat, vectorLon)
  if (magnitude < 0.001) {
    vectorLat = 1.2 + fallbackOffset
    vectorLon = 1.6 - fallbackOffset
    magnitude = Math.hypot(vectorLat, vectorLon)
  }

  const unitLat = vectorLat / magnitude
  const unitLon = vectorLon / magnitude
  const crossLat = -unitLon
  const crossLon = unitLat

  const nextLat = safeLat + unitLat * 0.35 + crossLat * 0.08
  const nextLon = safeLon + unitLon * 0.35 + crossLon * 0.08
  const nextDestinationLat = safeDestinationLat + crossLat * 1.1 + fallbackOffset * 0.4
  const nextDestinationLon = safeDestinationLon + crossLon * 1.1 - fallbackOffset * 0.4

  const safeCurrent = snapToSea(nextLat, nextLon)
  const safeDestination = snapToSea(nextDestinationLat, nextDestinationLon)

  const nextDri = Math.max(6, Math.min(96, Number(candidate.dri) - driDrop))
  const nextStatus = statusFromDri(nextDri)

  return {
    ...candidate,
    lat: safeCurrent.lat,
    lon: safeCurrent.lon,
    destination_lat: safeDestination.lat,
    destination_lon: safeDestination.lon,
    progress: 0.1,
    movement_mode: 'dynamic',
    reroute_moving_until: Date.now() + 60000,
    dri: nextDri,
    status: nextStatus,
    statusLabel: nextStatus.toUpperCase(),
    recommendation: {
      ...(candidate.recommendation || {}),
      route: candidate.destination_port || candidate.recommendation?.route || 'Dynamic reroute corridor',
    },
  }
}

function App() {
  const [catalogShipments, setCatalogShipments] = useState(() => generateGlobalShipCatalog())
  const [liveShipments, setLiveShipments] = useState([])
  const [visibleCount, setVisibleCount] = useState(24)
  const [selectedShipment, setSelectedShipment] = useState(null)
  const [usingFallback, setUsingFallback] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [actionState, setActionState] = useState({ type: '', message: '' })
  const [shipmentChanges, setShipmentChanges] = useState(new Map())
  const [automationEnabled, setAutomationEnabled] = useState(false)
  const [automationThreshold, setAutomationThreshold] = useState(75)
  const [reroutingShipments, setReroutingShipments] = useState(new Set())
  const [modelStatus, setModelStatus] = useState({
    connected: false,
    model: 'qwen2.5:7b',
    lastResponse: null,
    responseTime: 0,
  })
  const shipmentListRef = useRef([])
  const rerouteTimersRef = useRef(new Map())
  const rerouteCooldownRef = useRef(new Map())

  const visibleCatalog = useMemo(() => catalogShipments.slice(0, visibleCount), [catalogShipments, visibleCount])
  const shipmentList = useMemo(() => {
    return overlayLiveShipments(visibleCatalog, liveShipments)
  }, [liveShipments, visibleCatalog])

  useEffect(() => {
    shipmentListRef.current = shipmentList
  }, [shipmentList])

  useEffect(() => {
    return () => {
      rerouteTimersRef.current.forEach((timerId) => window.clearTimeout(timerId))
      rerouteTimersRef.current.clear()
    }
  }, [])

  const topRiskList = useMemo(
    () => [...shipmentList].sort((a, b) => b.dri - a.dri).slice(0, 2),
    [shipmentList],
  )

  const catalogCoverage = useMemo(() => {
    const liveHits = shipmentList.filter((shipment) => shipment.live_overlay).length
    return {
      total: catalogShipments.length,
      visible: shipmentList.length,
      liveHits,
    }
  }, [catalogShipments.length, shipmentList])

  const refreshShipments = useCallback(async () => {
    const result = await fetchDashboardShipments()
    const currentShipments = shipmentListRef.current
    const changes = detectShipmentChanges(result.shipments, currentShipments)
    setShipmentChanges(changes)

    setLiveShipments(result.shipments)
    setUsingFallback(result.usingFallback)
    setLastUpdated(new Date())
    initializeSimulation(result.shipments)
    setSelectedShipment((current) => {
      const refreshed = current ? currentShipments.find((shipment) => shipment.id === current.id) : null
      return refreshed || current || currentShipments[0] || result.shipments[0] || null
    })
  }, [])

  // Check local model status periodically
  useEffect(() => {
    const checkModelStatus = async () => {
      try {
        const startTime = performance.now()
        const response = await fetch('http://localhost:11434/api/tags', { timeout: 5000 })
        const endTime = performance.now()
        
        if (response.ok) {
          const data = await response.json()
          const hasModel = data.models?.some((m) => m.name?.includes('qwen'))
          setModelStatus({
            connected: true,
            model: 'qwen2.5:7b',
            lastResponse: new Date(),
            responseTime: Math.round(endTime - startTime),
          })
        } else {
          setModelStatus((prev) => ({ ...prev, connected: false }))
        }
      } catch (error) {
        setModelStatus((prev) => ({ ...prev, connected: false }))
      }
    }

    checkModelStatus()
    const modelCheckInterval = window.setInterval(checkModelStatus, 10000)
    return () => window.clearInterval(modelCheckInterval)
  }, [])

  useEffect(() => {
    const revealTimer = window.setInterval(() => {
      setVisibleCount((current) => Math.min(catalogShipments.length, current + 8))
    }, 2200)

    return () => window.clearInterval(revealTimer)
  }, [catalogShipments.length])

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
      setCatalogShipments((prevShipments) => {
        const movedShipments = simulateMovement(prevShipments)
        const changes = detectShipmentChanges(movedShipments, prevShipments)
        setShipmentChanges(changes)

        return movedShipments
      })
    }, 1000)

    return () => window.clearInterval(movementInterval)
  }, [shipmentList.length])

  // Auto-rerouting loop for high DRI shipments.
  useEffect(() => {
    if (!automationEnabled) {
      rerouteTimersRef.current.forEach((timerId) => window.clearTimeout(timerId))
      rerouteTimersRef.current.clear()
      setReroutingShipments(new Set())
      return
    }

    const now = Date.now()
    const highRiskCutoff = Math.max(75, automationThreshold)

    shipmentList.forEach((shipment) => {
      const isHighRisk = Number(shipment.dri) > highRiskCutoff
      if (!isHighRisk) return
      if (rerouteTimersRef.current.has(shipment.id)) return

      const cooldownUntil = rerouteCooldownRef.current.get(shipment.id) || 0
      if (now < cooldownUntil) return

      setReroutingShipments((prev) => {
        const next = new Set(prev)
        next.add(shipment.id)
        return next
      })

      const delayMs = 3000 + Math.floor(Math.random() * 1000)
      const timerId = window.setTimeout(() => {
        rerouteTimersRef.current.delete(shipment.id)
        rerouteCooldownRef.current.set(shipment.id, Date.now() + 10000)

        const driDrop = 8 + Math.floor(Math.random() * 10)

        setCatalogShipments((prevShipments) =>
          prevShipments.map((candidate) => {
            if (candidate.id !== shipment.id) return candidate
            return applyAutoReroute(candidate, driDrop)
          }),
        )

        setLiveShipments((prevShipments) =>
          prevShipments.map((candidate) => {
            if (candidate.id !== shipment.id) return candidate
            return applyAutoReroute(candidate, driDrop)
          }),
        )

        setShipmentChanges((prevChanges) => {
          const previous = prevChanges.get(shipment.id)
          const currentDri = Number(shipment.dri)
          const nextDri = Math.max(6, Math.min(96, currentDri - driDrop))
          const nextChanges = new Map(prevChanges)
          nextChanges.set(shipment.id, {
            ...previous,
            driChanged: true,
            oldDri: currentDri,
            newDri: nextDri,
            eventTriggered: 'Auto reroute applied and vessel course changed',
          })
          return nextChanges
        })

        setReroutingShipments((prev) => {
          const next = new Set(prev)
          next.delete(shipment.id)
          return next
        })
      }, delayMs)

      rerouteTimersRef.current.set(shipment.id, timerId)
    })
  }, [automationEnabled, automationThreshold, shipmentList])

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
          fleetCoverage={catalogCoverage}
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
          fleetCoverage={catalogCoverage}
          automationEnabled={automationEnabled}
          onAutomationToggle={setAutomationEnabled}
          automationThreshold={automationThreshold}
          onThresholdChange={setAutomationThreshold}
          modelStatus={modelStatus}
          reroutingShipments={reroutingShipments}
        />
      </aside>
    </div>
  )
}

export default App
