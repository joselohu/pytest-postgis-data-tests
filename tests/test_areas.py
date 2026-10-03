import pytest


def test_station_counts_match_the_database(api, db):
    expected = db.execute(
        """
        SELECT a.id, count(s.id) AS station_count
        FROM service_areas a
        LEFT JOIN stations s ON ST_Covers(a.geom, s.geom)
        GROUP BY a.id
        """
    ).fetchall()

    areas = api.get("/areas").json()

    assert {a["id"]: a["station_count"] for a in areas} == {r["id"]: r["station_count"] for r in expected}


def test_area_size_matches_a_geodesic_calculation(api, db):
    expected = {
        row["id"]: row["km2"]
        for row in db.execute("SELECT id, ST_Area(geom::geography) / 1e6 AS km2 FROM service_areas")
    }

    for area in api.get("/areas").json():
        assert area["area_km2"] == pytest.approx(expected[area["id"]], abs=0.001)


def test_stations_in_area_match_a_spatial_query(api, db):
    for area in db.execute("SELECT id FROM service_areas").fetchall():
        expected = db.execute(
            """
            SELECT s.id
            FROM stations s
            JOIN service_areas a ON ST_Covers(a.geom, s.geom)
            WHERE a.id = %s
            ORDER BY s.id
            """,
            (area["id"],),
        ).fetchall()

        response = api.get(f"/areas/{area['id']}/stations")

        assert response.status_code == 200
        assert [s["id"] for s in response.json()] == [row["id"] for row in expected]


def test_station_on_the_boundary_belongs_to_the_area(api, db):
    """ST_Contains would leave a point on the edge out; the API is expected to include it."""
    area = db.execute("SELECT id FROM service_areas WHERE name = 'Zona 10'").fetchone()

    names = [s["name"] for s in api.get(f"/areas/{area['id']}/stations").json()]

    assert "Borde Zona 10" in names


def test_station_outside_every_area_is_listed_nowhere(api):
    listed = {
        station["name"]
        for area in api.get("/areas").json()
        for station in api.get(f"/areas/{area['id']}/stations").json()
    }

    assert "Aeropuerto La Aurora" not in listed


def test_unknown_area_returns_404(api):
    response = api.get("/areas/999999/stations")

    assert response.status_code == 404
    assert response.json() == {"detail": "Service area not found"}
