import axios from "axios";

export const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api/v1";
export const DASHBOARD_SHIPMENTS_ENDPOINT =
  import.meta.env.VITE_SHIPMENTS_ENDPOINT || "/api/shipments";

const DEFAULT_USERNAME = import.meta.env.VITE_DEFAULT_USERNAME || "admin";
const DEFAULT_PASSWORD = import.meta.env.VITE_DEFAULT_PASSWORD || "admin123";
const TOKEN_STORAGE_KEY = "precursa_access_token";
const BACKEND_RETRY_MS = 15000;

let backendRetryAfter = 0;

const PORT_COORDS = {
  Mumbai: [18.922, 72.8347],
  "Nhava Sheva": [18.95, 72.95],
  Chennai: [13.0827, 80.2707],
  Colombo: [6.9271, 79.8612],
  Singapore: [1.3521, 103.8198],
  "Port Klang": [3.0, 101.4],
  "Jebel Ali": [24.9857, 55.0272],
  Suez: [30.0444, 32.5498],
  Rotterdam: [51.9244, 4.4777],
  Hamburg: [53.5511, 9.9937],
  Felixstowe: [51.9542, 1.3511],
  Antwerp: [51.2194, 4.4025],
  Shanghai: [31.2304, 121.4737],
  "Hong Kong": [22.3193, 114.1694],
  Busan: [35.1796, 129.0756],
  "Los Angeles": [33.7405, -118.2775],
};

export const FALLBACK_SHIPMENTS = [
  {
    id: "SGP-0142",
    lat: 1.29,
    lon: 103.85,
    dri: 82,
    status: "high",
    top_factors: [
      { name: "delay_12_hours", impact: 40 },
      { name: "port_congestion", impact: 35 },
      { name: "weather_storm", impact: 25 },
    ],
    recommendation: {
      route: "Port Klang",
      time_saved: "8 hours",
      cost_impact: 12000,
    },
  },
  {
    id: "IND-0331",
    lat: 18.94,
    lon: 72.92,
    dri: 68,
    status: "medium",
    top_factors: [
      { name: "customs_delay", impact: 38 },
      { name: "route_instability", impact: 31 },
      { name: "carrier_reliability", impact: 18 },
    ],
    recommendation: {
      route: "Colombo",
      time_saved: "5 hours",
      cost_impact: 7200,
    },
  },
  {
    id: "SHA-2207",
    lat: 31.23,
    lon: 121.47,
    dri: 77,
    status: "high",
    top_factors: [
      { name: "congestion_spike", impact: 42 },
      { name: "storm_alert", impact: 28 },
      { name: "berth_shortage", impact: 20 },
    ],
    recommendation: {
      route: "Busan",
      time_saved: "7 hours",
      cost_impact: 9400,
    },
  },
  {
    id: "HAM-1180",
    lat: 53.55,
    lon: 9.99,
    dri: 35,
    status: "low",
    top_factors: [
      { name: "minor_port_queue", impact: 18 },
      { name: "carrier_variance", impact: 12 },
    ],
    recommendation: {
      route: "Stay on current route",
      time_saved: "0 hours",
      cost_impact: 0,
    },
  },
  {
    id: "LAX-0914",
    lat: 33.74,
    lon: -118.28,
    dri: 54,
    status: "medium",
    top_factors: [
      { name: "warehouse_backlog", impact: 30 },
      { name: "rail_delay", impact: 21 },
    ],
    recommendation: {
      route: "Direct drayage priority",
      time_saved: "3 hours",
      cost_impact: 4100,
    },
  },
];

export async function ensureAccessToken() {
  const cachedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  if (cachedToken) {
    return cachedToken;
  }

  if (shouldSkipBackend()) {
    return null;
  }

  const formData = new URLSearchParams();
  formData.set("username", DEFAULT_USERNAME);
  formData.set("password", DEFAULT_PASSWORD);

  try {
    const response = await axios.post(`${API_PREFIX}/auth/token`, formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const token = response?.data?.access_token;
    if (token) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
      return token;
    }
  } catch {
    markBackendOffline();
    // Keep endpoints usable in MVP mode where auth fallback is enabled.
  }

  return null;
}

