import axios from "axios";

export const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api/v1";
export const DASHBOARD_SHIPMENTS_ENDPOINT =
  import.meta.env.VITE_SHIPMENTS_ENDPOINT || "/api/shipments";

const DEFAULT_USERNAME = import.meta.env.VITE_DEFAULT_USERNAME || "admin";
const DEFAULT_PASSWORD = import.meta.env.VITE_DEFAULT_PASSWORD || "admin123";
const TOKEN_STORAGE_KEY = "precursa_access_token";
const BACKEND_RETRY_MS = 15000;
const DRI_MIN = 6;
const DRI_MAX = 96;
const MAX_VEHICLES_PER_DRI = 3;

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

const GLOBAL_ROUTE_BLUEPRINTS = [
  { origin: 'Singapore', destination: 'Rotterdam' },
  { origin: 'Mumbai', destination: 'Colombo' },
  { origin: 'Shanghai', destination: 'Busan' },
  { origin: 'Hamburg', destination: 'Antwerp' },
  { origin: 'Los Angeles', destination: 'Felixstowe' },
  { origin: 'Jebel Ali', destination: 'Suez' },
  { origin: 'Chennai', destination: 'Singapore' },
  { origin: 'Hong Kong', destination: 'Shanghai' },
  { origin: 'Rotterdam', destination: 'Hamburg' },
  { origin: 'Antwerp', destination: 'Savannah' },
  { origin: 'Dubai', destination: 'Jebel Ali' },
  { origin: 'Durban', destination: 'Singapore' },
  { origin: 'Valencia', destination: 'Rotterdam' },
  { origin: 'Savannah', destination: 'Los Angeles' },
  { origin: 'Busan', destination: 'Hong Kong' },
  { origin: 'Port Klang', destination: 'Colombo' },
];

const GLOBAL_FACTOR_POOLS = [
  ['weather_severity', 'port_congestion', 'ais_anomaly'],
  ['customs_delay', 'route_variability', 'carrier_reliability'],
  ['fuel_cost_pressure', 'weather_severity', 'trend_delay'],
  ['berth_shortage', 'dock_delay', 'geo_risk'],
  ['traffic_backlog', 'vessel_speed', 'route_deviation'],
  ['storm_alert', 'port_congestion', 'weather'],
  ['inspection_delay', 'customs_delay', 'route_variability'],
  ['carrier_reliability', 'geo_risk', 'trend_congestion'],
];

const INLAND_ZONES = [
  { minLat: 10, maxLat: 34, minLon: 72, maxLon: 89 },
  { minLat: 35, maxLat: 54, minLon: 50, maxLon: 118 },
  { minLat: 26, maxLat: 48, minLon: -113, maxLon: -84 },
  { minLat: -20, maxLat: 12, minLon: -68, maxLon: -48 },
  { minLat: -30, maxLat: 16, minLon: 16, maxLon: 38 },
  { minLat: -37, maxLat: -18, minLon: 121, maxLon: 146 },
  { minLat: 45, maxLat: 55.5, minLon: 3, maxLon: 16.5 },
  { minLat: 43, maxLat: 49, minLon: 5, maxLon: 12.5 },
  { minLat: 44, maxLat: 47.8, minLon: 6.5, maxLon: 13.8 },
  { minLat: 40.5, maxLat: 46, minLon: 8, maxLon: 17.5 },
];

const SEA_NODES = [
  { lat: 25.2, lon: 55.0 },
  { lat: 26.5, lon: 50.2 },
  { lat: 24.8, lon: 57.3 },
  { lat: 20.2, lon: 38.9 },
  { lat: 16.4, lon: 41.8 },
  { lat: 13.0, lon: 42.7 },
  { lat: 30.5, lon: 32.5 },
  { lat: 35.4, lon: 14.4 },
  { lat: 37.8, lon: 15.4 },
  { lat: 43.6, lon: 7.2 },
  { lat: 44.2, lon: 8.9 },
  { lat: 43.1, lon: 5.3 },
  { lat: 45.3, lon: 12.8 },
  { lat: 50.9, lon: 1.8 },
  { lat: 51.6, lon: 3.0 },
  { lat: 53.8, lon: 8.5 },
  { lat: 54.0, lon: 10.5 },
  { lat: 31.1, lon: 121.6 },
  { lat: 22.3, lon: 114.2 },
  { lat: 1.2, lon: 103.8 },
  { lat: 6.2, lon: 80.0 },
  { lat: 12.8, lon: 80.4 },
  { lat: 19.1, lon: 72.7 },
  { lat: 51.9, lon: 4.2 },
  { lat: 53.6, lon: 9.9 },
  { lat: 52.0, lon: 2.0 },
  { lat: 33.7, lon: -118.3 },
  { lat: 32.7, lon: -117.2 },
];

