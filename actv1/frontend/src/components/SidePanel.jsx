import { riskColor, riskLabel } from '../api/client'

function money(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value || 0)
}

function factorText(factor) {
  return `${factor.label || factor.name} -> ${factor.impact}%`
}

function updatedLabel(date) {
  if (!date) return 'Waiting for first refresh'
  return `Updated ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
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
}) {
  return (
    <div className="side-panel">
      <header className="panel-header">
        <div>
          <p className="eyebrow">AI Copilot</p>
          <h1>Decision Intelligence</h1>
        </div>
        <span className="refresh-pill">{updatedLabel(lastUpdated)}</span>
      </header>

      {usingFallback && (
        <div className="notice">
          Backend unavailable. Showing resilient fallback shipments with default DRI values.
        </div>
      )}

      <section className="risk-feed" aria-label="Top shipment risk feed">
        <div className="section-title">
          <h2>Top Risk Feed</h2>
          <span>{shipmentList.length} live shipments</span>
        </div>

        <div className="feed-list">
          {topRiskList.map((shipment, index) => {
            const change = shipmentChanges.get(shipment.id)
            const showAlert = change?.driChanged && change?.newDri > change?.oldDri
            
            return (
              <button
                className={`feed-item ${selectedShipment?.id === shipment.id ? 'active' : ''} ${showAlert ? 'alert' : ''}`}
                key={shipment.id}
                onClick={() => onSelectShipment(shipment)}
                type="button"
              >
                <div className="feed-main">
                  <span className="rank">{index + 1}</span>
                  <span
                    className="risk-dot"
                    style={{ background: riskColor(shipment.status) }}
                    aria-label={`${shipment.statusLabel} risk`}
                  />
                  <strong>{shipment.id}</strong>
                  <span className="dri-pill">DRI {shipment.dri}</span>
                </div>
                {showAlert && (
                  <div className="alert-badge">
                    ⚠️ DRI {change.oldDri} → {change.newDri}
                  </div>
                )}
                {change?.eventTriggered && (
                  <div className="event-badge">🚨 {change.eventTriggered}</div>
                )}
                <ul className="reason-list">
                  {shipment.top_factors.slice(0, 3).map((factor) => (
                    <li key={`${shipment.id}-${factor.name}`}>{factor.label || factor.name}</li>
                  ))}
                </ul>
              </button>
            )
          })}
        </div>
      </section>

      {selectedShipment ? (
        <section className="selected-insight">
          <div className="selected-topline">
            <div>
              <p className="eyebrow">Selected Shipment</p>
              <h2>{selectedShipment.id}</h2>
            </div>
            <div className="score-gauge" style={{ borderColor: riskColor(selectedShipment.status) }}>
              <span>{selectedShipment.dri}</span>
              <small>DRI</small>
            </div>
          </div>

          {shipmentChanges.get(selectedShipment.id)?.eventTriggered && (
            <div className="event-notification">
              🚨 <strong>{shipmentChanges.get(selectedShipment.id).eventTriggered}</strong>
              <p>Risk has increased due to real-time event detection.</p>
            </div>
          )}

          <div className="explanation-block">
            <h3>
              Shipment {selectedShipment.id} is {riskLabel(selectedShipment.status)} RISK because:
            </h3>
            <ul>
              {selectedShipment.top_factors.map((factor) => (
                <li key={`${selectedShipment.id}-detail-${factor.name}`}>{factorText(factor)}</li>
              ))}
            </ul>
          </div>

          <div className="recommendation-block">
            <h3>Recommendation</h3>
            <p>-&gt; Reroute via {selectedShipment.recommendation.route}</p>
            <p>-&gt; Estimated time saved: {selectedShipment.recommendation.time_saved}</p>
            <p>-&gt; Cost impact: +{money(selectedShipment.recommendation.cost_impact)}</p>
          </div>

          <div className="action-row">
            <button className="primary-action" type="button" onClick={() => onAction('approve')}>
              Approve Reroute
            </button>
            <button type="button" onClick={() => onAction('reject')}>
              Reject
            </button>
            <button type="button" onClick={() => onAction('details')}>
              View Details
            </button>
          </div>

          {actionState?.message && (
            <div className={`action-state ${actionState.type || ''}`}>{actionState.message}</div>
          )}
        </section>
      ) : (
        <section className="selected-insight empty">
          Select a shipment marker or top-risk item to load the risk explanation and recommended action.
        </section>
      )}
    </div>
  )
}
