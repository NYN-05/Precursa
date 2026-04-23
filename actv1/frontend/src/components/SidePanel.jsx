import { useMemo, useState } from 'react'

function money(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value || 0)
}

function formatFactorName(factor) {
  return factor?.label || factor?.name || 'Unknown signal'
}

function updatedLabel(date) {
  if (!date) return 'Awaiting first update'
  return `Updated ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
}

function riskTone(dri) {
  if (dri > 75) return 'high'
  if (dri > 40) return 'medium'
  return 'low'
}

function riskColorByTone(tone) {
  if (tone === 'high') return '#EF4444'
  if (tone === 'medium') return '#F59E0B'
  return '#10B981'
}

function riskLabelByTone(tone) {
  if (tone === 'high') return 'HIGH'
  if (tone === 'medium') return 'MEDIUM'
  return 'LOW'
}

export default function SidePanel({
  selectedShipment,
  shipmentList,
  topRiskList,
  usingFallback,
  lastUpdated,
  actionState,
  onSelectShipment,
  onAction,
  shipmentChanges = new Map(),
  fleetCoverage,
  automationEnabled,
  onAutomationToggle,
  automationThreshold,
  onThresholdChange,
  modelStatus,
  reroutingShipments = new Set(),
}) {
  const selectedTone = riskTone(selectedShipment?.dri || 0)
  const [modelQuestion, setModelQuestion] = useState('')
  const [modelAnswer, setModelAnswer] = useState('')
  const [modelLoading, setModelLoading] = useState(false)

  const ringStyle = useMemo(() => {
    if (!selectedShipment) return undefined
    const dri = Math.max(0, Math.min(96, Number(selectedShipment.dri || 0)))
    const color = riskColorByTone(riskTone(dri))
    return {
      '--ring-fill': `${dri}%`,
      '--ring-color': color,
    }
  }, [selectedShipment])

  const askModel = async (e) => {
    e.preventDefault()
    if (!modelQuestion.trim() || modelLoading) return

    setModelLoading(true)
    setModelAnswer('')

    try {
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'qwen2.5:7b',
          prompt: modelQuestion,
          stream: false,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setModelAnswer(data.response || 'No response from model')
      } else {
        setModelAnswer('Error: Unable to connect to model')
      }
    } catch (error) {
      setModelAnswer('Error: ' + error.message)
    } finally {
      setModelLoading(false)
    }
  }

  return (
    <div className="side-panel">
      <header className="panel-header">
        <div className="panel-header-copy">
          <p className="eyebrow">AI Copilot</p>
          <h1>Decision Intelligence</h1>
        </div>
        <span className="refresh-pill">{updatedLabel(lastUpdated)}</span>
      </header>
      <div className="panel-divider" />

      <section className="panel-meta" aria-label="Fleet telemetry summary">
        {fleetCoverage && (
          <div className="meta-chip-row">
            <span className="meta-chip">Visible {fleetCoverage.visible}</span>
            <span className="meta-chip">Catalog {fleetCoverage.total}</span>
            <span className="meta-chip">Live Overlay {fleetCoverage.liveHits}</span>
          </div>
        )}
      </section>

      <section className="panel-section" aria-label="Top shipment risk feed">
        <div className="section-title">
          <h2>Top Risk Feed</h2>
          <span className="section-caption">{shipmentList.length} active shipments</span>
        </div>

        <div className="risk-list">
          {topRiskList.map((shipment, index) => {
            const change = shipmentChanges.get(shipment.id)
            const showAlert = change?.driChanged && change?.newDri > change?.oldDri
            const isRerouting = reroutingShipments.has(shipment.id)
            const tone = riskTone(shipment.dri)
            const topSignals = shipment.top_factors.slice(0, 2)
            const isTop = index === 0
            
            return (
              <button
                className={`risk-item ${isTop ? 'risk-item-top' : ''} ${selectedShipment?.id === shipment.id ? 'risk-item-active' : ''} ${showAlert ? 'risk-item-primary' : ''}`}
                key={shipment.id}
                onClick={() => onSelectShipment(shipment)}
                type="button"
              >
                <div className="risk-item-header">
                  <div className="risk-id-wrap">
                    <span className="rank">{index + 1}</span>
                    <strong className="risk-id">{shipment.id}</strong>
                  </div>
                  <span className="risk-level-badge" style={{ '--badge-color': riskColorByTone(tone) }}>
                    DRI {shipment.dri}
                  </span>
                </div>
                <div className="risk-signals">
                  {topSignals.map((factor) => (
                    <span className="risk-signal" key={`${shipment.id}-${factor.name}`}>
                      {formatFactorName(factor)}
                    </span>
                  ))}
                </div>
                <div className="risk-meta-line">
                  <span>{riskLabelByTone(tone)} RISK</span>
                  {isRerouting && <span>Rerouting...</span>}
                  {!isRerouting && showAlert && <span>DRI {change.oldDri} → {change.newDri}</span>}
                  {!isRerouting && !showAlert && change?.eventTriggered && <span>{change.eventTriggered}</span>}
                  {!isRerouting && !showAlert && !change?.eventTriggered && <span>Signals stable</span>}
                </div>
              </button>
            )
          })}
        </div>
      </section>

      {selectedShipment ? (
        <section className="selected-insight">
          <div className="selected-topline">
            <div className="selected-meta">
              <p className="eyebrow">Selected Shipment</p>
              <h2>{selectedShipment.id}</h2>
            </div>
            <div className="dri-ring" style={ringStyle}>
              <div className="dri-ring-inner">
                <span>{selectedShipment.dri}</span>
                <small>DRI</small>
              </div>
            </div>
          </div>

          {shipmentChanges.get(selectedShipment.id)?.eventTriggered && (
            <div className="event-notification">
              <strong>Realtime Event</strong>
              <p>{shipmentChanges.get(selectedShipment.id).eventTriggered}</p>
            </div>
          )}

          <div className="insight-card">
            <h3>Key Factors</h3>
            <ul className="factor-list">
              {selectedShipment.top_factors.slice(0, 4).map((factor) => (
                <li key={`${selectedShipment.id}-detail-${factor.name}`}>
                  <div className="factor-row">
                    <span>{formatFactorName(factor)}</span>
                    <strong>{factor.impact}%</strong>
                  </div>
                  <div className="factor-bar-track">
                    <div
                      className="factor-bar-fill"
                      style={{
                        width: `${Math.max(4, Math.min(100, factor.impact || 0))}%`,
                        '--factor-color': riskColorByTone(selectedTone),
                      }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="recommendation-hero">
            <div className="recommendation-icon" aria-hidden="true">↗</div>
            <div>
              <h3>Recommended Route</h3>
              <p className="route-primary">{selectedShipment.recommendation.route}</p>
              <p className="route-time">Time saved: {selectedShipment.recommendation.time_saved}</p>
              <p className="route-cost">Cost impact: +{money(selectedShipment.recommendation.cost_impact)}</p>
            </div>
          </div>

          {actionState?.message && (
            <div className={`action-state ${actionState.type || ''}`}>{actionState.message}</div>
          )}
        </section>
      ) : (
        <section className="selected-insight empty">
          Select a shipment from the map or risk feed to load structured intelligence and recommendations.
        </section>
      )}

      <section className="automation-settings">
        <div className="section-title">
          <h3>Automation Settings</h3>
        </div>
        <div className="automation-control">
          <label className="automation-toggle">
            <input
              type="checkbox"
              checked={automationEnabled}
              onChange={(e) => onAutomationToggle(e.target.checked)}
            />
            <span>{automationEnabled ? 'Automation ON' : 'Automation OFF'}</span>
          </label>
        </div>
        {automationEnabled && (
          <div className="threshold-control">
            <label>
              <span>Risk Threshold: {automationThreshold}</span>
              <input
                type="range"
                min="0"
                max="100"
                value={automationThreshold}
                onChange={(e) => onThresholdChange(Number(e.target.value))}
              />
            </label>
            <p className="threshold-hint">Auto-approve reroutes below this DRI threshold</p>
          </div>
        )}
      </section>

      <section className="model-chat">
        <div className="section-title">
          <h3>Ask Local Model</h3>
        </div>
        <form onSubmit={askModel} className="chat-form">
          <textarea
            value={modelQuestion}
            onChange={(e) => setModelQuestion(e.target.value)}
            placeholder="Ask a question about shipment analysis..."
            className="chat-input"
            disabled={modelLoading}
            rows="3"
          />
          <button
            type="submit"
            className="chat-submit"
            disabled={modelLoading || !modelQuestion.trim()}
          >
            {modelLoading ? 'Thinking...' : 'Send'}
          </button>
        </form>

        {modelAnswer && (
          <div className="chat-response">
            <p className="response-label">Model Response:</p>
            <div className="response-text">{modelAnswer}</div>
          </div>
        )}
      </section>
    </div>
  )
}