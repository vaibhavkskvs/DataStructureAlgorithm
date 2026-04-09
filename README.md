# Dynamic Delivery Slot Scheduling System

This project is a DSA-based delivery dispatch simulator that manages orders, drivers, routes, and delivery time slots dynamically.

## Problem Statement

In real-world delivery systems, new orders arrive continuously, drivers become available at different times, and routes must be chosen efficiently. A delivery platform needs fast assignment, quick lookup of records, and optimized path selection between locations.

The goal of this project is to design a `Dynamic Delivery Slot Scheduling System` using core Data Structures and Algorithms concepts so that orders can be prioritized, drivers can be assigned efficiently, time-slot feasibility can be checked, and delivery routes can be optimized.

## Objectives

- Manage delivery orders dynamically as they arrive.
- Assign higher-priority orders first.
- Store and retrieve orders and driver details efficiently.
- Model delivery locations as a graph.
- Find the shortest route between source and destination.
- Check whether the required route fits inside the requested delivery slot.
- Track completed deliveries for reporting.

## DSA Concepts Used

### 1. Graph
The road network between delivery locations is represented as a weighted graph.

- Nodes represent locations.
- Edges represent roads.
- We use Dijkstra's algorithm to find the shortest path.

### 2. Priority Queue (Heap)
Orders are stored in a priority queue so urgent orders and earlier slots are processed before lower-priority requests.

### 3. Hash Map
Orders and drivers are stored in dictionaries for fast lookup by ID.

### 4. Queue
Completed deliveries and waiting slot queues are stored using queue-based structures to maintain scheduling history and blocked requests.

## Features

- Add locations and weighted roads
- Register slot-aware drivers
- Create delivery orders with requested time windows
- Automatically assign the best feasible driver
- Use Dijkstra to calculate route distance and estimated delivery time
- Keep slot-blocked orders in a visible waiting queue
- Track Assigned, In Transit, Completed, and Delayed orders
- Display a graph-based route viewer in the website
- Keep a console interface for viva/demo backup

## Project Structure

```text
Dynamic delivery management system/
|-- README.md
|-- requirements.txt
|-- docs/
|   `-- PROJECT_REPORT.md
`-- src/
    |-- delivery_core.py
    |-- delivery_system.py
    |-- web_app.py
    |-- static/
    |   `-- styles.css
    `-- templates/
        |-- base.html
        `-- index.html
```

## How to Run

Make sure Python 3 and Flask are installed.

### Console Version

Run:

```bash
python src/delivery_system.py
```

### Website Version

Run:

```bash
python src/web_app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Deploy Online

The easiest way to get a public shareable link is:

1. Upload this project to a GitHub repository.
2. Create a new `Web Service` on Render.
3. Connect that GitHub repository.
4. Render will detect `render.yaml` and deploy the app automatically.

Production entry files already added:

- `wsgi.py`
- `render.yaml`
- `requirements.txt`

After deployment, Render gives you a public URL like:

```text
https://your-app-name.onrender.com
```

## Console Options

After running the console version, you can:

- start the simulation with demo data,
- add locations and roads,
- register slot-aware drivers,
- create new orders with a requested slot,
- assign the next feasible queued order,
- move assigned orders to transit,
- complete deliveries,
- find the shortest route between any two locations,
- display the full scheduling state.

## Website Features

The website version includes:

- dashboard cards for key delivery statistics
- quick actions for simulation start, assignment, and reset
- forms for adding locations, roads, drivers, and slot-based orders
- route finding using Dijkstra's algorithm
- a visible road-network graph with route highlighting
- live views for driver availability, scheduler heap, waiting queue, assigned orders, in-transit orders, completed orders, and delayed orders

## Expected Learning Outcome

This project demonstrates how multiple DSA concepts can work together in one practical system. It is suitable for a PBL or mini-project where the focus is on both implementation and explanation of algorithm choices.

## Future Enhancements

- Add delivery time windows
- Support multiple drivers at once
- Add traffic-based dynamic weights
- Add persistent database storage
- Add delivery analytics and performance reports
