import calendar
import json
import requests


def download_rainfall_data(config, output_folder):

    print("\nDownloading Rainfall Data...\n")

    latitude = config.get("latitude", config.get("lat"))
    longitude = config.get("longitude", config.get("lon"))

    rainfall = {}

    for month in range(1, 13):

        month_name = calendar.month_name[month]

        print(f"Downloading {month_name}...")

        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            "&start_date=2024-"
            f"{month:02d}-01"
            "&end_date=2024-"
            f"{month:02d}-28"
            "&daily=precipitation_sum"
            "&timezone=auto"
        )

        try:

            response = requests.get(
                url,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            save_file = output_folder / f"{month_name}.json"

            with open(save_file, "w") as f:
                json.dump(
                    data,
                    f,
                    indent=4
                )

            rainfall_values = data.get(
                "daily",
                {}
            ).get(
                "precipitation_sum",
                []
            )

            total = sum(
                x for x in rainfall_values
                if x is not None
            )

            rainfall[month_name] = total

            print(
                f"{month_name} : {total:.2f} mm"
            )

        except Exception as e:

            print(
                f"{month_name} download failed"
            )

            print(e)

            rainfall[month_name] = 0

    print("\nRainfall Download Completed")

    return rainfall
