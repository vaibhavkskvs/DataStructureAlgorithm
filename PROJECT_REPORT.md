# Project Report

## Title

Dynamic Delivery Management System Using Data Structures and Algorithms

## Abstract

The Dynamic Delivery Management System is a DSA-based project that simulates the functioning of a modern delivery platform. The system manages customer orders, assigns available drivers, and finds optimal delivery routes between locations. It uses a graph to represent the delivery network, a priority queue to process urgent orders first, hash maps for efficient storage and retrieval, and a queue to track completed deliveries. The project shows how data structures and algorithms can solve real-world logistics problems in an efficient and scalable way.

## Introduction

Online delivery services require continuous decision-making. Orders arrive at different times, customers expect fast service, and drivers must be assigned efficiently. A manual system is slow and error-prone, especially when the number of deliveries grows.

This project addresses that problem by building a delivery management system based on DSA concepts. It helps demonstrate how algorithms can improve route planning, task prioritization, and system responsiveness.

## Problem Definition

The main problem is to manage deliveries dynamically while ensuring:

- urgent orders are processed first,
- routes are optimized,
- driver information is easily accessible,
- completed deliveries are tracked in an organized way.

## Proposed Solution

The proposed system combines multiple DSA components:

- A `graph` stores delivery locations and road distances.
- `Dijkstra's algorithm` finds the shortest path between two locations.
- A `priority queue` stores pending orders according to urgency.
- `Hash maps` store order and driver records for fast lookup.
- A `queue` stores completed deliveries in processing order.

## Modules

### 1. Location and Route Management

- Add delivery locations
- Add weighted roads between locations
- Compute shortest paths

### 2. Driver Management

- Register drivers
- Track availability status

### 3. Order Management

- Create new orders
- Prioritize urgent orders
- Assign orders to available drivers

### 4. Delivery Completion

- Mark assigned deliveries as completed
- Store completed delivery history

## Algorithms Used

### Dijkstra's Algorithm

Used to determine the minimum-distance route from source to destination in the road network graph.

### Heap-Based Priority Queue

Used for selecting the most urgent order among all pending orders.

## Time Complexity

- Insert order into priority queue: `O(log n)`
- Remove highest-priority order: `O(log n)`
- Hash map lookup for order/driver: `O(1)` average
- Dijkstra's shortest path: `O((V + E) log V)` with a heap
- Queue insertion for completed deliveries: `O(1)`

## Advantages

- Efficient order prioritization
- Fast search and retrieval
- Better route selection
- Clear demonstration of multiple DSA topics in one project
- Easy to extend into a larger system

## Limitations

- Current version is a console-based prototype
- Uses static edge weights instead of live traffic
- Handles one delivery assignment at a time in the demo flow

## Conclusion

The Dynamic Delivery Management System is a practical example of applying data structures and algorithms to a logistics problem. The project clearly shows how graphs, queues, heaps, and hash maps can improve the efficiency of delivery operations. It is a suitable academic project because it combines theory, implementation, and real-world relevance.

## Viva Questions

1. Why is a priority queue used for orders?
2. Why is a graph suitable for delivery routing?
3. What is Dijkstra's algorithm, and when does it work best?
4. Why are hash maps useful in this system?
5. What is the time complexity of assigning the highest-priority order?
6. How can this project be improved for real-world deployment?
