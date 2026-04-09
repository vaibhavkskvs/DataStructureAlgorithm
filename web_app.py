from __future__ import annotations

import os
from typing import Dict

from flask import Flask, flash, redirect, render_template, request, url_for

from delivery_core import DeliveryManagementSystem, build_demo_system


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dynamic-delivery-slot-scheduling-secret")

SYSTEM_STORE: Dict[str, DeliveryManagementSystem] = {
    "system": DeliveryManagementSystem()
}


def get_system() -> DeliveryManagementSystem:
    return SYSTEM_STORE["system"]


def set_system(system: DeliveryManagementSystem) -> None:
    SYSTEM_STORE["system"] = system


def message_category(message: str) -> str:
    lowered = message.lower()
    if any(keyword in lowered for keyword in ["assigned", "registered", "added", "completed", "moved to in transit", "estimated delivery time"]):
        return "success"
    if "waiting" in lowered or "queued" in lowered:
        return "info"
    if any(keyword in lowered for keyword in ["invalid", "not found", "must", "cannot", "delayed", "no route"]):
        return "error"
    return "info"


def build_dashboard_context() -> Dict[str, object]:
    system = get_system()
    return {
        "counts": system.get_summary_counts(),
        "locations": system.city_graph.list_locations(),
        "roads": system.city_graph.list_roads(),
        "drivers": system.list_drivers(),
        "scheduler_queue": system.list_pending_orders(),
        "waiting_orders": system.list_waiting_orders(),
        "assigned_orders": system.list_assigned_orders(),
        "in_transit_orders": system.list_in_transit_orders(),
        "delayed_orders": system.list_delayed_orders(),
        "completed_orders": system.list_completed_deliveries(),
        "activity_log": system.list_activity_log(),
        "slot_summary": system.build_slot_summary(),
        "priority_options": list(system.PRIORITY_MAP.keys()),
        "slot_options": list(system.SLOT_LABELS),
        "driver_status_options": list(system.DRIVER_STATUS_OPTIONS),
        "route_view": system.get_last_route_info(),
        "graph_view": system.build_graph_view(),
    }


def flash_message(message: str) -> None:
    flash(message, message_category(message))


@app.get("/")
def index() -> str:
    return render_template("index.html", **build_dashboard_context())


@app.post("/load-demo")
def load_demo() -> str:
    set_system(build_demo_system())
    flash("Simulation data loaded successfully.", "success")
    return redirect(url_for("index"))


@app.post("/reset")
def reset_system() -> str:
    set_system(DeliveryManagementSystem())
    flash("System reset successfully.", "info")
    return redirect(url_for("index"))


@app.post("/locations")
def add_location() -> str:
    flash_message(get_system().add_location(request.form.get("location", "")))
    return redirect(url_for("index"))


@app.post("/roads")
def add_road() -> str:
    distance_text = request.form.get("distance", "").strip()
    try:
        distance = int(distance_text)
    except ValueError:
        flash("Distance must be a valid integer.", "error")
        return redirect(url_for("index"))

    flash_message(
        get_system().add_road(
            request.form.get("location_a", "").strip(),
            request.form.get("location_b", "").strip(),
            distance,
        )
    )
    return redirect(url_for("index"))


@app.post("/drivers")
def add_driver() -> str:
    flash_message(
        get_system().add_driver(
            request.form.get("driver_id", ""),
            request.form.get("driver_name", ""),
            request.form.get("driver_location", ""),
            request.form.getlist("available_slots"),
            request.form.get("driver_status", "Idle"),
        )
    )
    return redirect(url_for("index"))


@app.post("/orders")
def create_order() -> str:
    flash_message(
        get_system().create_order(
            request.form.get("order_id", ""),
            request.form.get("customer_name", ""),
            request.form.get("source", ""),
            request.form.get("destination", ""),
            request.form.get("package_type", ""),
            request.form.get("priority", ""),
            request.form.get("requested_slot", ""),
        )
    )
    return redirect(url_for("index"))


@app.post("/assign")
def assign_order() -> str:
    flash_message(get_system().assign_next_order())
    return redirect(url_for("index"))


@app.post("/dispatch")
def dispatch_order() -> str:
    flash_message(get_system().mark_order_in_transit(request.form.get("order_id", "")))
    return redirect(url_for("index"))


@app.post("/complete")
def complete_delivery() -> str:
    flash_message(get_system().complete_delivery(request.form.get("order_id", "")))
    return redirect(url_for("index"))


@app.post("/route")
def shortest_route() -> str:
    flash_message(
        get_system().get_shortest_route_summary(
            request.form.get("route_start", ""),
            request.form.get("route_end", ""),
        )
    )
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
