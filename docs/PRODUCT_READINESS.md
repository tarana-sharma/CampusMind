# Production / Sale Readiness — Required Before Real Institutional Use

The bundled product is a working local pilot. It is **not yet suitable for direct sale as a ready-to-deploy production university system** without additional work.

## Security and privacy (blockers)

- Authentication, multi-factor authentication where required, password reset, secure sessions, administrator and faculty roles, least-privilege authorization.
- Institution isolation if supporting multiple campuses, and permission checks for *every* API endpoint.
- Audit log with actor identity for all timetable, enrollment, faculty, and publication edits.
- Legal review and lawful handling of student and employee personal data, retention/deletion, privacy notice, purpose limitation, secure data import and export.
- Database access security, transport encryption, secret management, backups encrypted at rest, appropriate deployment infrastructure, patching and vulnerability review.

## Reliability (blockers)

- Controlled database migrations, automated backup and recovery with restore drills, meaningful operational monitoring and error logging.
- Load/performance testing with each institution's dataset size, including algorithm search caps and worker queues for long jobs.
- Administrative acceptance tests across real academic policy variants; time-zone/DST, room outages, public holidays, exam durations, special accommodations.
- Formal approval workflow with user identities; version history and rollback of published timetables and duty rosters.

## Advanced workflows (institution dependent)

- Multi-room examinations, parallel lab sections, additional room invigilators and shift handover.
- Departmental restrictions, staff leave integration, teaching/workload contracts, eligible subject invigilator policies.
- CSV / SIS / LMS imports, academic calendar, internal notifications and approved external exports.
- Separate staff-facing self-service access for duty acceptance, change requests and substitution approvals.
- PDF/print layouts, branding and institution preferences.

## What is already implemented

- Faculty directory and teaching assignments, leave/unavailability blocks, duty limits.
- Automated timetable draft/publication; room and student/instructor collision checks.
- Constraint-validated invigilation planning, manual reassignment, approval/publishing and CSV reports.
- Scenario revision checks and preserved official snapshots.
- Automated Python algorithm/integration tests.

Prioritize the listed blockers before entering real university records or exposing the server beyond localhost.
