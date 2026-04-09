from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
import heapq
import math
from typing import Deque, Dict, List, Optional, Tuple


SLOT_WINDOWS: Dict[str, Tuple[int, int]] = {
    "09:00-10:00": (9 * 60, 10 * 60),
    "10:00-11:00": (10 * 60, 11 * 60),
    "11:00-12:00": (11 * 60, 12 * 60),
    "12:00-13:00": (12 * 60, 13 * 60),
    "13:00-14:00": (13 * 60, 14 * 60),
}
SLOT_LABELS = list(SLOT_WINDOWS.keys())
SLOT_ORDER = {slot: index for index, slot in enumerate(SLOT_LABELS)}
PRIORITY_MAP = {
    "urgent": 1,
    "high": 2,
    "normal": 3,
    "low": 4,
}
DRIVER_STATUS_OPTIONS = ["Idle", "Offline"]
ACTIVE_ORDER_STATUSES = {"Assigned", "In Transit"}
MINUTES_PER_KM = 4
SERVICE_BUFFER_MINUTES = 8


def slot_duration(slot_label: str) -> int:
    start, end = SLOT_WINDOWS[slot_label]
    return end - start


def estimate_minutes(distance: float) -> int:
    return int(round(distance * MINUTES_PER_KM))


@dataclass(order=True)
class DeliveryOrder:
    sort_index: Tuple[int, int, int] = field(init=False, repr=False)
    priority_rank: int
    slot_rank: int
    sequence_number: int
    order_id: str = field(compare=False)
    customer_name: str = field(compare=False)
    source: str = field(compare=False)
    destination: str = field(compare=False)
    package_type: str = field(compare=False)
    priority_label: str = field(compare=False)
    requested_slot: str = field(compare=False)
    slot_start_minutes: int = field(compare=False)
    slot_end_minutes: int = field(compare=False)
    estimated_delivery_minutes: int = field(default=0, compare=False)
    route_distance: float = field(default=0, compare=False)
    route_path: List[str] = field(default_factory=list, compare=False)
    pickup_distance: float = field(default=0, compare=False)
    pickup_path: List[str] = field(default_factory=list, compare=False)
    projected_total_minutes: int = field(default=0, compare=False)
    status: str = field(default="Pending", compare=False)
    assigned_driver_id: Optional[str] = field(default=None, compare=False)
    scheduling_note: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        self.sort_index = (self.priority_rank, self.slot_rank, self.sequence_number)


@dataclass
class Driver:
    driver_id: str
    name: str
    current_location: str
    available_slots: List[str]
    availability_status: str = "Idle"
    active_slot_assignments: Dict[str, str] = field(default_factory=dict)
    slot_history: Dict[str, str] = field(default_factory=dict)

    def free_slots(self) -> List[str]:
        return [slot for slot in self.available_slots if slot not in self.active_slot_assignments]


