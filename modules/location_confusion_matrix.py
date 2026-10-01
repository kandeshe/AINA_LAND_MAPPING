from __future__ import annotations

import json
import math
import re
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.errors import RasterioIOError, WindowError
from rasterio.windows import Window, from_bounds
from rasterio.warp import transform_bounds

CLASS_NAMES = ["Water", "Vegetation", "Other land"]
CLASS_TO_INDEX = {name: i for i, name in enumerate(CLASS_NAMES)}

# EuroSAT CNN labels -> LARA's three evaluation groups.
_CNN_CLASS_MAP = {
    "annualcrop": "Vegetation",
    "forest": "Vegetation",
    "herbaceousvegetation": "Vegetation",
    "pasture": "Vegetation",
    "permanentcrop": "Vegetation",
    "river": "Water",
    "sealake": "Water",
    "water": "Water",
    "permanentwater": "Water",
    "highway": "Other land",
    "industrial": "Other land",
    "residential": "Other land",
    "builtup": "Other land",
    "built-up": "Other land",
    "bare": "Other land",
    "baresparsevegetation": "Other land",
    "sparsevegetation": "Other land",
    "otherland": "Other land",
    "nonvegetation": "Other land",
}

# ESA WorldCover 2021 class code -> broad evaluation class.
# 10 Tree cover; 20 Shrubland; 30 Grassland; 40 Cropland; 50 Built-up;
# 60 Bare/sparse vegetation; 70 Snow/ice; 80 Permanent water; 90 Wetland;
# 95 Mangroves; 100 Moss/lichen. Code 0 and unrecognized codes are ignored.
_WORLDCOVER_CLASS_MAP = {
    10: "Vegetation",
    20: "Vegetation",
    30: "Vegetation",
    40: "Vegetation",
    50: "Other land",
    60: "Other land",
    70: "Other land",
    80: "Water",
    90: "Vegetation",
    95: "Vegetation",
    100: "Vegetation",
}

_WORLDCOVER_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
    "v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
)


def _normalise_label(value: Any) -> str:
    """Normalise a prediction label to a broad evaluation class."""
    if isinstance(value, dict):
        for key in ("label", "class", "name", "prediction", "value"):
            if key in value:
                value = value[key]
                break
    label = str(value or "").strip()
    key = re.sub(r"[\s_]+", "", label).lower()
    if key in _CNN_CLASS_MAP:
        return _CNN_CLASS_MAP[key]
    # Accept class labels that may already have been grouped upstream.
    if key in {"water"}:
        return "Water"
    if key in {"vegetation", "plantcover"}:
        return "Vegetation"
    if key in {"otherland", "nonvegetation", "builtup"}:
        return "Other land"
    return ""