function interpolate(fromLat, fromLon, toLat, toLon, progress) {
  const clamped = Math.max(0, Math.min(1, progress));
  return {
    lat: fromLat + (toLat - fromLat) * clamped,
    lon: fromLon + (toLon - fromLon) * clamped,
  };
}

function isLikelyLand(lat, lon) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return false;
  return INLAND_ZONES.some(
    (zone) => lat >= zone.minLat && lat <= zone.maxLat && lon >= zone.minLon && lon <= zone.maxLon,
  );
}

function nearestWaterPosition(targetLat, targetLon, fromLat, fromLon) {
  if (!isLikelyLand(targetLat, targetLon)) {
    return { lat: targetLat, lon: targetLon };
  }

  // First walk back toward the previous position to stay on an ocean path.
  for (let step = 1; step <= 12; step += 1) {
    const ratio = step / 12;
    const candidateLat = targetLat + (fromLat - targetLat) * ratio;
    const candidateLon = targetLon + (fromLon - targetLon) * ratio;
    if (!isLikelyLand(candidateLat, candidateLon)) {
      return { lat: candidateLat, lon: candidateLon };
    }
  }

  // If still inland, probe nearby points and choose first water coordinate.
  const radii = [0.15, 0.3, 0.5, 0.8, 1.2];
  for (const radius of radii) {
    for (let angle = 0; angle < 360; angle += 30) {
      const rad = (angle * Math.PI) / 180;
      const candidateLat = targetLat + Math.sin(rad) * radius;
      const candidateLon = targetLon + Math.cos(rad) * radius;
      if (!isLikelyLand(candidateLat, candidateLon)) {
        return { lat: candidateLat, lon: candidateLon };
      }
    }
  }

  return snapToSea(fromLat, fromLon);
}

function distanceSquared(latA, lonA, latB, lonB) {
  const dLat = latA - latB;
  const dLon = lonA - lonB;
  return dLat * dLat + dLon * dLon;
}

export function snapToSea(lat, lon) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return { lat: 1.2, lon: 103.8 };
  }

  if (!isLikelyLand(lat, lon)) {
    return { lat, lon };
  }

  let bestNode = SEA_NODES[0];
  let bestDistance = distanceSquared(lat, lon, bestNode.lat, bestNode.lon);

  for (let index = 1; index < SEA_NODES.length; index += 1) {
    const node = SEA_NODES[index];
    const score = distanceSquared(lat, lon, node.lat, node.lon);
    if (score < bestDistance) {
      bestDistance = score;
      bestNode = node;
    }
  }

  return { lat: bestNode.lat, lon: bestNode.lon };
}

function sanitizeShipmentWaterPosition(shipment) {
  const safePosition = snapToSea(Number(shipment.lat), Number(shipment.lon));
  const safeDestination = snapToSea(
    Number(shipment.destination_lat ?? safePosition.lat),
    Number(shipment.destination_lon ?? safePosition.lon),
  );

  return {
    ...shipment,
    lat: safePosition.lat,
    lon: safePosition.lon,
    destination_lat: safeDestination.lat,
    destination_lon: safeDestination.lon,
  };
}

function routeBlueprintForIndex(index) {
  return GLOBAL_ROUTE_BLUEPRINTS[index % GLOBAL_ROUTE_BLUEPRINTS.length];
}

function factorImpactForIndex(index, factorIndex, dri) {
  const base = 12 + ((index * 9 + factorIndex * 13) % 28);
  return Math.max(1, Math.round(base + (dri > 75 ? 10 : dri >= 40 ? 5 : 0)));
}

function clampDri(value) {
  return Math.max(DRI_MIN, Math.min(DRI_MAX, Math.round(Number(value ?? DRI_MIN))));
}

function findAvailableDri(baseDri, counts) {
  const base = clampDri(baseDri);

  if ((counts.get(base) || 0) < MAX_VEHICLES_PER_DRI) {
    return base;
  }

  for (let step = 1; step <= DRI_MAX - DRI_MIN; step += 1) {
    const higher = base + step;
    if (higher <= DRI_MAX && (counts.get(higher) || 0) < MAX_VEHICLES_PER_DRI) {
      return higher;
    }

    const lower = base - step;
    if (lower >= DRI_MIN && (counts.get(lower) || 0) < MAX_VEHICLES_PER_DRI) {
      return lower;
    }
  }

  return DRI_MIN;
}