class CityGraph:
    def __init__(self) -> None:
        # Adjacency list keeps the road network compact and easy to explain in viva.
        self.adjacency_list: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

    def add_location(self, location: str) -> bool:
        normalized_location = location.strip()
        if not normalized_location:
            return False
        self.adjacency_list[normalized_location]
        return True

    def has_location(self, location: str) -> bool:
        return location in self.adjacency_list

    def add_road(self, location_a: str, location_b: str, distance: int) -> bool:
        if distance <= 0 or location_a == location_b:
            return False
        if not self.has_location(location_a) or not self.has_location(location_b):
            return False

        self._upsert_edge(location_a, location_b, distance)
        self._upsert_edge(location_b, location_a, distance)
        return True

    def _upsert_edge(self, source: str, destination: str, distance: int) -> None:
        neighbors = self.adjacency_list[source]
        for index, (neighbor, _) in enumerate(neighbors):
            if neighbor == destination:
                neighbors[index] = (destination, distance)
                return
        neighbors.append((destination, distance))

    def shortest_path(self, start: str, end: str) -> Tuple[float, List[str]]:
        if start not in self.adjacency_list or end not in self.adjacency_list:
            return float("inf"), []

        distances = {node: float("inf") for node in self.adjacency_list}
        previous: Dict[str, Optional[str]] = {node: None for node in self.adjacency_list}
        distances[start] = 0

        # Heap-based Dijkstra keeps path calculation efficient for repeated scheduling checks.
        min_heap: List[Tuple[float, str]] = [(0, start)]

        while min_heap:
            current_distance, current_node = heapq.heappop(min_heap)
            if current_distance > distances[current_node]:
                continue
            if current_node == end:
                break

            for neighbor, weight in self.adjacency_list[current_node]:
                new_distance = current_distance + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current_node
                    heapq.heappush(min_heap, (new_distance, neighbor))

        if distances[end] == float("inf"):
            return float("inf"), []

        path: List[str] = []
        current: Optional[str] = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return distances[end], path

    def list_locations(self) -> List[str]:
        return sorted(self.adjacency_list.keys())

    def list_roads(self) -> List[Tuple[str, str, int]]:
        roads: List[Tuple[str, str, int]] = []
        seen = set()
        for source, neighbors in self.adjacency_list.items():
            for destination, distance in neighbors:
                edge_key = tuple(sorted((source, destination)))
                if edge_key in seen:
                    continue
                seen.add(edge_key)
                roads.append((source, destination, distance))
        return sorted(roads)