export function authHeaders(token) {
  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

function shouldSkipBackend() {
  return Date.now() < backendRetryAfter;
}

function markBackendOffline() {
  backendRetryAfter = Date.now() + BACKEND_RETRY_MS;
}

function titleize(value) {
  return String(value || "unknown factor")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusFromDri(dri) {
  if (dri > 75) return "high";
  if (dri >= 40) return "medium";
  return "low";
}

function stableOffset(seed, axis) {
  const source = `${seed}:${axis}`;
  let hash = 0;
  for (let i = 0; i < source.length; i += 1) {
    hash = (hash * 31 + source.charCodeAt(i)) % 1000;
  }
  return (hash / 1000 - 0.5) * 0.9;
}

function coordsForShipment(raw, id) {
  const featureVector = raw.feature_vector || {};
  const port = featureVector.origin_port || featureVector.port_name || featureVector.affected_port;
  const coords = PORT_COORDS[port] || PORT_COORDS.Singapore;
  return [
    Number(raw.lat ?? featureVector.lat ?? coords[0] + stableOffset(id, "lat")),
    Number(raw.lon ?? raw.lng ?? featureVector.lon ?? coords[1] + stableOffset(id, "lon")),
  ];
}

function normalizeFactor(factor, index) {
  const rawName = factor?.name ?? factor?.feature ?? factor?.reason ?? `factor_${index + 1}`;
  const rawImpact = factor?.impact ?? factor?.weight ?? factor?.shap_value;
  return {
    name: rawName,
    label: titleize(rawName),
    impact: Math.max(1, Math.round(Math.abs(Number(rawImpact ?? 20 - index * 5)))),
    direction: factor?.direction,
  };
}

function factorsFromSnapshot(raw) {
  const featureVector = raw.feature_vector || {};
  const factors = [];
  const delay = Number(featureVector.delay_hours || 0);
  if (delay > 0) factors.push({ name: `delay_${Math.round(delay)}_hours`, impact: 40 });
  if (featureVector.status) factors.push({ name: featureVector.status, impact: 25 });
  if (featureVector.last_event_type || raw.last_event_type) {
    factors.push({ name: featureVector.last_event_type || raw.last_event_type, impact: 20 });
  }
  if (featureVector.origin_port) factors.push({ name: `${featureVector.origin_port}_port_pressure`, impact: 15 });
  return factors;
}

export function normalizeShipment(raw, index = 0) {
  const id = raw.id || raw.shipment_id || raw.shipment_key || `SHP-${String(index + 1).padStart(4, "0")}`;
  const dri = Math.max(0, Math.min(100, Math.round(Number(raw.dri ?? raw.provisional_dri ?? raw.dri_score ?? 0))));
  const [lat, lon] = coordsForShipment(raw, id);
  const topFactorsSource = raw.top_factors?.length ? raw.top_factors : factorsFromSnapshot(raw);
  const topFactors = (topFactorsSource.length ? topFactorsSource : FALLBACK_SHIPMENTS[index % FALLBACK_SHIPMENTS.length].top_factors)
    .slice(0, 3)
    .map(normalizeFactor);
  const status = String(raw.status || raw.dri_level || statusFromDri(dri)).toLowerCase();
  const featureVector = raw.feature_vector || {};

  return {
    id,
    lat,
    lon,
    dri,
    status,
    statusLabel: status.toUpperCase(),
    top_factors: topFactors,
    recommendation: {
      route: raw.recommendation?.route || featureVector.recommended_route || "Port Klang",
      time_saved: raw.recommendation?.time_saved || featureVector.time_saved || (dri > 75 ? "8 hours" : "3 hours"),
      cost_impact: Number(raw.recommendation?.cost_impact ?? featureVector.cost_impact ?? (dri > 75 ? 12000 : 4500)),
    },
    updated_at: raw.updated_at || raw.scored_at || null,
  };
}

export async function fetchDashboardShipments() {
  if (shouldSkipBackend()) {
    return {
      shipments: FALLBACK_SHIPMENTS.map(normalizeShipment),
      usingFallback: true,
      source: "fallback",
    };
  }

  const token = await ensureAccessToken();
  const headers = authHeaders(token);

  try {
    const response = await axios.get(DASHBOARD_SHIPMENTS_ENDPOINT, { headers });
    return {
      shipments: response.data.map(normalizeShipment),
      usingFallback: false,
      source: DASHBOARD_SHIPMENTS_ENDPOINT,
    };
  } catch {
    try {
      const response = await axios.get(`${API_PREFIX}/state/snapshots?limit=50`, { headers });
      return {
        shipments: response.data.map(normalizeShipment),
        usingFallback: false,
        source: `${API_PREFIX}/state/snapshots`,
      };
    } catch {
      markBackendOffline();
      return {
        shipments: FALLBACK_SHIPMENTS.map(normalizeShipment),
        usingFallback: true,
        source: "fallback",
      };
    }
  }
}

export async function approveReroute(shipmentId) {
  const token = await ensureAccessToken();
  return axios.post(`${API_PREFIX}/routes/reroute/${encodeURIComponent(shipmentId)}`, null, {
    headers: authHeaders(token),
  });
}

export async function rejectRecommendation(shipmentId) {
  const token = await ensureAccessToken();
  return axios.post(
    `${API_PREFIX}/agent/override/${encodeURIComponent(shipmentId)}`,
    {
      reason: "Operator rejected the AI reroute recommendation from the decision dashboard.",
      expires_minutes: 120,
    },
    { headers: authHeaders(token) },
  );
}

export async function requestShipmentDetails(shipmentId) {
  const token = await ensureAccessToken();
  return axios.post(
    `${API_PREFIX}/copilot`,
    {
      shipment_key: shipmentId,
      question: "Explain the DRI score, top factors, and recommended action for this shipment.",
    },
    { headers: authHeaders(token) },
  );
}

export function riskColor(statusOrDri) {
  const status = typeof statusOrDri === "number" ? statusFromDri(statusOrDri) : String(statusOrDri).toLowerCase();
  if (status === "high") return "#ef4444";
  if (status === "medium") return "#f97316";
  return "#22c55e";
}

export function riskLabel(statusOrDri) {
  return typeof statusOrDri === "number" ? statusFromDri(statusOrDri).toUpperCase() : String(statusOrDri).toUpperCase();
}

// ========================================
// LIVE SIMULATION ENGINE
// ========================================

// Shipment destinations (for movement simulation)
export const SHIPMENT_DESTINATIONS = {
  "SGP-0142": { lat: 3.0, lon: 101.4, port: "Port Klang" }, // Singapore → Port Klang
  "IND-0331": { lat: 6.9271, lon: 79.8612, port: "Colombo" }, // Mumbai → Colombo
  "SHA-2207": { lat: 35.1796, lon: 129.0756, port: "Busan" }, // Shanghai → Busan
  "HAM-1180": { lat: 51.9244, lon: 4.4777, port: "Rotterdam" }, // Hamburg → Rotterdam
  "LAX-0914": { lat: 51.9542, lon: 1.3511, port: "Felixstowe" }, // LA → Felixstowe
};

// Track simulation state per shipment
let simulationState = new Map(); // shipmentId -> { progress, eventCounter, lastDriIncrease, movedAt }

export function initializeSimulation(shipments) {
  shipments.forEach((s) => {
    if (!simulationState.has(s.id)) {
      simulationState.set(s.id, {
        progress: Math.random() * 0.3, // Start shipments at random positions
        eventCounter: 0,
        lastDriIncrease: 0,
        movedAt: Date.now(),
      });
    }
  });
}

export function interpolateLatLon(fromLat, fromLon, toLat, toLon, progress) {
  const clampedProgress = Math.max(0, Math.min(1, progress));
  return {
    lat: fromLat + (toLat - fromLat) * clampedProgress,
    lon: fromLon + (toLon - fromLon) * clampedProgress,
  };
}

export function simulateMovement(shipments) {
  const now = Date.now();
  const speedFactor = 0.00015; // Progress increment per millisecond

  return shipments.map((shipment) => {
    const state = simulationState.get(shipment.id) || {
      progress: 0.2,
      eventCounter: 0,
      lastDriIncrease: 0,
      movedAt: now,
    };

    // Update movement progress
    const timeDelta = now - state.movedAt;
    state.progress = Math.min(1, state.progress + speedFactor * timeDelta);
    state.movedAt = now;

    // Get destination
    const destination = SHIPMENT_DESTINATIONS[shipment.id];
    const originLat = shipment.lat;
    const originLon = shipment.lon;

    let newLat = originLat;
    let newLon = originLon;

    if (destination) {
      const interpolated = interpolateLatLon(
        originLat,
        originLon,
        destination.lat,
        destination.lon,
        state.progress,
      );
      newLat = interpolated.lat;
      newLon = interpolated.lon;
    }

    // Event simulation: random events trigger every 15-25 seconds
    state.eventCounter += 1;
    let driDelta = 0;
    let eventTriggered = null;

    if (state.eventCounter > 25 + Math.random() * 30) {
      // ~15-25 seconds at 1 update/sec
      const eventRand = Math.random();
      let eventDri = 0;

      if (eventRand < 0.4) {
        eventDri = 5 + Math.random() * 15; // Weather worsening
        eventTriggered = "Weather severity increased";
      } else if (eventRand < 0.7) {
        eventDri = 8 + Math.random() * 18; // Port congestion spike
        eventTriggered = "Port congestion spike detected";
      } else {
        eventDri = 6 + Math.random() * 12; // Vessel delay
        eventTriggered = "Unexpected delay reported";
      }

      driDelta = Math.round(eventDri);
      state.eventCounter = 0;
      state.lastDriIncrease = now;
    }

    simulationState.set(shipment.id, state);

    return {
      ...shipment,
      lat: newLat,
      lon: newLon,
      progress: state.progress,
      dri: Math.min(100, shipment.dri + driDelta),
      status: statusFromDri(Math.min(100, shipment.dri + driDelta)),
      eventTriggered,
      driDelta,
    };
  });
}

export function detectShipmentChanges(newShipments, oldShipments) {
  const oldMap = new Map(oldShipments.map((s) => [s.id, s]));
  const changes = new Map();

  newShipments.forEach((newS) => {
    const oldS = oldMap.get(newS.id);
    if (!oldS) {
      changes.set(newS.id, { driChanged: false, eventTriggered: null });
      return;
    }

    const driChanged = newS.dri !== oldS.dri;
    changes.set(newS.id, {
      driChanged,
      oldDri: oldS.dri,
      newDri: newS.dri,
      eventTriggered: newS.eventTriggered,
    });
  });

  return changes;
}