def _find_records(payload: Any) -> Tuple[List[dict], dict]:
    """Find the CNN tile records and top-level metadata in common JSON layouts."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)], {}
    if not isinstance(payload, dict):
        return [], {}

    for key in ("predictions", "tile_predictions", "tiles", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)], payload
        if isinstance(value, dict):
            records = []
            for tile_name, item in value.items():
                if isinstance(item, dict):
                    item = dict(item)
                    item.setdefault("tile", tile_name)
                    records.append(item)
            if records:
                return records, payload
    # Some outputs store predictions directly as a mapping of tile names to rows.
    records = []
    for tile_name, item in payload.items():
        if isinstance(item, dict) and any(k in item for k in ("prediction", "class", "label")):
            row = dict(item)
            row.setdefault("tile", tile_name)
            records.append(row)
    return records, payload


def _image_dimensions(metadata: dict, records: List[dict], tile_size: int) -> Tuple[int, int]:
    image_size = metadata.get("image_size") or metadata.get("image_dimensions")
    width = height = None
    if isinstance(image_size, dict):
        width = image_size.get("width") or image_size.get("w")
        height = image_size.get("height") or image_size.get("h")
    elif isinstance(image_size, (list, tuple)) and len(image_size) >= 2:
        width, height = image_size[0], image_size[1]
    width = width or metadata.get("image_width") or metadata.get("width")
    height = height or metadata.get("image_height") or metadata.get("height")

    # This project normally predicts on a 1024x1024 resized RGB preview.
    # If metadata is absent, infer a minimally sufficient square dimension.
    if not width or not height:
        coords = []
        for row in records:
            try:
                coords.append((float(row.get("x", 0)), float(row.get("y", 0))))
            except (TypeError, ValueError):
                continue
        if coords:
            max_x = max(x for x, _ in coords)
            max_y = max(y for _, y in coords)
            if max_x <= 16 and max_y <= 16:
                width = height = max(1, int(max(max_x, max_y) + 1) * tile_size)
            else:
                width = max(1, int(max_x + tile_size))
                height = max(1, int(max_y + tile_size))
        else:
            width = height = 1024
    return int(width), int(height)


def _tile_grid_coordinates(records: List[dict], image_width: int, image_height: int,
                           tile_size: int) -> bool:
    """Return True when x/y appear to be grid indices rather than pixel offsets."""
    coords = []
    for row in records:
        try:
            coords.append((float(row.get("x", row.get("col", 0))),
                           float(row.get("y", row.get("row", 0)))))
        except (TypeError, ValueError):
            pass
    if not coords:
        return False
    max_x = max(x for x, _ in coords)
    max_y = max(y for _, y in coords)
    return (
        max_x <= image_width / tile_size
        and max_y <= image_height / tile_size
        and all(float(x).is_integer() and float(y).is_integer() for x, y in coords)
    )


def _safe_location_name(latitude: float, longitude: float) -> str:
    def part(value: float) -> str:
        text = f"{value:.6f}"
        return text.replace("-", "m").replace(".", "p")
    return f"lat_{part(latitude)}_lon_{part(longitude)}"


def _worldcover_tile_name(latitude: float, longitude: float) -> str:
    """Return the ESA WorldCover 3-degree tile name for a coordinate."""
    south_or_west = math.floor(latitude / 3.0) * 3
    west = math.floor(longitude / 3.0) * 3
    if south_or_west < 0:
        lat_tag = f"S{abs(south_or_west):02d}"
    else:
        lat_tag = f"N{south_or_west:02d}"
    if west < 0:
        lon_tag = f"W{abs(west):03d}"
    else:
        lon_tag = f"E{west:03d}"
    return lat_tag + lon_tag


def _resolve_paths(output_folder: Optional[str | Path],
                   prediction_json_path: Optional[str | Path],
                   preview_raster_path: Optional[str | Path]) -> Tuple[Path, Path, Path, Path]:
    """Resolve project root, satellite output folder, CNN JSON and georeferenced raster."""
    if output_folder is None:
        project_root = Path(__file__).resolve().parents[1]
        satellite_dir = project_root / "data" / "satellite"
    else:
        folder = Path(output_folder).expanduser().resolve()
        if folder.name.lower() == "satellite":
            satellite_dir = folder
            project_root = folder.parent.parent if folder.parent.name.lower() == "data" else folder.parent
        elif (folder / "data" / "satellite").exists() or not (folder / "B04" / "B04.tif").exists():
            project_root = folder
            satellite_dir = folder / "data" / "satellite"
        else:
            satellite_dir = folder
            project_root = folder.parent.parent if folder.parent.name.lower() == "data" else folder.parent

    raster_path = (Path(preview_raster_path).expanduser().resolve()
                   if preview_raster_path else satellite_dir / "B04" / "B04.tif")
    json_path = (Path(prediction_json_path).expanduser().resolve()
                 if prediction_json_path else project_root / "cnn" / "results" / "satellite_landcover_prediction.json")
    return project_root, satellite_dir, raster_path, json_path


def _broad_reference_majority(worldcover_dataset, geographic_bounds: Tuple[float, float, float, float]) -> Optional[str]:
    """Return majority broad class inside a CNN tile's geographic bounding box."""
    west, south, east, north = geographic_bounds
    if not all(math.isfinite(v) for v in (west, south, east, north)):
        return None
    if east <= west or north <= south:
        return None

    try:
        window = from_bounds(west, south, east, north, transform=worldcover_dataset.transform)
        full_window = Window(0, 0, worldcover_dataset.width, worldcover_dataset.height)
        window = window.intersection(full_window)
        window = window.round_offsets().round_lengths()
    except (WindowError, ValueError, ZeroDivisionError):
        return None

    if window.width < 1 or window.height < 1:
        return None
    try:
        codes = worldcover_dataset.read(1, window=window, masked=False)
    except (RasterioIOError, ValueError, WindowError):
        return None
    if codes.size == 0:
        return None

    counts = {name: 0 for name in CLASS_NAMES}
    for code, count in zip(*np.unique(codes, return_counts=True)):
        broad_class = _WORLDCOVER_CLASS_MAP.get(int(code))
        if broad_class is not None:
            counts[broad_class] += int(count)
    total = sum(counts.values())
    if total == 0:
        return None
    # Deterministic tie-break uses CLASS_NAMES order.
    return max(CLASS_NAMES, key=lambda name: counts[name])