function enforceDriConstraints(shipments) {
  const counts = new Map();

  return shipments.map((shipment) => {
    const balancedDri = findAvailableDri(shipment.dri, counts);
    counts.set(balancedDri, (counts.get(balancedDri) || 0) + 1);
    const status = statusFromDri(balancedDri);

    return {
      ...shipment,
      dri: balancedDri,
      status,
      statusLabel: status.toUpperCase(),
    };
  });
}

function recommendationForIndex(index, dri, destinationPort) {
  if (dri > 75) {
    return {
      route: destinationPort,
      time_saved: '8 hours',
      cost_impact: 12000 + (index % 7) * 300,
    };
  }

  if (dri >= 40) {
    return {
      route: destinationPort,
      time_saved: '4 hours',
      cost_impact: 6500 + (index % 5) * 200,
    };
  }

  return {
    route: destinationPort,
    time_saved: '1 hour',
    cost_impact: 1200 + (index % 4) * 100,
  };
}

function createCatalogShipment(index) {
  const id = `GLB-${String(index + 1).padStart(4, '0')}`;
  const blueprint = routeBlueprintForIndex(index);
  const originCoords = PORT_COORDS[blueprint.origin] || PORT_COORDS.Singapore;
  const destinationCoords = PORT_COORDS[blueprint.destination] || PORT_COORDS.Rotterdam;
  const originLat = originCoords[0] + stableOffset(id, 'origin_lat') * 0.55;
  const originLon = originCoords[1] + stableOffset(id, 'origin_lon') * 0.55;
  const destinationLat = destinationCoords[0] + stableOffset(id, 'destination_lat') * 0.45;
  const destinationLon = destinationCoords[1] + stableOffset(id, 'destination_lon') * 0.45;
  const progress = ((index % 18) + 2) / 20;
  const position = interpolate(originLat, originLon, destinationLat, destinationLon, progress);
  const safePosition = snapToSea(position.lat, position.lon);
  const safeDestination = snapToSea(destinationLat, destinationLon);
  const dri = clampDri(18 + ((index * 11) % 66) + (index % 7 === 0 ? 11 : 0));
  const status = statusFromDri(dri);
  const factorPool = GLOBAL_FACTOR_POOLS[index % GLOBAL_FACTOR_POOLS.length];

  return {
    id,
    lat: safePosition.lat,
    lon: safePosition.lon,
    origin_port: blueprint.origin,
    destination_port: blueprint.destination,
    destination_lat: safeDestination.lat,
    destination_lon: safeDestination.lon,
    progress,
    movement_mode: dri < 40 ? 'dynamic' : 'static',
    reroute_moving_until: 0,
    dri,
    status,
    statusLabel: status.toUpperCase(),
    top_factors: factorPool.slice(0, 3).map((name, factorIndex) => ({
      name,
      label: titleize(name),
      impact: factorImpactForIndex(index, factorIndex, dri),
      direction: 'increase',
    })),
    recommendation: recommendationForIndex(index, dri, blueprint.destination),
    sourceTag: 'stored catalog',
    catalog_rank: index + 1,
    live_overlay: false,
    updated_at: null,
  };
}

export const GLOBAL_FLEET_SIZE = 200;

export function generateGlobalShipCatalog(total = GLOBAL_FLEET_SIZE) {
  const baseCatalog = Array.from({ length: total }, (_, index) => createCatalogShipment(index));
  return enforceDriConstraints(baseCatalog);
}

export function overlayLiveShipments(catalogShips, liveShips) {
  if (!liveShips?.length) {
    return enforceDriConstraints(catalogShips).map(sanitizeShipmentWaterPosition);
  }

  const merged = catalogShips.map((ship) => ({ ...ship }));
  const overlayCount = Math.min(liveShips.length, merged.length);

  for (let index = 0; index < overlayCount; index += 1) {
    const liveShip = liveShips[index];
    const catalogShip = merged[index];
    merged[index] = {
      ...catalogShip,
      ...liveShip,
      id: liveShip.id || catalogShip.id,
      lat: Number(liveShip.lat ?? catalogShip.lat),
      lon: Number(liveShip.lon ?? catalogShip.lon),
      destination_lat: Number(liveShip.destination_lat ?? catalogShip.destination_lat),
      destination_lon: Number(liveShip.destination_lon ?? catalogShip.destination_lon),
      sourceTag: 'live api',
      live_overlay: true,
      catalog_rank: catalogShip.catalog_rank,
      fallback_catalog_sizes: liveShip.fallback_catalog_sizes || catalogShip.fallback_catalog_sizes,
    };
  }

  return enforceDriConstraints(merged).map(sanitizeShipmentWaterPosition);
}

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

