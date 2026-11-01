# CampusMind Operations Guide

## Prepare an examination cycle

1. **Settings:** set the institution name and planning cycle. Configure one or two invigilators per exam and whether course teachers may supervise their own subjects.
2. **Courses & Enrollment:** check all course IDs, enrollments, room requirements, and instructors.
3. **Faculty & Teaching:** add teachers, select a primary instructor for every course, and set active status, department, unavailable exam sessions, and maximum duties.
4. **Examination Calendar:** add exam dates and morning/afternoon windows. Overlapping sessions on the same date are rejected.
5. **Rooms & Facilities:** verify capacity and special facilities.

## Produce and approve exams

- Open **Schedule Builder** and generate a proposed exam timetable.
- Review date, time, room and enrollment for every exam.
- Export a draft CSV for review.
- Click **Publish timetable** when approved. The published data is stored as a snapshot; edits to source records do not silently rewrite it.

## Produce and approve invigilation duties

- Open **Invigilation Duties** after the official timetable has been published.
- Choose **Balanced coverage** (more search) or **Quick allocation** (fast feasible plan).
- Click **Generate duty roster**. The optimizer respects active status, unavailable exam windows, maximum duties, duplicate/overlapping duties, and the own-course policy.
- Inspect the roster and teacher workload indicators.
- For substitutions, select a duty and a replacement teacher. A change violating any assignment rule is rejected.
- Click **Publish duties** to make the roster official. Use **Export roster** to download CSV. Use the Reports page for the official exported roster even after closing the draft.

## What if scheduling fails?

**Not enough rooms:** add a compatible venue, correct facilities/capacity or increase non-overlapping exam sessions.

**Not enough eligible invigilators:** add/activate faculty, increase per-person duty limits, review unavailability or change the required number of invigilators. Never bypass restrictions blindly.

**Old published roster:** source data or the official timetable has changed. Generate and republish a new timetable and roster; old official snapshots remain visible with a stale indicator until replaced/unpublished.

**Cannot remove faculty:** reassign their courses first.

## Export and backups

- CSVs are intended for Excel and are quoted/escaped to reduce formula-injection issues.
- To back up, stop both local servers and copy `data/campusmind.db` to a secure location.
- For technical diagnosis use the FastAPI documentation at http://127.0.0.1:8000/docs and `scripts/04_RUN_TESTS.bat`.

## Boundaries

- One primary instructor per course; team-teaching and workload-by-contact-hours are not modeled.
- One room per exam; splitting large cohorts across rooms is not modeled.
- Current duty planner covers one or two invigilators per exam, with exact validity checks and a bounded search for balanced plans.
- No teacher/self-service login, automated email notifications, attendance or payroll integrations.
- Institution accounts, audit permissions, and internet hosting need production engineering before real deployment.