def _row_value(row: dict, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def generate_location_confusion_matrix(
    output_folder: Optional[str | Path] = None,
    latitude: float = -17.5911558,
    longitude: float = 17.3967508,
    prediction_json_path: Optional[str | Path] = None,
    preview_raster_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Generate a 3-class CNN-vs-WorldCover location evaluation.

    Parameters
    ----------
    output_folder:
        Usually ``<project>/data/satellite`` or the LARA project root.
    latitude, longitude:
        Location metadata used to name and annotate the report.
    prediction_json_path:
        Optional override for ``cnn/results/satellite_landcover_prediction.json``.
    preview_raster_path:
        Optional override for the georeferenced source raster. The expected file
        is ``data/satellite/B04/B04.tif`` matching the full RGB preview extent.
    """
    latitude = float(latitude)
    longitude = float(longitude)
    project_root, satellite_dir, raster_path, json_path = _resolve_paths(
        output_folder, prediction_json_path, preview_raster_path
    )

    if not json_path.is_file():
        raise FileNotFoundError(f"CNN prediction JSON was not found: {json_path}")
    if not raster_path.is_file():
        raise FileNotFoundError(
            f"Georeferenced preview raster was not found: {raster_path}. "
            "Expected data/satellite/B04/B04.tif."
        )

    with json_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    records, metadata = _find_records(payload)
    if not records:
        raise ValueError(f"No CNN tile predictions were found in {json_path}")

    try:
        declared_tile_size = metadata.get("tile_size", 64)
        tile_size = int(declared_tile_size or 64)
    except (TypeError, ValueError):
        tile_size = 64
    image_width, image_height = _image_dimensions(metadata, records, tile_size)
    grid_coordinates = _tile_grid_coordinates(records, image_width, image_height, tile_size)

    output_dir = satellite_dir / "Location_Evaluation" / _safe_location_name(latitude, longitude)
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = output_dir / "worldcover_cnn_confusion_matrix.png"
    report_path = output_dir / "worldcover_cnn_evaluation_report.txt"
    json_result_path = output_dir / "worldcover_cnn_evaluation_results.json"

    matrix = np.zeros((len(CLASS_NAMES), len(CLASS_NAMES)), dtype=np.int64)
    reference_counts = {name: 0 for name in CLASS_NAMES}
    prediction_counts = {name: 0 for name in CLASS_NAMES}
    evaluated = 0
    skipped = 0
    skipped_reasons: Dict[str, int] = {}
    tile_names_used = set()

    with rasterio.open(raster_path) as preview:
        if preview.crs is None:
            raise ValueError(f"Preview raster has no CRS: {raster_path}")
        source_crs = preview.crs
        tile_cache: Dict[str, Any] = {}
        with ExitStack() as stack:
            for row in records:
                prediction_value = _row_value(row, "prediction", "class", "label", "predicted_label")
                predicted_class = _normalise_label(prediction_value)
                if not predicted_class:
                    skipped += 1
                    skipped_reasons["unrecognised_cnn_label"] = skipped_reasons.get("unrecognised_cnn_label", 0) + 1
                    continue

                try:
                    x = float(_row_value(row, "x", "col", "column", default=0))
                    y = float(_row_value(row, "y", "row", default=0))
                except (TypeError, ValueError):
                    skipped += 1
                    skipped_reasons["invalid_tile_coordinates"] = skipped_reasons.get("invalid_tile_coordinates", 0) + 1
                    continue

                if grid_coordinates:
                    x *= tile_size
                    y *= tile_size

                # CNN tile coordinates refer to the resized preview image. Scale
                # the tile footprint back to the georeferenced raster dimensions.
                col0 = max(0.0, min(preview.width, x * preview.width / image_width))
                col1 = max(0.0, min(preview.width, (x + tile_size) * preview.width / image_width))
                row0 = max(0.0, min(preview.height, y * preview.height / image_height))
                row1 = max(0.0, min(preview.height, (y + tile_size) * preview.height / image_height))
                if col1 <= col0 or row1 <= row0:
                    skipped += 1
                    skipped_reasons["tile_outside_preview"] = skipped_reasons.get("tile_outside_preview", 0) + 1
                    continue

                source_window = Window(col0, row0, col1 - col0, row1 - row0)
                west_src, south_src, east_src, north_src = rasterio.windows.bounds(source_window, preview.transform)
                try:
                    west, south, east, north = transform_bounds(
                        source_crs, "EPSG:4326", west_src, south_src, east_src, north_src,
                        densify_pts=11,
                    )
                except Exception:
                    skipped += 1
                    skipped_reasons["coordinate_transform_failed"] = skipped_reasons.get("coordinate_transform_failed", 0) + 1
                    continue

                center_lat = (south + north) / 2.0
                center_lon = (west + east) / 2.0
                tile_name = _worldcover_tile_name(center_lat, center_lon)
                tile_names_used.add(tile_name)
                if tile_name not in tile_cache:
                    tile_url = _WORLDCOVER_URL.format(tile=tile_name)
                    try:
                        tile_cache[tile_name] = stack.enter_context(rasterio.open(tile_url))
                    except (RasterioIOError, OSError) as exc:
                        skipped += 1
                        reason = f"worldcover_tile_unavailable_{tile_name}"
                        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
                        continue

                reference_class = _broad_reference_majority(
                    tile_cache[tile_name], (west, south, east, north)
                )
                if reference_class is None:
                    skipped += 1
                    skipped_reasons["no_valid_worldcover_pixels"] = skipped_reasons.get("no_valid_worldcover_pixels", 0) + 1
                    continue

                true_index = CLASS_TO_INDEX[reference_class]
                predicted_index = CLASS_TO_INDEX[predicted_class]
                matrix[true_index, predicted_index] += 1
                reference_counts[reference_class] += 1
                prediction_counts[predicted_class] += 1
                evaluated += 1

    if evaluated == 0:
        raise RuntimeError(
            "No CNN tiles could be compared with ESA WorldCover. Check the prediction JSON, "
            "preview raster, and internet access to the WorldCover COGs."
        )

    correct = int(np.trace(matrix))
    overall_agreement = correct / evaluated
    row_sums = matrix.sum(axis=1)
    col_sums = matrix.sum(axis=0)
    per_class = {}
    for index, name in enumerate(CLASS_NAMES):
        recall = float(matrix[index, index] / row_sums[index]) if row_sums[index] else None
        precision = float(matrix[index, index] / col_sums[index]) if col_sums[index] else None
        per_class[name] = {
            "reference_samples": int(row_sums[index]),
            "cnn_predictions": int(col_sums[index]),
            "recall_or_reference_agreement": recall,
            "precision_or_prediction_agreement": precision,
        }

    # Plot with reference classes as rows and CNN classes as columns.
    fig, ax = plt.subplots(figsize=(8.4, 6.8), constrained_layout=True)
    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    ax.set_title("LARA CNN vs ESA WorldCover 2021\nMajority reference class per CNN tile")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Number of CNN tiles")
    positions = np.arange(len(CLASS_NAMES))
    ax.set_xticks(positions, labels=CLASS_NAMES, rotation=25, ha="right")
    ax.set_yticks(positions, labels=CLASS_NAMES)
    ax.set_xlabel("CNN predicted class")
    ax.set_ylabel("ESA WorldCover reference class")
    threshold = float(matrix.max()) / 2.0 if matrix.size else 0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = int(matrix[i, j])
            ax.text(j, i, str(value), ha="center", va="center",
                    color="white" if value > threshold else "black", fontsize=11)
    fig.savefig(matrix_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    result = {
        "status": "success",
        "latitude": latitude,
        "longitude": longitude,
        "reference_dataset": "ESA WorldCover 2021 v200, 10 m",
        "evaluation_method": "Majority broad WorldCover class among pixels covered by each CNN tile",
        "class_order": CLASS_NAMES,
        "overall_agreement": overall_agreement,
        "correct_tiles": correct,
        "tiles_evaluated": evaluated,
        "tiles_skipped": skipped,
        "skipped_reasons": skipped_reasons,
        "worldcover_tiles_used": sorted(tile_names_used),
        "reference_class_counts": reference_counts,
        "cnn_prediction_counts": prediction_counts,
        "per_class_statistics": per_class,
        "confusion_matrix": matrix.tolist(),
        "matrix_path": str(matrix_path),
        "report_path": str(report_path),
        "json_path": str(json_result_path),
        "preview_raster_path": str(raster_path),
        "prediction_json_path": str(json_path),
        "caveat": (
            "This is agreement with ESA WorldCover 2021 after grouping both datasets into three broad classes. "
            "It is not field-validated accuracy; map dates, class definitions, spatial resolution, and CNN domain shift may differ."
        ),
    }

    with report_path.open("w", encoding="utf-8") as file:
        file.write("LARA CNN vs ESA WORLDCOVER 2021 LOCATION EVALUATION\n")
        file.write("=" * 62 + "\n\n")
        file.write(f"Location: latitude {latitude}, longitude {longitude}\n")
        file.write("Reference: ESA WorldCover 2021 v200, 10 m\n")
        file.write("Method: majority broad WorldCover class over each CNN tile footprint\n")
        file.write("Classes: Water, Vegetation, Other land\n\n")
        file.write(f"CNN tiles evaluated: {evaluated}\n")
        file.write(f"CNN tiles skipped: {skipped}\n")
        file.write(f"Correct agreements: {correct}/{evaluated}\n")
        file.write(f"Overall agreement: {overall_agreement:.2%}\n")
        file.write(f"WorldCover tiles used: {', '.join(sorted(tile_names_used))}\n\n")
        file.write("Confusion matrix (rows = WorldCover reference; columns = CNN prediction)\n")
        file.write("Class order: " + ", ".join(CLASS_NAMES) + "\n")
        file.write(np.array2string(matrix) + "\n\n")
        file.write("Per-class statistics\n")
        for name in CLASS_NAMES:
            stats = per_class[name]
            recall_text = "N/A (no reference samples)" if stats["recall_or_reference_agreement"] is None else f"{stats['recall_or_reference_agreement']:.2%}"
            precision_text = "N/A (no CNN predictions)" if stats["precision_or_prediction_agreement"] is None else f"{stats['precision_or_prediction_agreement']:.2%}"
            file.write(
                f"- {name}: reference samples={stats['reference_samples']}, "
                f"CNN predictions={stats['cnn_predictions']}, "
                f"reference agreement/recall={recall_text}, "
                f"prediction agreement/precision={precision_text}\n"
            )
        if skipped_reasons:
            file.write("\nSkipped tile reasons\n")
            for reason, count in sorted(skipped_reasons.items()):
                file.write(f"- {reason}: {count}\n")
        file.write("\nInterpretation limitation\n")
        file.write(result["caveat"] + "\n")

    with json_result_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    return result
