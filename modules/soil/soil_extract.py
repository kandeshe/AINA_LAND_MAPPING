import numpy as np
import rasterio


def _get_center_coordinates(
    reference_file
):

    """
    Get the center latitude/longitude of the
    Sentinel analysis area.
    """

    with rasterio.open(
        reference_file
    ) as src:

        center_x = (
            (src.bounds.left + src.bounds.right)
            / 2
        )

        center_y = (
            (src.bounds.bottom + src.bounds.top)
            / 2
        )

        source_crs = src.crs

        if (
            source_crs
            and source_crs.to_epsg() == 4326
        ):

            return center_x, center_y

        from pyproj import Transformer

        transformer = Transformer.from_crs(
            source_crs,
            "EPSG:4326",
            always_xy=True
        )

        lon, lat = transformer.transform(
            center_x,
            center_y
        )

        return lon, lat


def _find_soil_value(
    dataset,
    lon,
    lat
):

    """
    Find the SoilGrids value near the analysis centre.

    SoilGrids resolution is approximately 250 m,
    while LARA's Sentinel grid is 10 m.

    Therefore we use the SoilGrids source pixel/
    nearby valid pixels rather than inventing
    10 m soil detail.
    """

    # ---------------------------------------------------------
    # Convert WGS84 coordinate to SoilGrids raster CRS
    # ---------------------------------------------------------

    from pyproj import Transformer

    transformer = Transformer.from_crs(
        "EPSG:4326",
        dataset.crs,
        always_xy=True
    )

    x, y = transformer.transform(
        lon,
        lat
    )

    # ---------------------------------------------------------
    # Find containing raster pixel
    # ---------------------------------------------------------

    row, col = dataset.index(
        x,
        y
    )

    data = dataset.read(
        1
    ).astype(
        np.float32
    )

    height, width = data.shape

    # ---------------------------------------------------------
    # Search a small neighbourhood.
    #
    # This protects us when the exact centre pixel is
    # represented as 0/nodata.
    # ---------------------------------------------------------

    search_radius = 2

    r1 = max(
        0,
        row - search_radius
    )

    r2 = min(
        height,
        row + search_radius + 1
    )

    c1 = max(
        0,
        col - search_radius
    )

    c2 = min(
        width,
        col + search_radius + 1
    )

    window = data[
        r1:r2,
        c1:c2
    ]

    # ---------------------------------------------------------
    # SoilGrids WCS output seen in this project uses 0
    # where there is no useful soil observation.
    #
    # Treat zero as nodata for this extraction.
    # ---------------------------------------------------------

    valid = window[
        np.isfinite(window)
        & (window > 0)
    ]

    if valid.size == 0:

        return np.nan

    # Representative local SoilGrids value
    return float(
        np.median(valid)
    )


def extract_soil_layers(
    soil_files,
    output_folder
):

    print(
        "\nExtracting Soil Layers...\n"
    )

    layers = {}

    # ==========================================================
    # SENTINEL REFERENCE RASTER
    # ==========================================================

    reference_file = (
        output_folder.parent
        / "Analysis"
        / "B04.tif"
    )

    if not reference_file.exists():

        raise FileNotFoundError(
            "\nSentinel analysis raster not found:\n"
            f"{reference_file}"
        )

    with rasterio.open(
        reference_file
    ) as reference:

        reference_profile = (
            reference.profile.copy()
        )

        reference_height = (
            reference.height
        )

        reference_width = (
            reference.width
        )

        reference_transform = (
            reference.transform
        )

        reference_crs = (
            reference.crs
        )

        print(
            "Reference shape:",
            reference.shape
        )

        print(
            "Reference CRS:",
            reference_crs
        )

        print(
            "Reference transform:",
            reference_transform
        )

    # ==========================================================
    # CENTRE OF LARA ANALYSIS
    # ==========================================================

    lon, lat = _get_center_coordinates(
        reference_file
    )

    print(
        "Analysis centre:"
    )

    print(
        "Longitude:",
        lon
    )

    print(
        "Latitude:",
        lat
    )

    # ==========================================================
    # PROCESS EACH SOIL LAYER
    # ==========================================================

    for layer_name, files in soil_files.items():

        print(
            f"\nProcessing SoilGrids layer: "
            f"{layer_name}"
        )

        try:

            raw_tif = files["raw_tif"]

            aligned_tif = files["tif"]

            # --------------------------------------------------
            # OPEN SOILGRIDS RASTER
            # --------------------------------------------------

            with rasterio.open(
                raw_tif
            ) as src:

                print(
                    "Source shape:",
                    src.shape
                )

                print(
                    "Source CRS:",
                    src.crs
                )

                print(
                    "Source resolution:",
                    src.res
                )

                value = _find_soil_value(
                    src,
                    lon,
                    lat
                )

            # --------------------------------------------------
            # CHECK VALUE
            # --------------------------------------------------

            if np.isnan(value):

                print(
                    f"{layer_name}: "
                    "No valid SoilGrids value found."
                )

                continue

            print(
                f"{layer_name} selected SoilGrids value:",
                value
            )

            # --------------------------------------------------
            # CREATE LARA-ALIGNED REPRESENTATION
            #
            # IMPORTANT:
            # The same SoilGrids value is repeated over the
            # Sentinel analysis grid because SoilGrids does
            # not provide independent 10 m soil measurements.
            # --------------------------------------------------

            raster = np.full(
                (
                    reference_height,
                    reference_width
                ),
                value,
                dtype=np.float32
            )

            # --------------------------------------------------
            # SAVE
            # --------------------------------------------------

            profile = (
                reference_profile.copy()
            )

            profile.update({

                "driver": "GTiff",

                "height": reference_height,

                "width": reference_width,

                "count": 1,

                "dtype": "float32",

                "crs": reference_crs,

                "transform": reference_transform,

                "nodata": np.nan

            })

            with rasterio.open(
                aligned_tif,
                "w",
                **profile
            ) as dst:

                dst.write(
                    raster,
                    1
                )

            print(
                "Saved aligned raster ->",
                aligned_tif
            )

            # --------------------------------------------------
            # STORE
            # --------------------------------------------------

            layers[layer_name] = {

                "data": raster,

                "profile": profile,

                "value": value,

                "file": aligned_tif,

                "raw_file": raw_tif

            }

        except Exception as e:

            print(
                f"Failed : {layer_name}"
            )

            print(
                "Error:",
                e
            )

    print(
        "\nExtraction Complete"
    )

    return layers
