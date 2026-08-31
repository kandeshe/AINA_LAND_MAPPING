from modules.terrain_visualization import (
    generate_dem_image,
    generate_hillshade
)
import numpy as np
from PIL import Image
import math
from pathlib import Path
from modules.terrain import generate_terrain
import planetary_computer
import pystac_client
import rasterio
from rasterio.mask import mask
from shapely.geometry import Point, mapping
from pyproj import CRS, Transformer
from modules.terrain_slope import generate_slope
from modules.hydrology import generate_hydrology
from modules.watershed import generate_watersheds
from modules.climate import generate_climate
from modules.land_suitability import generate_land_suitability
from modules.soil.soil import generate_soil
from modules.rainfall.rainfall import generate_rainfall
from modules.groundwater.groundwater import generate_groundwater
from modules.flood.flood import generate_flood
from cnn.predict import predict_scene

def run_analysis(
    LAT,
    LON,
    ANALYSIS_AREA_ACRES,
    manual_data=None
 ):
    # --------------------------------------------------
    # USER INPUT
    # --------------------------------------------------

    # LAT=float(
    #     input(
    #         "Latitude : "
    #     )
    # )

    # LON=float(
    #     input(
    #         "Longitude : "
    #     )
    # )
    # print()

    # ANALYSIS_AREA_ACRES=float(
    #     input(
    #         "Enter analysis area (Acres): "
    #     )
    # )

    PREVIEW_AREA_ACRES = 100
    OUTPUT_FOLDER = r"D:\LARA-project\data\satellite"

    START_DATE = "2024-01-01"
    END_DATE = "2026-12-31"

    # --------------------------------------------------

    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    # radius for 1 acre
    # ======================================
    utm_zone = int((LON + 180) / 6) + 1
    epsg = 32700 + utm_zone if LAT < 0 else 32600 + utm_zone

    wgs84 = CRS.from_epsg(4326)
    utm = CRS.from_epsg(epsg)

    to_utm = Transformer.from_crs(wgs84, utm, always_xy=True)
    to_wgs = Transformer.from_crs(utm, wgs84, always_xy=True)

    # Convert Lat/Lon to UTM coordinates FIRST
    x, y = to_utm.transform(LON, LAT)

    # ======================================
    # Analysis Area (1 Acre)
    # ======================================

    analysis_area_m2 = ANALYSIS_AREA_ACRES * 4046.856
    analysis_radius = math.sqrt(analysis_area_m2 / math.pi)
    print("Analysis radius (m):", analysis_radius)
    analysis_polygon = Point(x, y).buffer(analysis_radius)

    # ======================================
    # Preview Area (100 Acres)
    # ======================================

    preview_area_m2 = PREVIEW_AREA_ACRES * 4046.856
    preview_radius = math.sqrt(preview_area_m2 / math.pi)

    preview_polygon = Point(x, y).buffer(preview_radius)

    # Download uses preview area
    polygon = preview_polygon

    coords = []

    for px, py in polygon.exterior.coords:
        lon, lat = to_wgs.transform(px, py)
        coords.append((lon, lat))

    aoi = {
        "type": "Polygon",
        "coordinates": [coords]
    }
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        intersects=aoi,
        datetime=f"{START_DATE}/{END_DATE}",
        query={"eo:cloud_cover": {"lt": 10}},
    )

    items = list(search.items())

    if len(items) == 0:
        raise Exception("No Sentinel image found.")

    items = sorted(
        items,
        key=lambda x: x.datetime,
        reverse=True
    )

    item = items[0]
    print(item.id)

    # --------------------------------------------------
    # DOWNLOAD REQUIRED BANDS
    # --------------------------------------------------

    BANDS = {
        "B02": "Blue",
        "B03": "Green",
        "B04": "Red",
        "B08": "NIR",
        "B11": "SWIR1",
        "B12": "SWIR2",
        "SCL": "Scene Classification"
    }

    print("\nDownloading bands...\n")

    for band_name, description in BANDS.items():

        print(f"Downloading {band_name} ({description})...")

        band_folder = Path(OUTPUT_FOLDER) / band_name
        band_folder.mkdir(parents=True, exist_ok=True)

        asset = item.assets[band_name].href

        with rasterio.open(asset) as src:

            clipped, transform = mask(
                src,
                [mapping(polygon)],
                crop=True,
                filled=False
            )

            valid_mask = ~clipped.mask
            clipped = clipped.data

            meta = src.meta.copy()

            meta.update({
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": transform,
                "driver": "GTiff"
            })

            output_file = band_folder / f"{band_name}.tif"

            with rasterio.open(output_file, "w", **meta) as dst:
                dst.write(clipped)

        print(f"Saved -> {output_file}")

    print("\n===================================")
    print("All bands downloaded successfully.")
    print("===================================")

    print("\nCreating Analysis Dataset...\n")

    analysis_folder = Path(OUTPUT_FOLDER) / "Analysis"
    analysis_folder.mkdir(parents=True, exist_ok=True)

    for band in BANDS.keys():

        input_file = Path(OUTPUT_FOLDER) / band / f"{band}.tif"
        output_file = analysis_folder / f"{band}.tif"

        with rasterio.open(input_file) as src:

            clipped, transform = mask(
                src,
                [mapping(analysis_polygon)],
                crop=True,
                filled=False
            )

            meta = src.meta.copy()

            meta.update({
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": transform,
                "driver": "GTiff"
            })

            with rasterio.open(output_file, "w", **meta) as dst:
                dst.write(clipped)

    print("Analysis dataset created.")

    with rasterio.open(Path(OUTPUT_FOLDER) / "Analysis" / "B04.tif") as src:
        print("Analysis Raster Shape:", src.shape)
        print("Pixel Size:", src.res)

    # ======================================================
    # CREATE RGB IMAGE
    # ======================================================

    print("\nCreating RGB Image...")

    rgb_folder = Path(OUTPUT_FOLDER) / "RGB"
    rgb_folder.mkdir(parents=True, exist_ok=True)
    ndvi_folder = Path(OUTPUT_FOLDER) / "NDVI"
    ndvi_folder.mkdir(parents=True, exist_ok=True)
    ndwi_folder = Path(OUTPUT_FOLDER) / "NDWI"
    ndwi_folder.mkdir(parents=True, exist_ok=True)
    savi_folder = Path(OUTPUT_FOLDER) / "SAVI"
    savi_folder.mkdir(parents=True, exist_ok=True)

    # Read Red
    with rasterio.open(Path(OUTPUT_FOLDER) / "B04" / "B04.tif") as src:
        red = src.read(1, masked=True).astype(np.float32)
        meta = src.meta.copy()
    red_raw = red.copy()

    with rasterio.open(Path(OUTPUT_FOLDER) / "B08" / "B08.tif") as src:
        nir = src.read(1, masked=True).astype(np.float32)
    nir_raw = nir.copy()

    # Read Green
    with rasterio.open(Path(OUTPUT_FOLDER) / "B03" / "B03.tif") as src:
        green = src.read(1, masked=True).astype(np.float32)
    green_raw = green.copy()

    # Read Blue
    with rasterio.open(Path(OUTPUT_FOLDER) / "B02" / "B02.tif") as src:
        blue = src.read(1, masked=True).astype(np.float32)

    blue_raw = blue.copy()

    # ---------------------------------------
    # Load Downloaded SCL
    # ---------------------------------------

    # with rasterio.open(Path(OUTPUT_FOLDER) / "SCL" / "SCL.tif") as src:
    #     downloaded_scl = src.read(1)

    # print("Downloaded SCL:", np.unique(downloaded_scl))

    # ---------------------------------------
    # Load Analysis SCL
    # ---------------------------------------

    # with rasterio.open(Path(OUTPUT_FOLDER) / "Analysis" / "SCL.tif") as src:
    #     scl = src.read(1)

    # print("Analysis SCL:", np.unique(scl))

    # valid_scl = np.isin(
    #     scl,
    #     [
    #         4,  # Vegetation
    #         5,  # Bare Soil
    #         6,  # Water
    #         7   # Unclassified
    #     ]
    # )

    # print("Valid Pixels :", np.sum(valid_scl))
    # print("Total Pixels :", valid_scl.size)
    # print("Invalid Pixels :", valid_scl.size - np.sum(valid_scl))

    # ----------------------------------------------------
    # Stretch values to 0-255
    # ----------------------------------------------------

    def stretch(img):

        img = img.astype(np.float32)

        p2 = np.percentile(img, 2)
        p98 = np.percentile(img, 98)

        img = np.clip(img, p2, p98)

        if p98 > p2:
            img = ((img - p2) / (p98 - p2)) * 255
        else:
            img[:] = 0

        return img.astype(np.uint8)

    red = stretch(red)
    green = stretch(green)
    blue = stretch(blue)

    rgb = np.dstack((red, green, blue))

    rgb_image = Image.fromarray(rgb)

    rgb_path = rgb_folder / "rgb_preview.jpg"

    rgb_image = rgb_image.resize((1024, 1024), Image.Resampling.NEAREST)

    rgb_image.save(
        rgb_path,
        quality=95
    )
    print("RGB Image Saved")

    print(rgb_path)

        # ======================================================
    # CNN LAND-COVER ANALYSIS
    # ======================================================

    print("\n========== CNN LAND-COVER ANALYSIS ==========\n")

    cnn_result = None

    try:

        cnn_result = predict_scene(
            rgb_path,
            save_result=True
        )

        print(
            "CNN land-cover analysis completed."
        )

    except Exception as e:

        print(
            "CNN land-cover analysis failed:",
            e
        )

        cnn_result = {
            "status": "failed",
            "error": str(e)
        }

    # ==========================================
    # LOAD ANALYSIS BANDS
    # ==========================================

    with rasterio.open(Path(OUTPUT_FOLDER) / "Analysis" / "B04.tif") as src:
        red = src.read(1, masked=True).astype(np.float32)
        meta = src.meta.copy()
    red_raw = red.copy()

    with rasterio.open(Path(OUTPUT_FOLDER) / "Analysis" / "B08.tif") as src:
        nir = src.read(1, masked=True).astype(np.float32)
    nir_raw = nir.copy()

    with rasterio.open(Path(OUTPUT_FOLDER) / "Analysis" / "B03.tif") as src:
        green = src.read(1, masked=True).astype(np.float32)
    green_raw = green.copy()

    with rasterio.open(Path(OUTPUT_FOLDER) / "Analysis" / "B02.tif") as src:
        blue = src.read(1, masked=True).astype(np.float32)
    blue_raw = blue.copy()

    # calculate_ndvi

    np.seterr(divide="ignore", invalid="ignore")

    valid = (
        (nir_raw + red_raw) > 0
    )

    ndvi = np.full(red_raw.shape, np.nan, dtype=np.float32)

    ndvi[valid] = (
        (nir_raw[valid] - red_raw[valid]) /
        (nir_raw[valid] + red_raw[valid])
    )

    ndvi = np.clip(ndvi, -1, 1)

    print("Red min/max :", np.min(red_raw), np.max(red_raw))
    print("NIR min/max :", np.min(nir_raw), np.max(nir_raw))

    # save ndvi

    meta.update(
        {
            "dtype": "float32",
            "count": 1
        }
    )

    with rasterio.open(
        ndvi_folder / "ndvi.tif",
        "w",
        **meta
    ) as dst:

        dst.write(ndvi.astype(np.float32), 1)

        # create NDVI Image

        ndvi_img = ((ndvi + 1) / 2) * 255

    ndvi_img = ndvi_img.astype(np.uint8)

    Image.fromarray(ndvi_img).resize(
        (512, 512),
        Image.Resampling.NEAREST
    ).save(
        ndvi_folder / "ndvi_preview.jpg"
    )

    # statistics

    mean_ndvi = float(np.nanmean(ndvi))
    max_ndvi = float(np.nanmax(ndvi))
    min_ndvi = float(np.nanmin(ndvi))
    max_ndvi = float(np.max(ndvi))
    min_ndvi = float(np.min(ndvi))

    # save statistics

    with open(ndvi_folder / "ndvi_statistics.txt", "w") as f:

        f.write(f"Mean NDVI : {mean_ndvi:.3f}\n")
        f.write(f"Maximum NDVI : {max_ndvi:.3f}\n")
        f.write(f"Minimum NDVI : {min_ndvi:.3f}\n")

        print("\nNDVI Created Successfully")

    print("Mean :", mean_ndvi)

    print("Max :", max_ndvi)

    print("Min :", min_ndvi)

    # calulate NDWI
    np.seterr(divide="ignore", invalid="ignore")
    green_raw = green.copy()

    valid = (
        (green_raw + nir_raw) > 0
    )

    ndwi = np.full(green_raw.shape, np.nan, dtype=np.float32)

    ndwi[valid] = (
        (green_raw[valid] - nir_raw[valid]) /
        (green_raw[valid] + nir_raw[valid])
    )

    ndwi = np.clip(ndwi, -1, 1)
    # save geo tiff

    meta.update({
        "dtype": "float32",
        "count": 1
    })

    with rasterio.open(
        ndwi_folder / "ndwi.tif",
        "w",
        **meta
    ) as dst:
        dst.write(ndwi.astype(np.float32), 1)

    # preview image

    ndwi_img = ((ndwi + 1) / 2) * 255
    ndwi_img = ndwi_img.astype(np.uint8)

    Image.fromarray(ndwi_img).resize(
        (512, 512),
        Image.Resampling.NEAREST
    ).save(
        ndwi_folder / "ndwi_preview.jpg"
    )

    # water statistics

    water_pixels = np.sum(ndwi > 0.3)

    water_percent = (water_pixels / ndwi.size) * 100

    print("\n========== NDWI ==========")
    print("Water Pixels :", water_pixels)
    print("Water Percentage :", round(water_percent, 2), "%")

    # save report

    with open(ndwi_folder / "ndwi_statistics.txt", "w") as f:
        f.write(f"Water Pixels : {water_pixels}\n")
        f.write(f"Water Percentage : {water_percent:.2f}%\n")

    # savi

    # ======================================================
    # CALCULATE SAVI
    # ======================================================

    L = 0.5

    np.seterr(divide="ignore", invalid="ignore")

    valid = (
        (nir_raw + red_raw) > 0
    )

    savi = np.full(red_raw.shape, np.nan, dtype=np.float32)

    savi[valid] = (
        ((nir_raw[valid] - red_raw[valid]) * (1 + L))
        /
        (nir_raw[valid] + red_raw[valid] + L)
    )

    savi = np.clip(savi, -1, 1)

    # save geo tiff

    meta.update({
        "dtype": "float32",
        "count": 1
    })

    with rasterio.open(
        savi_folder / "savi.tif",
        "w",
        **meta
    ) as dst:
        dst.write(savi.astype(np.float32), 1)

    # create preview

    savi_img = ((savi + 1) / 2) * 255
    savi_img = savi_img.astype(np.uint8)

    Image.fromarray(savi_img).resize(
        (512, 512),
        Image.Resampling.NEAREST
    ).save(
        savi_folder / "savi_preview.jpg"
    )

    # statistics

    mean_savi = float(np.mean(savi))
    max_savi = float(np.max(savi))
    min_savi = float(np.min(savi))

    print("\n========== SAVI ==========")
    print("Mean SAVI :", round(mean_savi, 3))
    print("Max SAVI :", round(max_savi, 3))
    print("Min SAVI :", round(min_savi, 3))

    # save report

    with open(savi_folder / "savi_statistics.txt", "w") as f:
        f.write(f"Mean SAVI : {mean_savi:.3f}\n")
        f.write(f"Maximum SAVI : {max_savi:.3f}\n")
        f.write(f"Minimum SAVI : {min_savi:.3f}\n")

    print("\n========== LAND ANALYSIS ==========\n")

    valid_pixels = ~np.isnan(ndvi)

    total_pixels = np.sum(valid_pixels)

    water = np.sum(
        valid_pixels &
        (ndvi < 0)
    )

    barren = np.sum((ndvi >= 0) & (ndvi < 0.20))

    sparse = np.sum((ndvi >= 0.20) & (ndvi < 0.40))

    moderate = np.sum((ndvi >= 0.40) & (ndvi < 0.60))

    dense = np.sum(ndvi >= 0.60)

    print("Total Pixels :", total_pixels)

    print("Water :", water)

    print("Bare Land :", barren)

    print("Sparse Vegetation :", sparse)

    print("Moderate Vegetation :", moderate)

    print("Dense Vegetation :", dense)

    print()

    print("Water % :", round(water / total_pixels * 100, 2))

    print("Bare Land % :", round(barren / total_pixels * 100, 2))

    print("Sparse % :", round(sparse / total_pixels * 100, 2))

    print("Moderate % :", round(moderate / total_pixels * 100, 2))

    print("Dense % :", round(dense / total_pixels * 100, 2))

    report = Path(OUTPUT_FOLDER) / "NDVI" / "land_analysis.txt"

    with open(report, "w") as f:

        f.write("LAND ANALYSIS\n\n")

        f.write(f"Total Pixels : {total_pixels}\n")
        f.write(f"Water : {water}\n")
        f.write(f"Bare Land : {barren}\n")
        f.write(f"Sparse Vegetation : {sparse}\n")
        f.write(f"Moderate Vegetation : {moderate}\n")
        f.write(f"Dense Vegetation : {dense}\n\n")

        f.write(f"Water % : {water / total_pixels * 100:.2f}\n")
        f.write(f"Bare Land % : {barren / total_pixels * 100:.2f}\n")
        f.write(f"Sparse % : {sparse / total_pixels * 100:.2f}\n")
        f.write(f"Moderate % : {moderate / total_pixels * 100:.2f}\n")
        f.write(f"Dense % : {dense / total_pixels * 100:.2f}\n")

    print("Land Analysis Saved")

    # ======================================================
    # LAND CLASSIFICATION
    # ======================================================

    print("\n========== LAND CLASSIFICATION ==========\n")

    classification = np.zeros(ndvi.shape, dtype=np.uint8)

    # Water
    water_mask = (
        (ndvi < 0.05) &
        (ndwi > 0.00)
    )
    classification[water_mask] = 1

    # Bare Land
    classification[(ndvi >= 0) & (ndvi < 0.20)] = 2

    # Sparse Vegetation
    classification[(ndvi >= 0.20) & (ndvi < 0.40)] = 3

    # Moderate Vegetation
    classification[(ndvi >= 0.40) & (ndvi < 0.60)] = 4

    # Dense Vegetation
    classification[(ndvi >= 0.60)] = 5

    classification_folder = Path(OUTPUT_FOLDER) / "Classification"
    classification_folder.mkdir(parents=True, exist_ok=True)

    meta.update({
        "dtype": "uint8",
        "count": 1
    })

    with rasterio.open(
        classification_folder / "classification.tif",
        "w",
        **meta
    ) as dst:
        dst.write(classification, 1)

    rgb_class = np.zeros((classification.shape[0], classification.shape[1], 3), dtype=np.uint8)

    # Water - Blue
    rgb_class[classification == 1] = [0, 0, 255]

    # Bare Land - Brown
    rgb_class[classification == 2] = [210, 180, 140]

    # Sparse Vegetation - Yellow
    rgb_class[classification == 3] = [255, 255, 0]

    # Moderate Vegetation - Light Green
    rgb_class[classification == 4] = [0, 255, 0]

    # Dense Vegetation - Dark Green
    rgb_class[classification == 5] = [0, 100, 0]

    Image.fromarray(rgb_class).resize(
        (512, 512),
        Image.Resampling.NEAREST
    ).save(
        classification_folder / "classification_preview.png"
    )

    print("Classification completed.")

    classes = {
        1: "Water",
        2: "Bare Land",
        3: "Sparse Vegetation",
        4: "Moderate Vegetation",
        5: "Dense Vegetation"
    }

    print("\nClassification Summary\n")

    for i in range(1, 6):
        pixels = np.sum(classification == i)
        percent = (pixels / classification.size) * 100
        print(f"{classes[i]} : {percent:.2f}%")

    print("\n===== BAND STATISTICS =====")

    print("Red   :", np.min(red_raw), np.max(red_raw), np.mean(red_raw))
    print("Green :", np.min(green_raw), np.max(green_raw), np.mean(green_raw))
    print("Blue  :", np.min(blue_raw), np.max(blue_raw), np.mean(blue_raw))
    print("NIR   :", np.min(nir_raw), np.max(nir_raw), np.mean(nir_raw))

    config = {
        "lat": LAT,
        "lon": LON,

        "analysis_polygon_utm": analysis_polygon,

        "analysis_aoi_wgs84": aoi,

        "output_folder": OUTPUT_FOLDER,

        "catalog": catalog,

        "epsg": epsg
    }

    modules = [
    ("Terrain", generate_terrain),
    ("Hydrology", generate_hydrology),
    ("Watershed", generate_watersheds),
    ("Climate", generate_climate),
    ("Land Suitability", generate_land_suitability),
    ("Soil", generate_soil),
    ("Rainfall", generate_rainfall),
    ("Groundwater", generate_groundwater),
    ("Flood", generate_flood),
    ]

    for name, func in modules:
     try:
        print(f"Running {name}...")
        func(config)
        print(f"{name} completed.")
     except Exception as e:
        print(f"{name} FAILED: {e}")

    mean_ndwi = float(np.nanmean(ndwi))

    results = {
        "location": "Unknown",
        "latitude": LAT,
        "longitude": LON,
        "area": ANALYSIS_AREA_ACRES,
        "elevation": "-",

        "mean_ndvi": round(mean_ndvi, 3),
        "mean_ndwi": round(mean_ndwi, 3),
        "mean_savi": round(mean_savi, 3),
        "water_percent": round(water_percent, 2),

         # NEW
        "total_pixels": int(total_pixels),

        "land_cover": {
        "water": round((water / total_pixels) * 100, 2),
        "bare": round((barren / total_pixels) * 100, 2),
        "sparse": round((sparse / total_pixels) * 100, 2),
        "moderate": round((moderate / total_pixels) * 100, 2),
        "dense": round((dense / total_pixels) * 100, 2),
        },

         # ==================================================
        # CNN LAND-COVER INFORMATION
        # ==================================================

        "cnn_landcover": cnn_result,
        
        # Existing image paths
        "rgb_image": str(Path(OUTPUT_FOLDER) / "RGB" / "rgb_preview.jpg"),
        "ndvi_image": str(Path(OUTPUT_FOLDER) / "NDVI" / "ndvi_preview.jpg"),
        "ndwi_image": str(Path(OUTPUT_FOLDER) / "NDWI" / "ndwi_preview.jpg"),
        "savi_image": str(Path(OUTPUT_FOLDER) / "SAVI" / "savi_preview.jpg"),
        "classification_image": str(Path(OUTPUT_FOLDER) / "Classification" / "classification_preview.png"),
        "terrain": {
         "dem": str(Path(OUTPUT_FOLDER) / "Terrain" / "DEM.png"),
         "hillshade": str(Path(OUTPUT_FOLDER) / "Terrain" / "Hillshade.png"),
         "slope": str(Path(OUTPUT_FOLDER) / "Terrain" / "Slope.png"),
         "aspect": str(Path(OUTPUT_FOLDER) / "Terrain" / "Aspect.png"),
         "contours": str(Path(OUTPUT_FOLDER) / "Terrain" / "Contours.png"),
         "tri": str(Path(OUTPUT_FOLDER) / "Terrain" / "TRI.png"),
         },
        "hydrology_image": str(Path(OUTPUT_FOLDER) / "Hydrology" / "FlowAccumulation.png"),

        "groundwater_image": str(Path(OUTPUT_FOLDER) / "Groundwater" / "Groundwater_Depth.png"),

        "flood_image": str(Path(OUTPUT_FOLDER) / "Flood" / "FloodRisk.png"),   
          }

    return results


    


if __name__ == "__main__":
    run_analysis(
        LAT=-1.2921,
        LON=36.8219,
        ANALYSIS_AREA_ACRES=1
    )
