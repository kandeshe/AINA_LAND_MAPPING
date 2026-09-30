import json
import requests
import rasterio
import numpy as np

from pathlib import Path
from pyproj import CRS, Transformer


SOIL_LAYERS = {

    "phh2o": "pH",
    "soc": "OrganicCarbon",
    "nitrogen": "Nitrogen",
    "clay": "Clay",
    "sand": "Sand",
    "silt": "Silt",
    "bdod": "BulkDensity",
    "cec": "CEC"

}


DEPTH = "0-5cm"

WGS84_CRS = "http://www.opengis.net/def/crs/EPSG/0/4326"

WCS_BASE = "https://maps.isric.org/mapserv"


def _get_wgs84_bbox(config, output_folder):

    reference_file = (
        output_folder.parent
        / "Analysis"
        / "B04.tif"
    )

    if not reference_file.exists():

        raise FileNotFoundError(
            "\nSentinel analysis reference raster not found:\n"
            f"{reference_file}"
        )

    with rasterio.open(reference_file) as src:

        bounds = src.bounds
        source_crs = src.crs

    transformer = Transformer.from_crs(
        source_crs,
        CRS.from_epsg(4326),
        always_xy=True
    )

    lon1, lat1 = transformer.transform(
        bounds.left,
        bounds.bottom
    )

    lon2, lat2 = transformer.transform(
        bounds.right,
        bounds.top
    )

    min_lon = min(lon1, lon2)
    max_lon = max(lon1, lon2)

    min_lat = min(lat1, lat2)
    max_lat = max(lat1, lat2)

    # Buffer so the 250 m SoilGrids cells surrounding
    # the selected LARA area are included.
    buffer_deg = 0.02

    min_lon -= buffer_deg
    max_lon += buffer_deg
    min_lat -= buffer_deg
    max_lat += buffer_deg

    return (
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )


def _download_wcs(
    layer,
    bbox,
    output_file
):

    min_lon, min_lat, max_lon, max_lat = bbox

    map_url = (
        f"{WCS_BASE}"
        f"?map=/map/{layer}.map"
    )

    params = [

        ("SERVICE", "WCS"),

        ("VERSION", "2.0.1"),

        ("REQUEST", "GetCoverage"),

        (
            "COVERAGEID",
            f"{layer}_{DEPTH}_mean"
        ),

        (
            "FORMAT",
            "GEOTIFF_INT16"
        ),

        (
            "SUBSET",
            f"X({min_lon},{max_lon})"
        ),

        (
            "SUBSET",
            f"Y({min_lat},{max_lat})"
        ),

        (
            "SUBSETTINGCRS",
            WGS84_CRS
        ),

        (
            "OUTPUTCRS",
            WGS84_CRS
        )

    ]

    response = requests.get(
        map_url,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    if (
        response.text[:20].lstrip().startswith("<")
        if response.content
        else False
    ):

        raise RuntimeError(
            "SoilGrids returned an XML response instead "
            "of a GeoTIFF."
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "wb"
    ) as f:

        f.write(response.content)

    # --------------------------------------------------
    # Validate downloaded raster
    # --------------------------------------------------

    with rasterio.open(output_file) as src:

        data = src.read(1)

        print(
            "Downloaded raster shape:",
            src.shape
        )

        print(
            "Downloaded raster CRS:",
            src.crs
        )

        print(
            "Downloaded raster bounds:",
            src.bounds
        )

        print(
            "Downloaded raster resolution:",
            src.res
        )

        print(
            "Raw minimum:",
            float(np.min(data))
        )

        print(
            "Raw maximum:",
            float(np.max(data))
        )

        print(
            "Raw mean:",
            float(np.mean(data))
        )


def download_soil_data(
    config,
    output_folder
):

    print(
        "\nDownloading SoilGrids Data using WCS...\n"
    )

    bbox = _get_wgs84_bbox(
        config,
        output_folder
    )

    print(
        "SoilGrids WGS84 bounding box:"
    )

    print(
        "Longitude:",
        bbox[0],
        "to",
        bbox[2]
    )

    print(
        "Latitude:",
        bbox[1],
        "to",
        bbox[3]
    )

    downloaded_files = {}

    for layer, folder in SOIL_LAYERS.items():

        print(
            f"\nDownloading {folder}..."
        )

        save_folder = (
            output_folder
            / folder
        )

        save_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        raw_tif = (
            save_folder
            / f"{folder}_soilgrids_wcs.tif"
        )

        aligned_tif = (
            save_folder
            / f"{folder}.tif"
        )

        metadata_file = (
            save_folder
            / f"{folder}_metadata.json"
        )

        try:

            _download_wcs(
                layer,
                bbox,
                raw_tif
            )

            metadata = {

                "source": "ISRIC SoilGrids 2.0 WCS",

                "property": layer,

                "coverage_id":
                    f"{layer}_{DEPTH}_mean",

                "depth": DEPTH,

                "prediction":
                    "mean",

                "requested_crs":
                    "EPSG:4326",

                "soilgrids_resolution_m":
                    250,

                "raw_file":
                    str(raw_tif),

                "aligned_file":
                    str(aligned_tif)

            }

            with open(
                metadata_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    metadata,
                    f,
                    indent=4
                )

            downloaded_files[layer] = {

                "raw_tif": raw_tif,

                "tif": aligned_tif,

                "metadata": metadata_file

            }

            print(
                f"{folder} WCS download completed."
            )

        except Exception as e:

            print(
                f"{folder} FAILED:"
            )

            print(e)

    print(
        "\nSoilGrids WCS Download Complete"
    )

    return downloaded_files
