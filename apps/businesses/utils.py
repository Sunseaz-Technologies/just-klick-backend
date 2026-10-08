import requests

def get_coordinates(location):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
        }
        headers = {
            "User-Agent": "JustKlick/1.0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()

        if data:
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            return float(lat), float(lon)
        return None, None

    except Exception:
        return None, None