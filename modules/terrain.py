
import planetary_computer
import rasterio
import numpy as np
from pathlib import Path
from rasterio.mask import mask
from rasterio.merge import merge
from shapely.geometry import mapping
from rasterio.warp import transform_geom
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from modules.terrain_visualization import ( 
    generate_dem_image,
    generate_hillshade
)
from modules.terrain_reproject import reproject_dem
from modules.terrain_slope import generate_slope
from modules.terrain_aspect import generate_aspect
from modules.terrain_contours import generate_contours
from modules.terrain_tri import generate_tri
def generate_terrain(config):

    lat = config["lat"]
    lon = config["lon"]

    analysis_polygon = config["analysis_polygon_utm"]
    aoi = config["analysis_aoi_wgs84"]

    output_folder = config["output_folder"]
    catalog = config["catalog"]
    epsg = config["epsg"]
    terrain_folder = Path(output_folder) / "Terrain"
    terrain_folder.mkdir(parents=True, exist_ok=True)

    print("\n==========================")
    print("Terrain Module")
    print("==========================")

    print("Latitude :", lat)
    print("Longitude:", lon)

    print("\nSearching DEM...")

    search = catalog.search(
        collections=["cop-dem-glo-30"],
        intersects=aoi
    )

    items = list(search.items())

    print("DEM Tiles Found :", len(items))

    if len(items) == 0:
        print("No DEM found.")
        return

    print("\nAvailable DEM Tiles")
    for item in items:
     print(item.id)

    # ============================================
    # Download DEM Tiles
    # ============================================

    print("\nDownloading DEM Tiles...")

    dem_files = []

    for index, item in enumerate(items):

        print(f"Downloading : {item.id}")

        if "data" not in item.assets:
            print("DEM asset missing.")
            continue

        asset = item.assets["data"]

        signed_url = planetary_computer.sign(asset.href)

        tile_path = terrain_folder / f"DEM_Tile_{index}.tif"

        try:
            with rasterio.open(signed_url) as src:

                profile = src.profile

                with rasterio.open(
                    tile_path,
                    "w",
                    **profile
                ) as dst:

                    dst.write(src.read())

            dem_files.append(tile_path)

        except Exception as e:
            print(f"Failed to download {item.id}")
            print(e)
    print("\nDownloaded", len(dem_files), "DEM Tiles")

    if len(dem_files) == 0:
        print("No DEM files downloaded.")
        return

    print(f"\nSuccessfully downloaded {len(dem_files)} tiles")

    # ============================================
    # Merge DEM Tiles
    # ============================================

    print("\nCreating DEM Mosaic...")

    src_files = []

    for file in dem_files:
        src_files.append(rasterio.open(file))

    mosaic, transform = merge(src_files)

    profile = src_files[0].profile.copy()

    profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=transform
    )

    merged_dem = terrain_folder / "DEM_Full.tif"

    with rasterio.open(
        merged_dem,
        "w",
        **profile
    ) as dst:

        dst.write(mosaic)

    for src in src_files:
        src.close()

    print("DEM Mosaic Created")

    # ============================================
    # Verify Mosaic
    # ============================================

    with rasterio.open(merged_dem) as src:

        print("\n========== DEM INFORMATION ==========")

        print("CRS        :", src.crs)
        print("Bounds     :", src.bounds)
        print("Resolution :", src.res)
        print("Width      :", src.width)
        print("Height     :", src.height)

    # ============================================
    # Clip DEM Mosaic
    # ============================================

    print("\nClipping DEM...")

    clipped_dem = terrain_folder / "DEM.tif"

    with rasterio.open(merged_dem) as src:

        # Convert AOI to the DEM CRS if required
        geometry = transform_geom(
            "EPSG:4326",
            src.crs,
            aoi
        )

        clipped, transform = mask(
            src,
            [geometry],
            crop=True,
            nodata=src.nodata
        )

        profile = src.profile.copy()

        profile.update(
            driver="GTiff",
            height=clipped.shape[1],
            width=clipped.shape[2],
            transform=transform
        )

    with rasterio.open(
        clipped_dem,
        "w",
        **profile
    ) as dst:

        dst.write(clipped)

    print("DEM Clipped Successfully")

    dem_utm = reproject_dem(
        clipped_dem,
        terrain_folder,
        epsg
    )

        # ============================================
    # Elevation Statistics
    # ============================================

    print("\nCalculating Elevation Statistics...")

    with rasterio.open(dem_utm) as src:

        dem = src.read(1).astype(np.float32)

        nodata = src.nodata

        if nodata is not None:
            dem[dem == nodata] = np.nan

        valid = dem[np.isfinite(dem)]

    if valid.size == 0:
        print("No valid DEM pixels found.")
        return

    print("\n========== TERRAIN SUMMARY ==========")
    print(f"Minimum Elevation : {valid.min():.2f} m")
    print(f"Maximum Elevation : {valid.max():.2f} m")
    print(f"Average Elevation : {valid.mean():.2f} m")
    print(f"Median Elevation  : {np.median(valid):.2f} m")
    print(f"Std Deviation     : {np.std(valid):.2f} m")
    print(f"Elevation Range   : {(valid.max() - valid.min()):.2f} m")

   

    generate_dem_image(dem_utm, terrain_folder)

    generate_hillshade(dem_utm, terrain_folder)

    generate_slope(dem_utm, terrain_folder)

    generate_aspect(
        dem_utm,
        terrain_folder
    )

    generate_contours(
      dem_utm,
      terrain_folder
    )
    
    generate_tri(
    dem_utm,
    terrain_folder
    )
