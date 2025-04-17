# B-Tree File Organization
![image](https://github.com/user-attachments/assets/ce1acbdf-8a4d-4fd2-ba0b-90a2a00141be)

## Project Overview

This project implements a **B-Tree** data structure used as an indexing mechanism for organizing a data file. The implementation is written in **Python** and utilizes **binary file operations** and **buffered memory management** to simulate efficient file handling.

The main goal of this project was to simulate how databases or file systems use B-Trees for indexing, optimizing disk reads and writes while ensuring balanced tree structure and fast access times.

## Key Features
  
- Insertion of records into the B-Tree  
- Record lookup (search by key)  
- Record update functionality  
- Visual and textual traversal of the tree in sorted key order  
- Loading B-Tree configuration from a main data file  

Each record in the data file contains:
- A **natural key** (an integer)
- The **lengths of a parallelogram's sides**
- The **angle** between the sides

## B-Tree Algorithm and Overflow Handling

This implementation uses a **classic B-Tree** data structure (not B+Tree or B*Tree), where:

- **All nodes** (internal and leaf) may store both **keys and associated data**
- Internal nodes contain keys and pointers to child nodes
- Keys are kept **in strictly sorted order**
- The tree remains **balanced**, ensuring logarithmic time complexity for search, insert, and update operations

### Insertion Strategy with Pre-Split Redistribution

A key feature of this implementation is the **overflow handling mechanism**, which optimizes tree growth and minimizes the number of node splits:

1. **Redistribution Before Split (Compensation)**:
   - When a node becomes full (i.e., holds `2d` keys), the algorithm first checks if a **sibling node** (left or right) has space to accommodate an extra key and associated data.
   - If possible, the overflowing node redistributes part of its content to the sibling node — this process is called **compensation**.
   - This step helps delay the need to split the node.

2. **Node Split (Fallback)**:
   - If no redistribution is possible (i.e., both neighbors are full), the node is **split** into two:
     - The middle key is promoted to the parent node.
     - The new left and right nodes each receive part of the original keys and data.
   - This can cause recursive splits up the tree, potentially increasing its height.

### Benefits of Redistribution Strategy

- Reduces the frequency of **node splits** and tree height growth
- Minimizes **disk I/O** operations, improving performance
- Provides more **stable insertion behavior** by spreading data more evenly across nodes
- Offers better **buffer and memory utilization**, especially with disk-backed structures

This overflow handling strategy is commonly used in real-world systems where disk performance and structural stability are important.
## Implementation Details

### 1. Main File Structure

The main data file stores records line by line in plain text format. Each line starts with the key, followed by values representing a geometric object (e.g., parallelogram side lengths and angle). The position (index) of a record in the file corresponds to the line number, starting from 1.

### 2. B-Tree Structure

- **Minimum degree (d)**: `2` (configurable)
- **Serialization**: Each B-Tree node is serialized and stored in a binary file with a unique address.
- **Node structure**:
  - Information about parent (used for validation)
  - Leaf flag
  - Ordered keys and pointers to children
  - Internal and leaf node types supported

Each node can hold between `d` and `2d` keys, and `d+1` to `2d+1` child pointers.

### 3. Buffer Management

A custom buffer was implemented to reduce the number of disk I/O operations. Pages (tree nodes) are loaded into the buffer based on tree height `h` and degree `d`. Each page size is proportional to the value of `d` (e.g., 60 bytes per node for `d = 2`).

### 4. Algorithms

Implemented key algorithms:
- `insert(key, record)`
- `search_key(key)`
- `delete_key(key)`
- `actualize_tree()` - it works like deleting and adding, or it just swaps the localization of the key 

Splitting of nodes, key compensation between siblings, and balancing were all handled in accordance with standard B-Tree rules.

## Experiments

Two main experiments were conducted to analyze **disk I/O performance**.

### Experiment 1: Continuous Insertion

Tested the number of disk read/write operations while inserting `x` randomly generated elements into an initially empty tree. The tested values of `x` were:

`[10, 100, 500, 1000, 5000]`  
and B-Tree degrees `d = [2, 4, 6, 8, 10]`.

 Observation:
- Disk I/O (read + write) **decreased** with increasing B-Tree degree.
- However, larger degrees increased page size.
- Read operations dominated write operations as more nodes had to be loaded for traversal.

### Experiment 2: Single Insertion Analysis

Measured the disk operations for inserting **one** element into a **pre-filled** B-Tree (with `x` existing elements). Focus was on the immediate cost of insertion:

 Conclusion:
- Disk I/O increases with the number of existing records due to tree height.
- Insertions may or may not trigger splits, resulting in fluctuations.
- Higher `d` values reduced I/O by allowing more data per node.
