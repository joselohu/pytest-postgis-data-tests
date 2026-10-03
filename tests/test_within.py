import pytest

from geo import haversine_m

ZONA_VIVA = {"lat": 14.6010, "lon": -90.5120}


@pytest.mark.parametrize("radius_m", [0, 250, 600, 2_000, 10_000])
def test_radius_search_matches_the_database(api, db, radius_m):
    expected = db.execute(
        """
        SELECT id
        FROM stations
        WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography, %(radius_m)s)
        ORDER BY id
        """,
        {**ZONA_VIVA, "radius_m": radius_m},
    ).fetchall()

    response = api.get("/stations/within", params={**ZONA_VIVA, "radius_m": radius_m})

    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == [row["id"] for row in expected]


def test_every_result_is_inside_the_radius(api):
    radius_m = 2_000

    stations = api.get("/stations/within", params={**ZONA_VIVA, "radius_m": radius_m}).json()

    assert stations
    for station in stations:
        distance = haversine_m(ZONA_VIVA["lat"], ZONA_VIVA["lon"], station["lat"], station["lon"])
        assert distance <= radius_m * 1.006


def test_zero_radius_returns_only_the_station_at_that_point(api):
    stations = api.get("/stations/within", params={**ZONA_VIVA, "radius_m": 0}).json()

    assert [s["name"] for s in stations] == ["Zona Viva"]


def test_radius_far_from_any_station_is_empty(api):
    middle_of_the_pacific = {"lat": 0, "lon": -140}

    assert api.get("/stations/within", params={**middle_of_the_pacific, "radius_m": 1_000}).json() == []


@pytest.mark.parametrize("radius_m", [-1, 50_001, "wide"])
def test_invalid_radius_is_rejected(api, radius_m):
    assert api.get("/stations/within", params={**ZONA_VIVA, "radius_m": radius_m}).status_code == 422
