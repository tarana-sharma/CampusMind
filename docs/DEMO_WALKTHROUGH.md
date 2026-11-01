# CampusMind — Operator Demonstration

1. Launch with `scripts/05_START_CAMPUSMIND.bat` after initial setup.
2. Open **Overview** and review course, room and examination window counts.
3. Open **Faculty & Teaching**; inspect a faculty profile and set an unavailable exam session.
4. Use the course assignment dropdown to change a primary instructor, then save.
5. Open **Examination Calendar** and inspect the session dates.
6. Open **Schedule Builder**, generate a timetable, review the draft, and publish it.
7. Open **Invigilation Duties**, select balanced planning, generate duties, and examine the staff workload chart.
8. Try a manual replacement; a conflicting or prohibited assignment should be rejected.
9. Publish duties; download the official exam schedule and teacher duty CSV files.
10. Review saved plans in **Reports & Activity**.

For technical assessment: code lives in `backend/app/algorithms`. Graph coloring avoids exam conflicts, Branch and Bound allocates exam rooms, and a constraint-aware duty assignment optimizer allocates invigilators. See `ALGORITHM_ANALYSIS.md` for algorithm descriptions. The normal staff interface deliberately avoids runtime/complexity graphs.
