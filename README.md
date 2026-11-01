# CampusMind — Academic Operations Platform

**A professional local-first application for exam scheduling, faculty management, teaching assignments, room allocation and invigilation duties.**

CampusMind combines a React/TypeScript administration workspace with a FastAPI/Python optimization engine and SQLite persistence. Academic staff see the final schedules and operational outcomes; implementation details remain in the source and technical API.

## Quick start — Windows 11

1. Extract the ZIP into a **new** folder (do not overwrite an earlier CampusMind installation without backing it up).
2. Double-click `scripts/01_SETUP_WINDOWS.bat` **once**. This creates `.venv`, installs Python packages, and installs npm packages. Internet access is required.
3. Double-click `scripts/05_START_CAMPUSMIND.bat` every time you want to open the app.
4. Open **http://127.0.0.1:5173** if your browser does not open automatically.
5. Leave the two server windows running. Press **Ctrl+C** in each to stop.

Requirements: Python 3.10+ and Node.js 20+ including npm. Avoid running RescueNet or the older CampusMind simultaneously: they use the same ports (8000 and 5173).

## Main modules

- **Overview:** live operational summary and examination planning status.
- **Schedule Builder:** clash-free examination timetables with room assignment, draft review, version checks and controlled publishing.
- **Official Timetable:** immutable published snapshot and Excel-friendly CSV export.
- **Courses & Enrollment:** manage course records, primary instructors, student identifiers and facility requirements.
- **Faculty & Teaching:** add/edit faculty profiles and teaching assignments; manage department, designation, contact, expertise, active status, duty limit and unavailable exam slots.
- **Invigilation Duties:** automatically allocate faculty to published exams using workload-aware assignment; review, manually replace invigilators with rule checks, publish and export official duty rosters. Shows staff workload at a glance.
- **Examination Calendar:** maintain examination dates and session windows through regular forms, without raw JSON editing.
- **Rooms & Facilities:** maintain venues, capacities and facilities.
- **Resource Planning:** course prerequisite validation and budget optimization.
- **Reports & Activity:** source-versioned planning history and file exports.
- **Institution Settings:** institutional metadata, exam duty policy and reset/advanced data tools.

## Recommended administrative workflow

1. Open **Courses & Enrollment**, **Faculty & Teaching**, **Rooms & Facilities**, and **Examination Calendar**. Check the sample setup.
2. In **Faculty & Teaching**, select a course and assign its primary instructor. Edit faculty profiles to configure unavailable sessions and maximum invigilation duties.
3. In **Schedule Builder**, generate an examination draft, review rooms and time slots, and publish the official timetable.
4. In **Invigilation Duties**, choose **Balanced coverage**, generate the duty roster, optionally change individual assignments, and publish.
5. Export the official exam timetable and duty roster as CSV files, or review history in **Reports & Activity**.

**Important:** If you change a course, faculty profile, exam session or policy after publication, the previously published snapshot remains preserved but is marked *stale*. Generate and publish a new timetable and duty plan before circulating updates.

## Algorithms (backend only)

- DSATUR greedy / backtracking graph coloring for examination conflict avoidance.
- Greedy / Branch and Bound for venue assignment.
- Constraint-aware greedy / bounded Branch and Bound for invigilation assignments (fairness, leave, subject restrictions, non-overlap, duty limits).
- Kahn's topological sorting for course prerequisites.
- 0/1 Knapsack dynamic programming for resource budget optimization.

The balanced invigilation planner can return a feasible best-found assignment if its search limit is reached. The user interface does **not** claim mathematical optimality in that case. The original comparison endpoints remain available through the API for technical examination or evaluation.

## Directory overview

```
CampusMind_Complete/
├── backend/
│   ├── app/
│   │   ├── main.py                     API routes
│   │   ├── service.py                  Scenario validation / scheduling
│   │   ├── storage.py                  SQLite persistence / publications
│   │   └── algorithms/
│   │       ├── conflicts.py
│   │       ├── coloring.py
│   │       ├── rooms.py
│   │       ├── invigilation.py         NEW: faculty duty optimizer
│   │       ├── prerequisites.py
│   │       └── budget.py
│   └── tests/
│       └── test_faculty_duties.py      NEW: faculty/duty integration tests
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── WorkspaceExtras.tsx        NEW: faculty, duties, calendar pages
│       └── styles.css
├── data/
│   └── campus_demo.json               fictional starter dataset
├── docs/
│   ├── OPERATIONS_GUIDE.md
│   ├── WINDOWS_SETUP.md
│   ├── PRODUCT_READINESS.md
│   └── ALGORITHM_ANALYSIS.md
└── scripts/
    ├── 01_SETUP_WINDOWS.bat
    ├── 02_START_BACKEND.bat
    ├── 03_START_FRONTEND.bat
    ├── 04_RUN_TESTS.bat
    └── 05_START_CAMPUSMIND.bat
```

## Data and database

The sample institution and student IDs are **fictional**. The database is initialized automatically on the first backend launch at `data/campusmind.db`. It is excluded from the project ZIP. Existing scenario and run history are stored locally in the database and are **not synced between installations**.

To preserve an older installation's data, **back up its SQLite database first**. Copy a database only after stopping both server processes, and only if you understand which version/source data it contains. On first launch in a new folder, the bundled example is loaded. Older faculty records missing new optional fields use defaults until edited and saved.

Backend API: http://127.0.0.1:8000/docs

Run backend tests via `scripts/04_RUN_TESTS.bat` or `cd backend && python -m pytest -q tests` with the project's virtual environment active.

## Commercial deployment warning

This is a functional, integrated **single-institution local prototype**, not a pre-certified university ERP or internet-ready SaaS. It has **no authentication or role-based access controls**, and SQLite stores data locally without encryption-at-rest. Do **not** put it on a public server or enter real students' private records without further security and legal review. Before taking payments or deploying to an institution, see `docs/PRODUCT_READINESS.md` for the necessary access control, tenancy, audit, backup, data protection, deployment, and acceptance-testing requirements.
