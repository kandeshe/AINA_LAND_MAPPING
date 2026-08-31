import rasterio

from pathlib import Path

from rasterio.warp import (
    calculate_default_transform,
    reproject,
    Resampling
)


def reproject_dem(input_dem, terrain_folder, epsg):

    print("\nReprojecting DEM to UTM...")

    output_dem = Path(terrain_folder) / "DEM_UTM.tif"

    with rasterio.open(input_dem) as src:

        dst_crs = f"EPSG:{epsg}"

        # Preserve source NoData if available
        src_nodata = src.nodata

        if src_nodata is None:
            src_nodata = -9999.0

        # Calculate new transform
        transform, width, height = calculate_default_transform(
            src.crs,
            dst_crs,
            src.width,
            src.height,
            *src.bounds
        )

        # Update output profile
        profile = src.profile.copy()

        profile.update(
            driver="GTiff",
            crs=dst_crs,
            transform=transform,
            width=width,
            height=height,
            nodata=src_nodata,
            compress="lzw"
        )

        with rasterio.open(
            output_dem,
            "w",
            **profile
        ) as dst:

            for band in range(1, src.count + 1):

                reproject(
                    source=rasterio.band(src, band),
                    destination=rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src_nodata,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    dst_nodata=src_nodata,
                    resampling=Resampling.bilinear
                )

    print("DEM Reprojected Successfully")

    return output_dem