export async function ensureAccessToken(forceRefresh = false) {
  if (forceRefresh) {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }

  const cachedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  if (cachedToken && !forceRefresh) {
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

async function getWithAuthRetry(url, token) {
  try {
    return await axios.get(url, { headers: authHeaders(token) });
  } catch (error) {
    if (error?.response?.status !== 401) {
      throw error;
    }

    const freshToken = await ensureAccessToken(true);
    return axios.get(url, { headers: authHeaders(freshToken) });
  }
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
  const dri = clampDri(raw.dri ?? raw.provisional_dri ?? raw.dri_score ?? DRI_MIN);
  const [rawLat, rawLon] = coordsForShipment(raw, id);
  const safePosition = snapToSea(rawLat, rawLon);
  const topFactorsSource = raw.top_factors?.length ? raw.top_factors : factorsFromSnapshot(raw);
  const topFactors = (topFactorsSource.length ? topFactorsSource : FALLBACK_SHIPMENTS[index % FALLBACK_SHIPMENTS.length].top_factors)
    .slice(0, 3)
    .map(normalizeFactor);
  const status = String(raw.status || raw.dri_level || statusFromDri(dri)).toLowerCase();
  const featureVector = raw.feature_vector || {};

  return {
    id,
    lat: safePosition.lat,
    lon: safePosition.lon,
    dri,
    status,
    statusLabel: status.toUpperCase(),
    top_factors: topFactors,
    recommendation: {
      route: raw.recommendation?.route || featureVector.recommended_route || "Port Klang",
      time_saved: raw.recommendation?.time_saved || featureVector.time_saved || (dri > 75 ? "8 hours" : "3 hours"),
      cost_impact: Number(raw.recommendation?.cost_impact ?? featureVector.cost_impact ?? (dri > 75 ? 12000 : 4500)),
    },
    fallback_catalog_sizes: {
      weather: Number(raw.fallback_catalog_sizes?.weather ?? 100),
      news: Number(raw.fallback_catalog_sizes?.news ?? 100),
      ais: Number(raw.fallback_catalog_sizes?.ais ?? 200),
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

  try {
    const response = await getWithAuthRetry(DASHBOARD_SHIPMENTS_ENDPOINT, token);
    return {
      shipments: response.data.map(normalizeShipment),
      usingFallback: false,
      source: DASHBOARD_SHIPMENTS_ENDPOINT,
    };
  } catch {
    try {
      const response = await getWithAuthRetry(`${API_PREFIX}/state/snapshots?limit=50`, token);
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

  const movedShipments = shipments.map((shipment) => {
    const state = simulationState.get(shipment.id) || {
      progress: 0.2,
      direction: 1,
      eventCounter: 0,
      lastDriIncrease: 0,
      movedAt: now,
    };

    const rerouteMovingUntil = Number(shipment.reroute_moving_until || 0);
    const isRerouteActive = rerouteMovingUntil > now;
    const isLowDriDynamic = Number(shipment.dri) < 40;
    const shouldMove = isLowDriDynamic || isRerouteActive;

    // Update movement progress only for dynamic ships.
    if (shouldMove) {
      const timeDelta = now - state.movedAt;
      state.progress += speedFactor * timeDelta * state.direction;
      if (state.progress >= 1) {
        state.progress = 1;
        state.direction = -1;
      } else if (state.progress <= 0) {
        state.progress = 0;
        state.direction = 1;
      }
    }
    state.movedAt = now;

    // Get destination
    const destination =
      SHIPMENT_DESTINATIONS[shipment.id] ||
      (Number.isFinite(Number(shipment.destination_lat)) && Number.isFinite(Number(shipment.destination_lon))
        ? { lat: Number(shipment.destination_lat), lon: Number(shipment.destination_lon) }
        : null);
    const originLat = shipment.lat;
    const originLon = shipment.lon;

    let newLat = originLat;
    let newLon = originLon;

    if (shouldMove && destination) {
      const interpolated = interpolateLatLon(
        originLat,
        originLon,
        destination.lat,
        destination.lon,
        state.progress,
      );
      const waterPosition = nearestWaterPosition(interpolated.lat, interpolated.lon, originLat, originLon);
      newLat = waterPosition.lat;
      newLon = waterPosition.lon;
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

    const nextDri = clampDri(shipment.dri + driDelta);

    const safePosition = snapToSea(newLat, newLon);

    return {
      ...shipment,
      lat: safePosition.lat,
      lon: safePosition.lon,
      progress: state.progress,
      movement_mode: shouldMove ? 'dynamic' : 'static',
      dri: nextDri,
      status: statusFromDri(nextDri),
      eventTriggered,
      driDelta,
    };
  });

  return enforceDriConstraints(movedShipments);
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
