def calculate_index(name, numerator, denominator):

    import numpy as np

    result = np.where(
        denominator != 0,
        numerator / denominator,
        np.nan
    )

    result = np.clip(result, -1, 1)

    print(f"{name} Created")

    print(f"Mean : {np.nanmean(result):.3f}")
    print(f"Max  : {np.nanmax(result):.3f}")
    print(f"Min  : {np.nanmin(result):.3f}")

    return result

with rasterio.open(config["bands"]["B02"]) as src:

    blue = src.read(1).astype(np.float32)
    profile = src.profile

with rasterio.open(config["bands"]["B03"]) as src:
    green = src.read(1).astype(np.float32)

with rasterio.open(config["bands"]["B04"]) as src:
    red = src.read(1).astype(np.float32)

with rasterio.open(config["bands"]["B08"]) as src:
    nir = src.read(1).astype(np.float32)

with rasterio.open(config["bands"]["B11"]) as src:
    swir1 = src.read(1).astype(np.float32)

with rasterio.open(config["bands"]["B12"]) as src:
    swir2 = src.read(1).astype(np.float32)\
    
ndvi = calculate_index(
    "NDVI",
    nir-red,
    nir+red
)

gndvi = calculate_index(
    "GNDVI",
    nir-green,
    nir+green
)

ndwi = calculate_index(
    "NDWI",
    green-nir,
    green+nir
)

ndmi = calculate_index(
    "NDMI",
    nir-swir1,
    nir+swir1
)

msi = swir1 / nir

mndwi = calculate_index(
    "MNDWI",
    green-swir1,
    green+swir1
)

nbr = calculate_index(
    "NBR",
    nir-swir2,
    nir+swir2
)

bsi = calculate_index(
    "BSI",
    (swir1+red)-(nir+blue),
    (swir1+red)+(nir+blue)
)

evi = 2.5 * (
    (nir-red) /
    (nir + 6*red - 7.5*blue + 1)
)

L = 0.5

savi = ((nir-red)/(nir+red+L))*(1+L)

def save_raster(output_file, image, profile):

    profile.update(
        dtype=rasterio.float32,
        count=1
    )

    with rasterio.open(
        output_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            image.astype(np.float32),
            1
        )

save_raster(...NDVI...)
save_raster(...NDWI...)
save_raster(...EVI...)
...