class DeliveryManagementSystem:
    PRIORITY_MAP = PRIORITY_MAP
    SLOT_WINDOWS = SLOT_WINDOWS
    SLOT_LABELS = SLOT_LABELS
    DRIVER_STATUS_OPTIONS = DRIVER_STATUS_OPTIONS

    def __init__(self) -> None:
        self.city_graph = CityGraph()

        # Heap = priority queue. Orders stay here until the scheduler finds a feasible assignment.
        self.pending_orders: List[DeliveryOrder] = []

        # Hash maps give O(1) average lookup for order/driver updates.
        self.order_lookup: Dict[str, DeliveryOrder] = {}
        self.drivers: Dict[str, Driver] = {}

        # FIFO queues track completed deliveries and slot-based waiting orders.
        self.completed_deliveries: Deque[DeliveryOrder] = deque()
        self.waiting_queues: Dict[str, Deque[str]] = {slot: deque() for slot in SLOT_LABELS}
        self.waiting_membership: set[str] = set()
        self.activity_log: Deque[str] = deque(maxlen=12)

        self.order_counter = 0
        self.last_route_info: Optional[Dict[str, object]] = None

    def _log_event(self, message: str) -> None:
        self.activity_log.appendleft(message)

    def _validate_slot(self, slot_label: str) -> bool:
        return slot_label in SLOT_WINDOWS

    def _update_driver_status(self, driver: Driver) -> None:
        if driver.availability_status == "Offline":
            return
        active_count = self.get_driver_active_count(driver)
        driver.availability_status = "Busy" if active_count else "Idle"

    def _refresh_order_route_metrics(self, order: DeliveryOrder) -> None:
        distance, path = self.city_graph.shortest_path(order.source, order.destination)
        order.route_distance = 0 if not path else distance
        order.route_path = path
        order.estimated_delivery_minutes = 0 if not path else estimate_minutes(distance)

    def _remove_from_waiting_queue(self, order: DeliveryOrder) -> None:
        if order.order_id not in self.waiting_membership:
            return

        slot_queue = self.waiting_queues[order.requested_slot]
        try:
            slot_queue.remove(order.order_id)
        except ValueError:
            pass
        self.waiting_membership.discard(order.order_id)

    def _mark_waiting(self, order: DeliveryOrder, note: str) -> None:
        previous_status = order.status
        previous_note = order.scheduling_note
        order.status = "Waiting for Slot"
        order.scheduling_note = note
        if order.order_id not in self.waiting_membership:
            self.waiting_queues[order.requested_slot].append(order.order_id)
            self.waiting_membership.add(order.order_id)
        if previous_status != order.status or previous_note != note:
            self._log_event(f"{order.order_id} moved to waiting queue for {order.requested_slot}.")

    def _set_delayed(self, order: DeliveryOrder, note: str) -> None:
        if order.status != "Delayed" or order.scheduling_note != note:
            self._log_event(f"{order.order_id} delayed because {note.lower()}")
        order.status = "Delayed"
        order.scheduling_note = note
        self._remove_from_waiting_queue(order)

    def _get_driver_reference_location(self, driver: Driver, slot_label: str) -> str:
        current_slot_rank = SLOT_ORDER[slot_label]
        earlier_slots = [
            slot for slot in driver.slot_history if SLOT_ORDER[slot] < current_slot_rank
        ]
        if not earlier_slots:
            return driver.current_location

        latest_slot = max(earlier_slots, key=lambda slot: SLOT_ORDER[slot])
        latest_order = self.order_lookup.get(driver.slot_history[latest_slot])
        if latest_order is None:
            return driver.current_location
        return latest_order.destination

    def get_driver_active_count(self, driver: Driver) -> int:
        return sum(
            1
            for order_id in driver.active_slot_assignments.values()
            if self.order_lookup.get(order_id)
            and self.order_lookup[order_id].status in ACTIVE_ORDER_STATUSES
        )

    def _build_waiting_reason(self, order: DeliveryOrder) -> str:
        slot_name = order.requested_slot
        if order.route_path and order.estimated_delivery_minutes > slot_duration(slot_name):
            return (
                f"delivery ETA {order.estimated_delivery_minutes} min exceeds "
                f"the {slot_duration(slot_name)} min slot"
            )

        free_slot_drivers = [
            driver
            for driver in self.drivers.values()
            if driver.availability_status != "Offline"
            and slot_name in driver.available_slots
            and slot_name not in driver.active_slot_assignments
        ]
        if not free_slot_drivers:
            return f"no driver has a free {slot_name} slot"

        return f"no eligible driver can reach {order.source} and finish within {slot_name}"

    def _select_best_driver(self, order: DeliveryOrder) -> Optional[Dict[str, object]]:
        candidates: List[Dict[str, object]] = []

        for driver in self.drivers.values():
            if driver.availability_status == "Offline":
                continue
            if order.requested_slot not in driver.available_slots:
                continue
            if order.requested_slot in driver.active_slot_assignments:
                continue

            reference_location = self._get_driver_reference_location(driver, order.requested_slot)
            pickup_distance, pickup_path = self.city_graph.shortest_path(reference_location, order.source)
            if not pickup_path:
                continue

            pickup_minutes = estimate_minutes(pickup_distance)
            projected_total = pickup_minutes + order.estimated_delivery_minutes + SERVICE_BUFFER_MINUTES
            if projected_total > slot_duration(order.requested_slot):
                continue

            workload = self.get_driver_active_count(driver)
            # Candidate scoring keeps the dispatch rule easy to explain:
            # nearest feasible pickup first, then least workload, then stable ID tie-break.
            candidates.append(
                {
                    "driver": driver,
                    "reference_location": reference_location,
                    "pickup_distance": pickup_distance,
                    "pickup_path": pickup_path,
                    "pickup_minutes": pickup_minutes,
                    "projected_total": projected_total,
                    "workload": workload,
                    "score": (pickup_distance, workload, driver.driver_id),
                }
            )

        if not candidates:
            return None
        return min(candidates, key=lambda candidate: candidate["score"])

    def _store_route_focus(
        self,
        title: str,
        path: List[str],
        distance: float,
        estimated_minutes: int,
        *,
        driver_name: Optional[str] = None,
        slot_label: Optional[str] = None,
        pickup_path: Optional[List[str]] = None,
        pickup_distance: Optional[float] = None,
        projected_total: Optional[int] = None,
    ) -> None:
        self.last_route_info = {
            "title": title,
            "path": path,
            "distance": int(distance),
            "estimated_minutes": estimated_minutes,
            "driver_name": driver_name,
            "slot_label": slot_label,
            "pickup_path": pickup_path or [],
            "pickup_distance": 0 if pickup_distance is None else int(pickup_distance),
            "projected_total": projected_total or estimated_minutes,
        }

    def _apply_assignment(self, order: DeliveryOrder, candidate: Dict[str, object]) -> str:
        driver = candidate["driver"]

        order.assigned_driver_id = driver.driver_id
        order.status = "Assigned"
        order.pickup_distance = candidate["pickup_distance"]
        order.pickup_path = candidate["pickup_path"]
        order.projected_total_minutes = candidate["projected_total"]
        order.scheduling_note = (
            f"Scheduled with {driver.name} in {order.requested_slot}. "
            f"Pickup {int(order.pickup_distance)} km, delivery {int(order.route_distance)} km."
        )

        driver.active_slot_assignments[order.requested_slot] = order.order_id
        driver.slot_history[order.requested_slot] = order.order_id
        self._update_driver_status(driver)
        self._remove_from_waiting_queue(order)

        self._store_route_focus(
            f"Assigned {order.order_id}",
            order.route_path,
            order.route_distance,
            order.estimated_delivery_minutes,
            driver_name=driver.name,
            slot_label=order.requested_slot,
            pickup_path=order.pickup_path,
            pickup_distance=order.pickup_distance,
            projected_total=order.projected_total_minutes,
        )
        self._log_event(
            f"{order.order_id} assigned to {driver.name} for {order.requested_slot} "
            f"using shortest route {int(order.route_distance)} km."
        )
        return (
            f"Assigned {order.order_id} to {driver.name} for {order.requested_slot}. "
            f"Pickup {int(order.pickup_distance)} km, delivery {int(order.route_distance)} km, "
            f"total ETA {order.projected_total_minutes} min."
        )

    def _attempt_schedule_order(self, order: DeliveryOrder) -> Tuple[bool, str]:
        self._refresh_order_route_metrics(order)

        if not order.route_path:
            note = "no connected route exists between source and destination"
            self._set_delayed(order, note)
            return False, f"{order.order_id} delayed because {note}."

        candidate = self._select_best_driver(order)
        if candidate is None:
            note = self._build_waiting_reason(order)
            self._mark_waiting(order, note)
            return False, f"{order.order_id} waiting: {note}."

        return True, self._apply_assignment(order, candidate)

    def _run_scheduler(self, limit: Optional[int] = None) -> Tuple[int, List[str]]:
        if not self.pending_orders:
            return 0, ["No pending orders are currently queued."]

        extracted_orders: List[DeliveryOrder] = []
        while self.pending_orders:
            extracted_orders.append(heapq.heappop(self.pending_orders))

        messages: List[str] = []
        assigned_count = 0
        requeue: List[DeliveryOrder] = []

        for order in extracted_orders:
            if order.status in {"Assigned", "In Transit", "Completed"}:
                continue
            if limit is not None and assigned_count >= limit:
                requeue.append(order)
                continue

            assigned, message = self._attempt_schedule_order(order)
            messages.append(message)
            if assigned:
                assigned_count += 1
            else:
                requeue.append(order)

        for order in requeue:
            heapq.heappush(self.pending_orders, order)

        return assigned_count, messages

    def auto_schedule_pending_orders(self) -> str:
        assigned_count, messages = self._run_scheduler()
        if assigned_count:
            return f"Auto scheduler assigned {assigned_count} order(s)."
        if messages:
            return messages[0]
        return "No pending orders are currently queued."

    def add_driver(
        self,
        driver_id: str,
        name: str,
        current_location: str,
        available_slots: Optional[List[str]] = None,
        availability_status: str = "Idle",
    ) -> str:
        driver_id = driver_id.strip()
        name = name.strip()
        current_location = current_location.strip()
        availability_status = availability_status.strip().title() or "Idle"

        if not driver_id or not name:
            return "Driver ID and name cannot be empty."
        if driver_id in self.drivers:
            return f"Driver {driver_id} already exists."
        if not self.city_graph.has_location(current_location):
            return f"Location {current_location} does not exist."
        if availability_status not in DRIVER_STATUS_OPTIONS:
            return f"Invalid driver status. Use one of: {', '.join(DRIVER_STATUS_OPTIONS)}."

        slot_pool = available_slots or SLOT_LABELS
        cleaned_slots = []
        for slot_label in slot_pool:
            if slot_label in SLOT_WINDOWS and slot_label not in cleaned_slots:
                cleaned_slots.append(slot_label)
        if not cleaned_slots:
            return "At least one valid driver slot is required."

        self.drivers[driver_id] = Driver(
            driver_id=driver_id,
            name=name,
            current_location=current_location,
            available_slots=cleaned_slots,
            availability_status=availability_status,
        )
        self._log_event(f"Driver {driver_id} registered at {current_location}.")

        scheduler_summary = self.auto_schedule_pending_orders()
        if scheduler_summary.startswith("Auto scheduler assigned"):
            return f"Driver {driver_id} registered successfully. {scheduler_summary}"
        return f"Driver {driver_id} registered successfully."

    def add_location(self, location: str) -> str:
        location = location.strip()
        if not location:
            return "Location name cannot be empty."
        if self.city_graph.has_location(location):
            return f"Location {location} already exists."

        self.city_graph.add_location(location)
        self._log_event(f"Location {location} added to the network.")
        return f"Location {location} added successfully."

    def add_road(self, location_a: str, location_b: str, distance: int) -> str:
        if not self.city_graph.has_location(location_a) or not self.city_graph.has_location(location_b):
            return "Both locations must exist before adding a road."
        if distance <= 0:
            return "Distance must be greater than 0."
        if location_a == location_b:
            return "A road needs two different locations."

        self.city_graph.add_road(location_a, location_b, distance)
        self._log_event(f"Road {location_a} <-> {location_b} added with weight {distance}.")

        scheduler_summary = self.auto_schedule_pending_orders()
        if scheduler_summary.startswith("Auto scheduler assigned"):
            return (
                f"Road added between {location_a} and {location_b} with distance {distance} km. "
                f"{scheduler_summary}"
            )
        return f"Road added between {location_a} and {location_b} with distance {distance} km."

    def create_order(
        self,
        order_id: str,
        customer_name: str,
        source: str,
        destination: str,
        package_type: str,
        priority: str,
        requested_slot: str,
    ) -> str:
        order_id = order_id.strip()
        customer_name = customer_name.strip()
        source = source.strip()
        destination = destination.strip()
        package_type = package_type.strip()
        normalized_priority = priority.strip().lower()
        requested_slot = requested_slot.strip()

        if not all([order_id, customer_name, source, destination, package_type, requested_slot]):
            return "Order details cannot be empty."
        if order_id in self.order_lookup:
            return f"Order {order_id} already exists."
        if not self.city_graph.has_location(source) or not self.city_graph.has_location(destination):
            return "Source and destination must be valid locations."
        if normalized_priority not in PRIORITY_MAP:
            return f"Invalid priority. Use one of: {', '.join(PRIORITY_MAP.keys())}."
        if not self._validate_slot(requested_slot):
            return f"Invalid slot. Use one of: {', '.join(SLOT_LABELS)}."

        slot_start, slot_end = SLOT_WINDOWS[requested_slot]
        self.order_counter += 1
        order = DeliveryOrder(
            priority_rank=PRIORITY_MAP[normalized_priority],
            slot_rank=SLOT_ORDER[requested_slot],
            sequence_number=self.order_counter,
            order_id=order_id,
            customer_name=customer_name,
            source=source,
            destination=destination,
            package_type=package_type,
            priority_label=normalized_priority.title(),
            requested_slot=requested_slot,
            slot_start_minutes=slot_start,
            slot_end_minutes=slot_end,
        )

        self.order_lookup[order_id] = order
        self._refresh_order_route_metrics(order)
        heapq.heappush(self.pending_orders, order)
        self._log_event(f"Order {order_id} entered the priority queue for {requested_slot}.")

        self.auto_schedule_pending_orders()

        if order.status in {"Waiting for Slot", "Delayed"}:
            self._store_route_focus(
                f"Evaluated {order.order_id}",
                order.route_path,
                order.route_distance,
                order.estimated_delivery_minutes,
                slot_label=order.requested_slot,
                pickup_distance=order.pickup_distance,
                projected_total=order.projected_total_minutes or order.estimated_delivery_minutes,
            )

        if order.status == "Assigned":
            return (
                f"Order {order_id} created and assigned to {order.assigned_driver_id}. "
                f"Route {int(order.route_distance)} km and total ETA {order.projected_total_minutes} min in {requested_slot}."
            )
        if order.status == "Waiting for Slot":
            return (
                f"Order {order_id} created. Route {int(order.route_distance)} km, "
                f"delivery ETA {order.estimated_delivery_minutes} min. Waiting for slot: {order.scheduling_note}."
            )
        if order.status == "Delayed":
            return f"Order {order_id} created but delayed. {order.scheduling_note}."
        return (
            f"Order {order_id} created and added to the scheduling queue. "
            f"Route {int(order.route_distance)} km, ETA {order.estimated_delivery_minutes} min."
        )

    def assign_next_order(self) -> str:
        assigned_count, messages = self._run_scheduler(limit=1)
        if assigned_count:
            return messages[0]
        if messages:
            return messages[0]
        return "No pending orders are currently queued."

    def mark_order_in_transit(self, order_id: str) -> str:
        order = self.order_lookup.get(order_id.strip())
        if order is None:
            return "Order not found."
        if order.status != "Assigned":
            return f"Order {order.order_id} must be Assigned before starting transit."

        order.status = "In Transit"
        driver = self.drivers.get(order.assigned_driver_id or "")
        if driver is not None:
            self._update_driver_status(driver)
        self._log_event(f"{order.order_id} is now in transit.")
        return f"Order {order.order_id} moved to In Transit."

    def complete_delivery(self, order_id: str) -> str:
        order = self.order_lookup.get(order_id.strip())
        if order is None:
            return "Order not found."
        if order.status not in {"Assigned", "In Transit"}:
            return f"Order {order.order_id} is not active right now."

        order.status = "Completed"
        order.scheduling_note = "Delivered successfully."
        self.completed_deliveries.append(order)
        self._remove_from_waiting_queue(order)

        driver = self.drivers.get(order.assigned_driver_id or "")
        if driver is not None:
            driver.current_location = order.destination
            driver.active_slot_assignments.pop(order.requested_slot, None)
            self._update_driver_status(driver)

        self._store_route_focus(
            f"Completed {order.order_id}",
            order.route_path,
            order.route_distance,
            order.estimated_delivery_minutes,
            driver_name=driver.name if driver else None,
            slot_label=order.requested_slot,
            pickup_path=order.pickup_path,
            pickup_distance=order.pickup_distance,
            projected_total=order.projected_total_minutes,
        )
        self._log_event(f"{order.order_id} completed and moved to the completed queue.")
        scheduler_summary = self.auto_schedule_pending_orders()
        if scheduler_summary.startswith("Auto scheduler assigned"):
            return f"Order {order.order_id} marked as completed. {scheduler_summary}"
        return f"Order {order.order_id} marked as completed."

    def get_shortest_route_summary(self, start: str, end: str) -> str:
        distance, path = self.city_graph.shortest_path(start.strip(), end.strip())
        if not path:
            return f"No route found between {start} and {end}."

        estimated_minutes = estimate_minutes(distance)
        self._store_route_focus(
            f"Route from {start} to {end}",
            path,
            distance,
            estimated_minutes,
            projected_total=estimated_minutes,
        )
        self._log_event(f"Shortest route checked from {start} to {end}.")
        return (
            f"Shortest path: {' -> '.join(path)} | Distance: {int(distance)} km | "
            f"Estimated delivery time: {estimated_minutes} min"
        )

    def list_pending_orders(self) -> List[DeliveryOrder]:
        return sorted(self.pending_orders)

    def list_waiting_orders(self) -> List[DeliveryOrder]:
        waiting_orders: List[DeliveryOrder] = []
        seen = set()
        for slot_label in SLOT_LABELS:
            for order_id in self.waiting_queues[slot_label]:
                order = self.order_lookup.get(order_id)
                if order and order.status == "Waiting for Slot" and order_id not in seen:
                    waiting_orders.append(order)
                    seen.add(order_id)
        return waiting_orders

    def list_assigned_orders(self) -> List[DeliveryOrder]:
        return sorted(
            (order for order in self.order_lookup.values() if order.status == "Assigned"),
            key=lambda order: (order.slot_rank, order.priority_rank, order.sequence_number),
        )

    def list_in_transit_orders(self) -> List[DeliveryOrder]:
        return sorted(
            (order for order in self.order_lookup.values() if order.status == "In Transit"),
            key=lambda order: (order.slot_rank, order.priority_rank, order.sequence_number),
        )

    def list_delayed_orders(self) -> List[DeliveryOrder]:
        return sorted(
            (order for order in self.order_lookup.values() if order.status == "Delayed"),
            key=lambda order: order.sequence_number,
        )

    def list_drivers(self) -> List[Driver]:
        drivers = sorted(self.drivers.values(), key=lambda driver: driver.driver_id)
        for driver in drivers:
            self._update_driver_status(driver)
        return drivers

    def list_completed_deliveries(self) -> List[DeliveryOrder]:
        return list(self.completed_deliveries)

    def list_activity_log(self) -> List[str]:
        return list(self.activity_log)

    def build_slot_summary(self) -> List[Dict[str, object]]:
        summary = []
        for slot_label in SLOT_LABELS:
            available_drivers = sum(
                1
                for driver in self.drivers.values()
                if driver.availability_status != "Offline"
                and slot_label in driver.available_slots
                and slot_label not in driver.active_slot_assignments
            )
            waiting_count = sum(
                1
                for order_id in self.waiting_queues[slot_label]
                if self.order_lookup.get(order_id)
                and self.order_lookup[order_id].status == "Waiting for Slot"
            )
            summary.append(
                {
                    "label": slot_label,
                    "available_drivers": available_drivers,
                    "waiting_count": waiting_count,
                }
            )
        return summary

    def get_summary_counts(self) -> Dict[str, int]:
        return {
            "locations": len(self.city_graph.list_locations()),
            "roads": len(self.city_graph.list_roads()),
            "drivers": len(self.drivers),
            "idle_drivers": sum(1 for driver in self.drivers.values() if driver.availability_status == "Idle"),
            "busy_drivers": sum(1 for driver in self.drivers.values() if driver.availability_status == "Busy"),
            "offline_drivers": sum(1 for driver in self.drivers.values() if driver.availability_status == "Offline"),
            "queued_orders": len(self.pending_orders),
            "waiting_orders": len(self.list_waiting_orders()),
            "delayed_orders": len(self.list_delayed_orders()),
            "assigned_orders": len(self.list_assigned_orders()),
            "in_transit_orders": len(self.list_in_transit_orders()),
            "completed_orders": len(self.completed_deliveries),
        }

    def get_last_route_info(self) -> Optional[Dict[str, object]]:
        return self.last_route_info

    def build_graph_view(self) -> Dict[str, object]:
        width = 720
        height = 420
        locations = self.city_graph.list_locations()
        if not locations:
            return {"width": width, "height": height, "nodes": [], "edges": []}

        center_x = width / 2
        center_y = height / 2
        radius = 145 if len(locations) > 1 else 0

        positions: Dict[str, Tuple[float, float]] = {}
        for index, location in enumerate(locations):
            if len(locations) == 1:
                positions[location] = (center_x, center_y)
                continue
            angle = (2 * math.pi * index / len(locations)) - (math.pi / 2)
            positions[location] = (
                center_x + math.cos(angle) * radius,
                center_y + math.sin(angle) * radius,
            )

        highlighted_nodes = set()
        highlighted_edges = set()
        if self.last_route_info:
            route_path = self.last_route_info.get("path", [])
            highlighted_nodes = set(route_path)
            for start, end in zip(route_path, route_path[1:]):
                highlighted_edges.add(frozenset((start, end)))

        edges = []
        for source, destination, distance in self.city_graph.list_roads():
            x1, y1 = positions[source]
            x2, y2 = positions[destination]
            edges.append(
                {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2),
                    "label_x": round((x1 + x2) / 2, 2),
                    "label_y": round((y1 + y2) / 2, 2),
                    "distance": distance,
                    "highlighted": frozenset((source, destination)) in highlighted_edges,
                }
            )

        nodes = []
        for location, (x, y) in positions.items():
            nodes.append(
                {
                    "name": location,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "highlighted": location in highlighted_nodes,
                }
            )

        return {"width": width, "height": height, "nodes": nodes, "edges": edges}

    def display_status(self) -> None:
        counts = self.get_summary_counts()
        print("\nDynamic Delivery Slot Scheduling System")
        print("=" * 48)
        print(
            f"Locations: {counts['locations']} | Roads: {counts['roads']} | Drivers: {counts['drivers']}"
        )
        print(
            f"Queued: {counts['queued_orders']} | Waiting: {counts['waiting_orders']} | "
            f"Assigned: {counts['assigned_orders']} | In Transit: {counts['in_transit_orders']} | "
            f"Completed: {counts['completed_orders']} | Delayed: {counts['delayed_orders']}"
        )

        print("\nDrivers:")
        for driver in self.list_drivers():
            print(
                f"  {driver.driver_id}: {driver.name} | Status: {driver.availability_status} | "
                f"Location: {driver.current_location} | Free Slots: {', '.join(driver.free_slots())}"
            )

        print("\nScheduler Queue:")
        for order in self.list_pending_orders():
            print(
                f"  {order.order_id}: {order.priority_label} | Slot: {order.requested_slot} | "
                f"Status: {order.status} | ETA: {order.estimated_delivery_minutes} min"
            )

        print("\nCompleted Queue:")
        for order in self.list_completed_deliveries():
            print(f"  {order.order_id}: {order.customer_name} | Status: {order.status}")


