import requests


def get_location_name(lat, lon):

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "accept-language": "en"
    }

    headers = {
    "User-Agent": "LARA Agricultural Analysis",
    "Accept-Language": "en"
   }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        address = data.get("address", {})

        return {

            "display_name": data.get(
                "display_name",
                "Unknown"
            ),

            "place": (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("hamlet")
                or "Unknown"
            ),

            "district": (
                address.get("county")
                or address.get("district")
                or "Unknown"
            ),

            "region": (
                address.get("state")
                or address.get("region")
                or "Unknown"
            ),

            "country": address.get(
                "country",
                "Unknown"
            ),

            "postcode": address.get(
                "postcode",
                ""
            )

        }

    except Exception as e:

        print("Location Error:", e)

        return {

            "display_name": "Unknown",

            "place": "Unknown",

            "district": "Unknown",

            "region": "Unknown",

            "country": "Unknown",

            "postcode": ""

        }
