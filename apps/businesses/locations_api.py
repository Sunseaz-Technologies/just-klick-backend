import requests
from ninja import Router

router = Router()

@router.get("/search/")
def search_locations(request, q: str):
    url = "https://photon.komoot.io/api/"
    params = {
        "q": q,
        "limit": 10,
        "lang": "en",
        "lat": 20.5937,
        "lon": 78.9629,
    }
    headers = {"User-Agent": "JustKlick/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
    except Exception:
        return []

    results = []
    for item in data.get("features", []):
        props = item.get("properties", {})
        coords = item.get("geometry", {}).get("coordinates", [])
        if len(coords) == 2:
            name_parts = list(filter(None, [
                props.get("name"),
                props.get("city"),
                props.get("state"),
                props.get("country"),
            ]))
            results.append({
                "name": ", ".join(name_parts),
                "lat": float(coords[1]),
                "lng": float(coords[0]),
            })

    return results