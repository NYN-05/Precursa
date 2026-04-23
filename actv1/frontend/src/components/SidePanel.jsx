import { useEffect, useState } from "react"
import axios from "axios"
import { API_PREFIX, authHeaders, ensureAccessToken } from "../api/client"

export default function SidePanel() {
  const [shipments, setShipments] = useState([])
  const [selected, setSelected] = useState(null)
  const [explanation, setExplanation] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    setError("")
    try {
      const token = await ensureAccessToken()
      const res = await axios.get(`${API_PREFIX}/risk/shipments?limit=20&top_k=3`, {
        headers: authHeaders(token),
      })
      setShipments(res.data)
    } catch (err) {
      console.error(err)
      setError("Unable to load shipments. Check backend status and credentials.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleExplain = async (shipment) => {
    setSelected(shipment)
    setExplanation("Analyzing...")

    try {
      const token = await ensureAccessToken()
      const res = await axios.post(
        `${API_PREFIX}/copilot`,
        {
          shipment_key: shipment.shipment_key,
          question: "Why is this shipment at this risk level and what action is recommended?",
        },
        {
          headers: authHeaders(token),
        },
      )
      setExplanation(res.data.explanation)
    } catch {
      setExplanation("Failed to fetch explanation.")
    }
  }

  return (
    <div className="side-panel">
      <h2 style={{ marginBottom: "20px" }}>AI Copilot</h2>

      {isLoading && <p>Loading shipment risk feed...</p>}
      {error && <p style={{ color: "#fca5a5" }}>{error}</p>}

      {shipments.map((s, i) => (
        <div key={s.shipment_key ?? i} style={{
          padding: "10px",
          marginBottom: "10px",
          borderRadius: "8px",
          background: "rgba(255,255,255,0.05)"
        }}>
          <strong>{s.shipment_key}</strong><br />
          DRI: {s.dri}<br />

          <button
            onClick={() => handleExplain(s)}
            style={{
              marginTop: "5px",
              padding: "5px 10px",
              background: "#2563eb",
              border: "none",
              borderRadius: "5px",
              color: "white",
              cursor: "pointer"
            }}
          >
            Explain Risk
          </button>
        </div>
      ))}

      {selected && (
        <div style={{
          marginTop: "20px",
          padding: "15px",
          background: "rgba(37, 99, 235, 0.1)",
          borderRadius: "10px"
        }}>
          <h3>AI Insight</h3>
          <p>{explanation}</p>
        </div>
      )}
    </div>
  )
}