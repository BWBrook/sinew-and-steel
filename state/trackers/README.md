# Trackers (Seed Fixture)

A campaign's session tracker, `campaigns/<slug>/state/trackers/session.yaml`,
holds session-level clocks and counters (Pressure, resources, scenes, optional
threats). Use `tools/play.py pressure`, `clock`, `scene` and `beat` for
transactional updates.
Pressure has scope, fired steps, pending character penalties and lasting crisis
effects; it is not a generic clock.
The seed tracker matches templates/tracker.yaml; add extra clocks as needed.