def build_demo_system() -> DeliveryManagementSystem:
    system = DeliveryManagementSystem()

    for location in [
        "Warehouse",
        "North Gate",
        "South Hub",
        "Market",
        "Riverside",
        "Station",
        "Campus",
        "Tech Park",
        "Remote Outpost",
    ]:
        system.add_location(location)

    roads = [
        ("Warehouse", "North Gate", 4),
        ("Warehouse", "Market", 6),
        ("Warehouse", "South Hub", 5),
        ("North Gate", "Campus", 5),
        ("North Gate", "Station", 6),
        ("South Hub", "Market", 3),
        ("South Hub", "Riverside", 4),
        ("Market", "Station", 4),
        ("Market", "Tech Park", 5),
        ("Riverside", "Campus", 6),
        ("Station", "Campus", 3),
        ("Station", "Tech Park", 4),
        ("Campus", "Tech Park", 4),
    ]
    for source, destination, distance in roads:
        system.add_road(source, destination, distance)

    # Demo drivers are arranged so the slot-feasibility rules are visible on screen.
    system.add_driver("D1", "Aarav", "Warehouse", ["09:00-10:00"])
    system.add_driver("D2", "Meera", "Market", ["10:00-11:00", "11:00-12:00", "12:00-13:00"])
    system.add_driver("D3", "Kabir", "North Gate", ["09:00-10:00", "11:00-12:00"])
    system.add_driver("D4", "Sana", "South Hub", ["12:00-13:00", "13:00-14:00"])
    system.add_driver("D5", "Ishita", "Campus", ["09:00-10:00"], "Offline")

    system.create_order("O301", "Aditi", "Warehouse", "Campus", "Books", "urgent", "09:00-10:00")
    system.create_order("O302", "Rohan", "Market", "South Hub", "Documents", "urgent", "10:00-11:00")
    system.create_order("O303", "Neha", "South Hub", "Campus", "Groceries", "high", "10:00-11:00")
    system.create_order("O304", "Vivek", "North Gate", "Station", "Medicine", "normal", "11:00-12:00")
    system.create_order("O305", "Simran", "Riverside", "Warehouse", "Electronics", "high", "12:00-13:00")
    system.create_order("O306", "Tarun", "Market", "Remote Outpost", "Medical Kit", "normal", "13:00-14:00")

    system.mark_order_in_transit("O301")
    return system
