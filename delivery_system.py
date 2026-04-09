from __future__ import annotations

from delivery_core import (
    DeliveryManagementSystem,
    SLOT_LABELS,
    SLOT_WINDOWS,
    build_demo_system,
)


def print_menu() -> None:
    print("\nDynamic Delivery Slot Scheduling System")
    print("=" * 46)
    print("1. Start simulation with demo data")
    print("2. Add location")
    print("3. Add road")
    print("4. Register driver")
    print("5. Create order")
    print("6. Assign next order")
    print("7. Start transit for an assigned order")
    print("8. Mark order completed")
    print("9. Find shortest route")
    print("10. Display status")
    print("11. Exit")


def prompt_non_empty(message: str) -> str:
    while True:
        value = input(message).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")


def prompt_positive_int(message: str) -> int:
    while True:
        value = input(message).strip()
        try:
            number = int(value)
        except ValueError:
            print("Please enter a valid integer.")
            continue
        if number <= 0:
            print("Please enter a value greater than 0.")
            continue
        return number


def prompt_slot(message: str) -> str:
    while True:
        value = input(message).strip()
        if value in SLOT_WINDOWS:
            return value
        print(f"Choose a valid slot: {', '.join(SLOT_LABELS)}")


def handle_load_demo_data() -> DeliveryManagementSystem:
    print("Simulation data loaded successfully.")
    return build_demo_system()


def handle_add_location(system: DeliveryManagementSystem) -> None:
    print(system.add_location(prompt_non_empty("Enter location name: ")))


def handle_add_road(system: DeliveryManagementSystem) -> None:
    location_a = prompt_non_empty("Enter first location: ")
    location_b = prompt_non_empty("Enter second location: ")
    distance = prompt_positive_int("Enter distance in km: ")
    print(system.add_road(location_a, location_b, distance))


def handle_register_driver(system: DeliveryManagementSystem) -> None:
    driver_id = prompt_non_empty("Enter driver ID: ")
    name = prompt_non_empty("Enter driver name: ")
    current_location = prompt_non_empty("Enter current location: ")
    slot_text = prompt_non_empty(
        "Enter available slots separated by commas "
        f"({', '.join(SLOT_LABELS)}): "
    )
    available_slots = [slot.strip() for slot in slot_text.split(",") if slot.strip()]
    print(system.add_driver(driver_id, name, current_location, available_slots))


def handle_create_order(system: DeliveryManagementSystem) -> None:
    order_id = prompt_non_empty("Enter order ID: ")
    customer_name = prompt_non_empty("Enter customer name: ")
    source = prompt_non_empty("Enter source location: ")
    destination = prompt_non_empty("Enter destination location: ")
    package_type = prompt_non_empty("Enter package type: ")
    priority = prompt_non_empty("Enter priority (urgent/high/normal/low): ")
    requested_slot = prompt_slot("Enter requested slot: ")
    print(
        system.create_order(
            order_id,
            customer_name,
            source,
            destination,
            package_type,
            priority,
            requested_slot,
        )
    )


def handle_mark_in_transit(system: DeliveryManagementSystem) -> None:
    print(system.mark_order_in_transit(prompt_non_empty("Enter order ID: ")))


def handle_complete_delivery(system: DeliveryManagementSystem) -> None:
    print(system.complete_delivery(prompt_non_empty("Enter order ID: ")))


def handle_shortest_route(system: DeliveryManagementSystem) -> None:
    start = prompt_non_empty("Enter source location: ")
    end = prompt_non_empty("Enter destination location: ")
    print(system.get_shortest_route_summary(start, end))


def run_console_app() -> None:
    system = DeliveryManagementSystem()

    while True:
        print_menu()
        choice = input("Choose an option (1-11): ").strip()

        if choice == "1":
            system = handle_load_demo_data()
        elif choice == "2":
            handle_add_location(system)
        elif choice == "3":
            handle_add_road(system)
        elif choice == "4":
            handle_register_driver(system)
        elif choice == "5":
            handle_create_order(system)
        elif choice == "6":
            print(system.assign_next_order())
        elif choice == "7":
            handle_mark_in_transit(system)
        elif choice == "8":
            handle_complete_delivery(system)
        elif choice == "9":
            handle_shortest_route(system)
        elif choice == "10":
            system.display_status()
        elif choice == "11":
            print("Exiting Dynamic Delivery Slot Scheduling System.")
            break
        else:
            print("Invalid choice. Please select a number from 1 to 11.")


def main() -> None:
    run_console_app()


if __name__ == "__main__":
    main()
