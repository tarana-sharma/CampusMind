# CampusMind

## Research problem

Create a reproducible synthetic examination scheduling framework balancing hard enrollment conflicts, room compatibility and capacity, and available time blocks. Compare the speed and solution quality of polynomial heuristics with exact exponential search and pseudo-polynomial dynamic programming.

## Algorithm specification and complexity

**Input:** courses, enrolled student identifiers, instructor IDs, exam room seats/facilities, ordered timeslots, directed course prerequisites, indivisible readiness investments. **Output:** exam-to-timeslot coloring, room mapping, curricular dependency order, budget allocation and instrumentation.

A conflict graph G=(V,E) is derived by placing an edge between courses if they share at least one student or share an instructor. A valid timetable requires a proper coloring: for every edge (u,v), color(u) ≠ color(v). Colors correspond to available timeslots.

## Decrease and Conquer / Greedy

### DSATUR coloring

At each iteration, choose the uncolored vertex with highest *saturation degree* (distinct neighbor colors), tie-break by vertex degree and ID, then assign the lowest available color. Produces a feasible coloring; does not guarantee minimum colors. This simple Python version recomputes saturation values each step: O(V³) conservative upper bound.

### Kahn topological sorting

Construct a directed curriculum prerequisite graph and use a zero-indegree queue, removing incoming-degree counts as vertices are processed. O(V + E). A partial ordering indicates a cycle; DFS extracts an example cycle. Do not interpret prerequisites as exam precedence constraints.

### Greedy room allocation

Sort each slot's examinations by number of compatible rooms, then enrollment, then course ID. For each choose the lowest-cost unoccupied eligible room. It is fast, but may produce nonoptimal assignments or fail when a different assignment could succeed.

## Backtracking, Branch and Bound, Dynamic Programming

### Exact graph coloring (backtracking)

First find a DSATUR upper bound K. Attempt feasible k-coloring with k=2,...,K-1 (or k=1 when no edges), selecting highest-saturation uncolored vertices. A failed exhaustive k-color search proves k colors insufficient. Stop on the first successful k to prove minimal colors. Worst case exponential. Interactive limit: at most 13 exams and 400,000 search nodes; aborts explicitly without falsely claiming an optimum.

### Room assignment via Branch and Bound

Each assigned exam uses exactly one eligible room in its time block. Minimize Σ (unused seats + penalty for using a specialist lab for non-lab exams). Search across room assignments ordered by constrainedness; prune when `current_cost + lower_bound_remaining >= incumbent`, where lower bound independently chooses the cheapest room for each remaining exam ignoring room uniqueness. This lower bound is optimistic and therefore safe. The worst case is factorial in the number of choices per slot; slots are independent and solved individually.

### 0/1 knapsack via Dynamic Programming

For indivisible exam-readiness investments, let dp[i][w] be the maximum benefit using the first i items and budget at most w:

`dp[i][w] = max(dp[i-1][w], dp[i-1][w-cost_i] + value_i)` when cost_i <= w, otherwise carry the previous value. Complexity O(nW) time and O(nW) memory. Greedy ratio ordering is a fast heuristic but not always optimal.

## Experiments

1. Generate a default schedule using DSATUR, then exact coloring, comparing time blocks used and search nodes.
2. Holding coloring fixed, compare Greedy room matching and Branch and Bound objective cost.
3. Holding budget fixed, compare ratio Greedy against exact Knapsack DP benefit.
4. Alter room capacities; inspect when no feasible room exists and verify error handling.
5. Introduce a shared student across previously unrelated courses; observe the new graph edge.
6. Add a prerequisite cycle; confirm topological sorting refuses to return a complete ordering.
7. Repeat each experiment under increasing input sizes and multiple runs, recording medians.

**Correctness:** brute force for tiny graph/room cases, check every conflicting pair of courses has different colors, verify no two exams share a room in a slot, seat and facility constraints, budgets not exceeded, and all prerequisites precede their dependents in a valid order.

**Caution:** one-run timing comparisons cannot establish overall speed superiority. Complexity results refer to algorithm structure, not any single measurement. An optimal room assignment is only optimal given the fixed coloring and the modeled objective, not globally across all conceivable campus policies.

## Faculty invigilation assignment — Greedy and bounded Branch and Bound

File: `backend/app/algorithms/invigilation.py`.

Inputs are a published exam schedule, staff membership/active status, forbidden sessions, subject ownership, maximum duty count and per-exam supervision requirements. Each exam requires one or two *different* invigilators. A faculty member cannot supervise overlapping sessions. Own-course exclusions are configurable.

The **Quick** solver processes the most constrained tasks first and assigns each eligible faculty member by incremental cost. The cost is based on assignment fairness (additional assignments become progressively more expensive) and an optional modest same-department preference. This is a Greedy heuristic and does not guarantee the globally lowest score.

The **Balanced** solver starts from the Greedy incumbent and performs Branch and Bound with an admissible lower bound that relaxes slot collisions and availability while accounting for minimum assignment, workload and department costs. It prunes branches that cannot improve the incumbent. Because the assignment problem can be combinatorial, search is capped at 120,000 expanded nodes and reports `status='feasible'` if the cap is reached. Only an exhausted (fully searched) feasible search can report `status='optimal'`. Both solvers pass the same strict constraint validator before returning any plan.

Worst-case combinatorial growth is exponential in the number of duties. Fairness is modeled by a progressive workload penalty, not claimed as a legally mandated or universally optimal staffing policy.

The normal administration interface shows the resulting duties and workloads. Algorithm measurements remain available through API run records, to keep technical diagnostics separate from the operational workflow.
