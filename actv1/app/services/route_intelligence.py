from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx
import pulp

from app.db.models import ShipmentSnapshot

PORTS: dict[str, dict[str, Any]] = {
    "Mumbai": {"country": "IN", "cold_chain": True},
    "Colombo": {"country": "LK", "cold_chain": True},
    "Singapore": {"country": "SG", "cold_chain": True},
    "Port Klang": {"country": "MY", "cold_chain": True},
    "Jebel Ali": {"country": "AE", "cold_chain": True},
    "Suez": {"country": "EG", "cold_chain": False},
    "Rotterdam": {"country": "NL", "cold_chain": True},
    "Hamburg": {"country": "DE", "cold_chain": True},
    "Shanghai": {"country": "CN", "cold_chain": True},
    "Cape Town": {"country": "ZA", "cold_chain": False},
}

EDGES: tuple[tuple[str, str, dict[str, float]], ...] = (
    ("Mumbai", "Colombo", {"cost_usd": 1800, "eta_hours": 44, "risk": 0.25, "carbon_kg": 900}),
    ("Colombo", "Singapore", {"cost_usd": 2100, "eta_hours": 50, "risk": 0.22, "carbon_kg": 1050}),
    ("Singapore", "Suez", {"cost_usd": 3900, "eta_hours": 96, "risk": 0.42, "carbon_kg": 2200}),
    ("Suez", "Rotterdam", {"cost_usd": 2400, "eta_hours": 62, "risk": 0.35, "carbon_kg": 1280}),
    ("Rotterdam", "Hamburg", {"cost_usd": 700, "eta_hours": 14, "risk": 0.10, "carbon_kg": 280}),
    ("Mumbai", "Jebel Ali", {"cost_usd": 2200, "eta_hours": 56, "risk": 0.26, "carbon_kg": 1100}),
    ("Jebel Ali", "Suez", {"cost_usd": 2600, "eta_hours": 70, "risk": 0.33, "carbon_kg": 1320}),
    ("Mumbai", "Cape Town", {"cost_usd": 4600, "eta_hours": 128, "risk": 0.31, "carbon_kg": 2820}),
    ("Cape Town", "Rotterdam", {"cost_usd": 2900, "eta_hours": 88, "risk": 0.21, "carbon_kg": 1680}),
    ("Shanghai", "Singapore", {"cost_usd": 2500, "eta_hours": 66, "risk": 0.36, "carbon_kg": 1350}),
    ("Port Klang", "Suez", {"cost_usd": 3600, "eta_hours": 90, "risk": 0.37, "carbon_kg": 1980}),
    ("Singapore", "Port Klang", {"cost_usd": 800, "eta_hours": 18, "risk": 0.15, "carbon_kg": 330}),
    ("Shanghai", "Port Klang", {"cost_usd": 2400, "eta_hours": 58, "risk": 0.31, "carbon_kg": 1200}),
)

TARIFF_RATE_BY_COUNTRY: dict[str, float] = {
    "CN": 0.32,
    "IN": 0.08,
    "SG": 0.04,
    "AE": 0.06,
    "MY": 0.07,
    "ZA": 0.05,
    "EG": 0.09,
    "NL": 0.04,
    "DE": 0.04,
    "LK": 0.06,
}

POLICY_RISK_PORT_PENALTY: dict[str, float] = {
    "Suez": 1400.0,
    "Shanghai": 900.0,
}

GLOBAL_SANCTIONED_PORTS: set[str] = set()


@dataclass(frozen=True)
class RouteOption:
    path: list[str]
    cost_usd: float
    eta_hours: float
    risk_score: float
    carbon_kg: float
    tariff_delta_usd: float
    policy_penalty_usd: float
    composite_score: float


@dataclass(frozen=True)
class RejectedRoute:
    path: list[str]
    reasons: list[str]


@dataclass(frozen=True)
class RoutePlanResult:
    shipment_key: str
    source_port: str
    destination_port: str
    solver_status: str
    selected_path: list[str] | None
    top_routes: list[RouteOption]
    rejected_routes: list[RejectedRoute]
    message: str


