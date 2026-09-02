import numpy as np
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path
def generate_climate(config):

    print("\n==========================")
    print("Climate Module")
    print("==========================")

    terrain_folder = Path(config["output_folder"]) / "Terrain"

    climate_folder = Path(config["output_folder"]) / "Climate"

    climate_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    dem_file = terrain_folder / "DEM_UTM.tif"

    if not dem_file.exists():

        print("DEM not found.")

        return

    with rasterio.open(dem_file) as src:

        dem = src.read(1).astype(np.float32)

        profile = src.profile

        nodata = src.nodata

    if nodata is not None:

        dem[dem == nodata] = np.nan

    print("Estimating Temperature...")

    base_temperature = 30.0

    # Environmental lapse rate (6.5°C per 1000 m)
    temperature = base_temperature - (dem * 0.0065)

    temperature[np.isnan(dem)] = np.nan
    print("Saving Temperature Raster...")

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=np.nan
    )

    temperature_file = climate_folder / "Temperature.tif"

    with rasterio.open(
        temperature_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            temperature.astype(np.float32),
            1
        )

    print("Temperature Raster Saved")

    display = np.where(
        np.isnan(temperature),
        np.nan,
        temperature
    )

    plt.figure(figsize=(8,8))

    plt.imshow(
        display,
        cmap="coolwarm"
    )

    plt.colorbar(label="Temperature (°C)")

    plt.title("Estimated Temperature")

    plt.tight_layout()

    plt.savefig(
        climate_folder / "Temperature.png",
        dpi=300
    )
        
    plt.close()
    print("Climate analysis completed.")
    print("Temperature Image Saved")
    print("Generating Climate Zones...")

    climate = np.zeros(
        temperature.shape,
        dtype=np.uint8
    )

    climate[(temperature >= 35)] = 1
    climate[(temperature >= 30) & (temperature < 35)] = 2
    climate[(temperature >= 25) & (temperature < 30)] = 3
    climate[(temperature >= 20) & (temperature < 25)] = 4
    climate[(temperature < 20)] = 5

    climate[np.isnan(temperature)] = 0

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0
    )

    climate_file = climate_folder / "ClimateZones.tif"

    with rasterio.open(
        climate_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            climate,
            1
        )

    print("Climate Zone Raster Saved")

    print("Generating Climate Zone Image...")

    plt.figure(figsize=(8, 8))

    plt.imshow(
        climate,
        cmap="tab10",
        interpolation="nearest"
    )

    cbar = plt.colorbar(
        ticks=[1, 2, 3, 4, 5]
    )

    cbar.set_ticklabels([
        "Very Hot",
        "Hot",
        "Warm",
        "Mild",
        "Cool"
    ])

    plt.title("Climate Zones")

    plt.tight_layout()

    plt.savefig(
        climate_folder / "ClimateZones.png",
        dpi=300
    )

    plt.close()

    print("Climate Zone Image Saved")

    print("Calculating Climate Statistics...")

    valid = temperature[np.isfinite(temperature)]

    pixel_width = abs(profile["transform"].a)
    pixel_height = abs(profile["transform"].e)

    pixel_area = pixel_width * pixel_height

    stats_file = climate_folder / "Climate_Statistics.txt"

    zone_names = {
        1: "Very Hot",
        2: "Hot",
        3: "Warm",
        4: "Mild",
        5: "Cool"
    }

    with open(stats_file, "w") as f:

        f.write("CLIMATE ANALYSIS REPORT\n")
        f.write("===============================\n\n")

        f.write(f"Minimum Temperature : {valid.min():.2f} °C\n")
        f.write(f"Maximum Temperature : {valid.max():.2f} °C\n")
        f.write(f"Average Temperature : {valid.mean():.2f} °C\n")
        f.write(f"Median Temperature  : {np.median(valid):.2f} °C\n")
        f.write(f"Std. Deviation      : {valid.std():.2f} °C\n\n")

        f.write("Climate Zone Areas\n")
        f.write("-------------------------------\n")

        for zone in range(1, 6):

            pixels = np.sum(climate == zone)

            area_sqkm = (pixels * pixel_area) / 1000000

            f.write(
                f"{zone_names[zone]:12s}: "
                f"{pixels} pixels   "
                f"{area_sqkm:.4f} sq.km\n"
            )

    print("Climate Statistics Saved")

    print("\n========== CLIMATE SUMMARY ==========")
    print(f"Minimum Temperature : {valid.min():.2f} °C")
    print(f"Maximum Temperature : {valid.max():.2f} °C")
    print(f"Average Temperature : {valid.mean():.2f} °C")

    print("\nClimate Module Completed Successfully.")
