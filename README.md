# API and Data Tests with pytest and PostGIS

[![API and data tests](https://github.com/joselohu/pytest-postgis-data-tests/actions/workflows/tests.yml/badge.svg)](https://github.com/joselohu/pytest-postgis-data-tests/actions/workflows/tests.yml)

Tests that check a geospatial API against its own database. The system under test is a small bike-share service: stations are points, service areas are polygons, and the API answers questions such as "which stations are in this area" and "which stations are nearest to me".

An API test that only looks at the response can pass while the answer is wrong. These tests ask the database the same question with an independent query, and for distances they also check against maths that does not use PostGIS at all.

## What it covers

| File | What it verifies |
|---|---|
| `test_areas.py` | Station counts and area sizes match SQL. Stations per area match a spatial join. A station exactly on a boundary is included, a station outside every area is not. |
| `test_nearest.py` | Order and distance match PostGIS. Distances agree with a hand written haversine within the known sphere versus spheroid tolerance. Limits and invalid coordinates. |
| `test_within.py` | Radius search matches `ST_DWithin` for several radii, including zero and a point far from everything. |
| `test_station_write.py` | A created station is stored with the right coordinates and SRID, shows up in later queries, and rejected requests write nothing. |
| `test_data_quality.py` | Database only checks: valid geometries, WGS84 everywhere, no overlapping areas, no duplicate locations, spatial indexes present. |

53 tests, about two seconds.

## Run it

Requires Docker and Python 3.11 or newer.

```bash
docker compose up -d --build --wait
python -m venv .venv
.venv/Scripts/activate        # Windows; use "source .venv/bin/activate" elsewhere
pip install -r requirements-dev.txt
pytest
```

Useful variations:

```bash
pytest -m data_quality                              # database checks only
pytest --html=report.html --self-contained-html    # HTML report
docker compose down -v                              # stop and discard the data
```

The API listens on `localhost:8010` and PostgreSQL on `localhost:5433`. Override them with the `API_URL` and `DATABASE_URL` environment variables.

## How it is built

```
app/      FastAPI service with seven endpoints, SQL written by hand
db/       Schema and seed data, loaded when the database container starts
tests/    pytest suite, plus geo.py with the independent distance maths
```

Design decisions:

- **Three sources of truth.** The API response, a SQL query written separately from the API's query, and for distances a haversine function in plain Python. A bug has to exist in two of them in the same way to go unnoticed.
- **Tolerances are explained, not guessed.** PostGIS measures on the WGS84 spheroid and haversine on a sphere. They differ by up to about half a percent, so the comparison allows 0.6 percent and says why.
- **Boundary cases are in the seed data.** One station sits exactly on the edge of an area and one sits outside all of them, because that is where `ST_Contains` and `ST_Covers` give different answers.
- **Rejected writes are checked in the database.** A 409 or 422 is followed by a row count that proves nothing was inserted.
- **Tests clean up.** Stations created by a test are removed by a fixture, so the suite can run repeatedly against the same database.

## CI

GitHub Actions builds the stack with Docker Compose, runs the suite, uploads the HTML report and prints container logs if anything fails.

## Notes

The network is fictional and laid over Guatemala City with approximate coordinates. The database password in `docker-compose.yml` is a default for a local, throwaway container.