class RouteIntelligenceService:
    def __init__(self) -> None:
        self._graph = self._build_graph()

    @staticmethod
    def _build_graph() -> nx.Graph:
        graph = nx.Graph()

        for port_name, attrs in PORTS.items():
            graph.add_node(port_name, **attrs)

        for source, destination, attrs in EDGES:
            graph.add_edge(source, destination, **attrs)

        return graph

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_blocked_ports(value: Any) -> set[str]:
        if isinstance(value, list):
            return {str(item) for item in value if str(item).strip()}
        return set()

    @staticmethod
    def _edge_priority_weight(data: dict[str, Any]) -> float:
        return (
            float(data.get("cost_usd", 0.0))
            + (float(data.get("eta_hours", 0.0)) * 12.0)
            + (float(data.get("risk", 0.0)) * 1800.0)
        )

    def _candidate_paths(self, source_port: str, destination_port: str, max_paths: int) -> list[list[str]]:
        try:
            iterator = nx.shortest_simple_paths(
                self._graph,
                source_port,
                destination_port,
                weight=self._edge_priority_weight,
            )
        except nx.NetworkXNoPath:
            return []

        paths: list[list[str]] = []
        for path in iterator:
            paths.append(path)
            if len(paths) >= max_paths:
                break

        return paths

    def _summarize_route(
        self,
        path: list[str],
        feature_vector: dict[str, Any],
    ) -> RouteOption:
        cost_usd = 0.0
        eta_hours = 0.0
        risk_score = 0.0
        carbon_kg = 0.0

        for source, destination in zip(path, path[1:], strict=True):
            edge = self._graph[source][destination]
            cost_usd += float(edge["cost_usd"])
            eta_hours += float(edge["eta_hours"])
            risk_score += float(edge["risk"])
            carbon_kg += float(edge["carbon_kg"])

        risk_score = round(risk_score / max(1, len(path) - 1), 6)

        cargo_value_usd = self._safe_float(feature_vector.get("cargo_value_usd"), default=50000.0)
        origin_country = str(feature_vector.get("origin_country", "")).upper()
        base_rate = TARIFF_RATE_BY_COUNTRY.get(origin_country, 0.05)

        transit_countries = [
            str(PORTS[port]["country"]).upper()
            for port in path[1:-1]
            if port in PORTS
        ]
        transit_rate = 0.0
        if transit_countries:
            transit_rate = sum(TARIFF_RATE_BY_COUNTRY.get(country, 0.03) for country in transit_countries)
            transit_rate /= len(transit_countries)

        tariff_delta_usd = cargo_value_usd * (base_rate + (transit_rate * 0.5))

        policy_penalty_usd = sum(POLICY_RISK_PORT_PENALTY.get(port, 0.0) for port in path)

        tariff_weight = self._safe_float(feature_vector.get("tariff_priority_weight"), default=1.0)
        policy_weight = self._safe_float(feature_vector.get("policy_priority_weight"), default=1.0)

        composite_score = (
            cost_usd
            + (eta_hours * 14.0)
            + (risk_score * 2200.0)
            + (carbon_kg * 0.18)
            + (tariff_delta_usd * tariff_weight)
            + (policy_penalty_usd * policy_weight)
        )

        return RouteOption(
            path=path,
            cost_usd=round(cost_usd, 2),
            eta_hours=round(eta_hours, 2),
            risk_score=round(risk_score, 6),
            carbon_kg=round(carbon_kg, 2),
            tariff_delta_usd=round(tariff_delta_usd, 2),
            policy_penalty_usd=round(policy_penalty_usd, 2),
            composite_score=round(composite_score, 2),
        )

    def _hard_constraint_reasons(
        self,
        route: RouteOption,
        feature_vector: dict[str, Any],
    ) -> list[str]:
        reasons: list[str] = []

        blocked_ports = GLOBAL_SANCTIONED_PORTS | self._parse_blocked_ports(
            feature_vector.get("sanctioned_ports")
        )
        violating_ports = [port for port in route.path if port in blocked_ports]
        if violating_ports:
            reasons.append(
                "Route contains sanctioned/blocked ports: " + ", ".join(violating_ports)
            )

        sla_hours = self._safe_float(feature_vector.get("sla_hours"), default=0.0)
        if sla_hours > 0 and route.eta_hours > sla_hours:
            reasons.append(
                f"Route ETA {route.eta_hours:.1f}h exceeds SLA limit {sla_hours:.1f}h"
            )

        max_risk_tolerance = self._safe_float(feature_vector.get("max_risk_tolerance"), default=0.0)
        if max_risk_tolerance > 0 and route.risk_score > max_risk_tolerance:
            reasons.append(
                f"Route risk {route.risk_score:.3f} exceeds tolerance {max_risk_tolerance:.3f}"
            )

        requires_cold_chain = feature_vector.get("temp_requirement_celsius") is not None
        if requires_cold_chain:
            missing_cold_chain = [
                port
                for port in route.path
                if not bool(self._graph.nodes[port].get("cold_chain", False))
            ]
            if missing_cold_chain:
                reasons.append(
                    "Cold-chain requirement violated at ports: "
                    + ", ".join(missing_cold_chain)
                )

        return reasons

    @staticmethod
    def _solve_best_route_index(route_options: list[RouteOption], feasible_indices: list[int]) -> tuple[str, int | None]:
        if not route_options:
            return "no-candidates", None

        problem = pulp.LpProblem("reroute_selection", pulp.LpMinimize)
        variables = {
            index: pulp.LpVariable(f"route_{index}", cat="Binary")
            for index in range(len(route_options))
        }

        problem += pulp.lpSum(
            route_options[index].composite_score * variables[index]
            for index in variables
        )
        problem += pulp.lpSum(variables.values()) == 1

        feasible_set = set(feasible_indices)
        for index, variable in variables.items():
            if index not in feasible_set:
                problem += variable <= 0

        try:
            status_code = problem.solve(pulp.PULP_CBC_CMD(msg=False))
        except pulp.PulpError:
            if feasible_indices:
                return "fallback-feasible", min(
                    feasible_indices,
                    key=lambda idx: route_options[idx].composite_score,
                )
            return "fallback-infeasible", None

        status_name = pulp.LpStatus.get(status_code, "Unknown")
        if status_name != "Optimal":
            return status_name.lower(), None

        for index, variable in variables.items():
            if variable.value() and variable.value() > 0.5:
                return "optimal", index

        return "optimal-no-selection", None

    def reroute_shipment(
        self,
        snapshot: ShipmentSnapshot,
        max_paths: int = 12,
        top_k: int = 3,
    ) -> RoutePlanResult:
        feature_vector = snapshot.feature_vector if isinstance(snapshot.feature_vector, dict) else {}

        source_port = str(feature_vector.get("origin_port") or "").strip()
        destination_port = str(feature_vector.get("destination_port") or "").strip()

        if not source_port or not destination_port:
            raise ValueError("Missing origin_port or destination_port in shipment feature vector")

        if source_port not in self._graph.nodes:
            raise ValueError(f"Unknown origin_port '{source_port}'")

        if destination_port not in self._graph.nodes:
            raise ValueError(f"Unknown destination_port '{destination_port}'")

        candidate_paths = self._candidate_paths(source_port, destination_port, max_paths=max_paths)
        if not candidate_paths:
            return RoutePlanResult(
                shipment_key=snapshot.shipment_key,
                source_port=source_port,
                destination_port=destination_port,
                solver_status="no-path",
                selected_path=None,
                top_routes=[],
                rejected_routes=[],
                message="No candidate paths available between origin and destination",
            )

        route_options: list[RouteOption] = []
        rejected_routes: list[RejectedRoute] = []
        feasible_indices: list[int] = []

        for path in candidate_paths:
            option = self._summarize_route(path=path, feature_vector=feature_vector)
            reasons = self._hard_constraint_reasons(option, feature_vector=feature_vector)

            route_options.append(option)
            index = len(route_options) - 1
            if reasons:
                rejected_routes.append(RejectedRoute(path=path, reasons=reasons))
            else:
                feasible_indices.append(index)

        solver_status, selected_index = self._solve_best_route_index(route_options, feasible_indices)

        top_routes = [route_options[index] for index in feasible_indices]
        top_routes.sort(key=lambda route: route.composite_score)
        top_routes = top_routes[: max(1, min(top_k, len(top_routes)))]

        selected_path = None
        if selected_index is not None:
            selected_path = route_options[selected_index].path

        if not top_routes:
            return RoutePlanResult(
                shipment_key=snapshot.shipment_key,
                source_port=source_port,
                destination_port=destination_port,
                solver_status=solver_status,
                selected_path=selected_path,
                top_routes=[],
                rejected_routes=rejected_routes,
                message="All candidate routes were rejected by hard constraints",
            )

        return RoutePlanResult(
            shipment_key=snapshot.shipment_key,
            source_port=source_port,
            destination_port=destination_port,
            solver_status=solver_status,
            selected_path=selected_path,
            top_routes=top_routes,
            rejected_routes=rejected_routes,
            message="Feasible reroute options generated",
        )


route_intelligence_service = RouteIntelligenceService()
