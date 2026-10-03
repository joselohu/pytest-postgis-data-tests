import pytest

from geo import SPHERE_VS_SPHEROID_TOLERANCE, haversine_m

# Plaza de la Constitucion, a few metres from the "Parque Central" station.
ORIGIN = {"lat": 14.6417, "lon": -90.5132}


def test_nearest_matches_database_order_and_distance(api, db):
    expected = db.execute(
        """
        SELECT id, ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography) AS distance_m
        FROM stations
        ORDER BY distance_m, id
        LIMIT 5
        """,
        ORIGIN,
    ).fetchall()

    stations = api.get("/stations/nearest", params={**ORIGIN, "limit": 5}).json()

    assert [s["id"] for s in stations] == [row["id"] for row in expected]
    for station, row in zip(stations, expected):
        assert station["distance_m"] == pytest.approx(row["distance_m"], abs=0.1)


def test_distances_agree_with_an_independent_haversine(api):
    stations = api.get("/stations/nearest", params={**ORIGIN, "limit": 50}).json()

    for station in stations:
        expected = haversine_m(ORIGIN["lat"], ORIGIN["lon"], station["lat"], station["lon"])
        assert station["distance_m"] == pytest.approx(expected, rel=SPHERE_VS_SPHEROID_TOLERANCE, abs=1)


def test_results_are_sorted_closest_first(api):
    distances = [s["distance_m"] for s in api.get("/stations/nearest", params={**ORIGIN, "limit": 50}).json()]

    assert distances == sorted(distances)
    assert distances[0] < 50  # Parque Central is next to the origin


def test_default_limit_is_three(api):
    assert len(api.get("/stations/nearest", params=ORIGIN).json()) == 3


@pytest.mark.parametrize("limit", [1, 4, 10])
def test_limit_is_respected(api, limit):
    assert len(api.get("/stations/nearest", params={**ORIGIN, "limit": limit}).json()) == limit


@pytest.mark.parametrize(
    "params",
    [
        {"lat": 90.1, "lon": -90.5},
        {"lat": -90.1, "lon": -90.5},
        {"lat": 14.6, "lon": 180.1},
        {"lat": 14.6, "lon": -180.1},
        {"lat": "north", "lon": -90.5},
        {"lon": -90.5},
        {"lat": 14.6, "lon": -90.5, "limit": 0},
        {"lat": 14.6, "lon": -90.5, "limit": 51},
    ],
    ids=["lat-too-high", "lat-too-low", "lon-too-high", "lon-too-low", "lat-not-a-number", "lat-missing", "limit-zero", "limit-too-high"],
)
def test_invalid_input_is_rejected(api, params):
    assert api.get("/stations/nearest", params=params).status_code == 422
