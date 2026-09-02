# =============================================================
# LARA - CROP AND VEGETABLE RECOMMENDATION RULES
# =============================================================
#
# Purpose:
#   Convert LARA environmental measurements into ranked
#   agricultural screening recommendations.
#
# IMPORTANT:
#   These are screening recommendations, not field-level
#   agronomic guarantees. Final decisions should consider
#   local conditions, season, irrigation, field observations
#   and appropriate soil testing.
#
# Output structure is kept compatible with AI Advisor:
#
# {
#     "crops": [...],
#     "vegetables": [...],
#     "soil_rehabilitation": [...]
# }
# =============================================================


def _safe_number(value, default=0.0):
    """
    Safely convert a value to float.
    """
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _get_soil(analysis):
    """
    Safely obtain soil dictionary.
    """
    soil = analysis.get("soil", {})

    if not isinstance(soil, dict):
        soil = {}

    return soil


def _add_score(scores, reasons, crop, points, reason):
    """
    Add suitability points and a human-readable reason.
    """
    if crop not in scores:
        scores[crop] = 0.0

    if crop not in reasons:
        reasons[crop] = []

    scores[crop] += points

    if reason and reason not in reasons[crop]:
        reasons[crop].append(reason)


def _rank_items(scores):
    """
    Return items sorted by score from highest to lowest.
    """
    return [
        item
        for item, score in sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
    ]


def _crop_reason_summary(reasons, crop):
    """
    Return a short reason string.
    """
    crop_reasons = reasons.get(crop, [])

    if not crop_reasons:
        return "Selected from the available environmental screening."

    return "; ".join(crop_reasons[:3])


# =============================================================
# MAIN RECOMMENDATION FUNCTION
# =============================================================

def generate_recommendations(analysis, previous_crops=None):

    if not isinstance(analysis, dict):
        analysis = {}

    if previous_crops is None:
        previous_crops = []

    if not isinstance(previous_crops, list):
        previous_crops = [previous_crops]

    previous_crops = [
        str(crop).strip().lower()
        for crop in previous_crops
        if str(crop).strip()
    ]

    # =========================================================
    # LAND / CLIMATE DATA
    # =========================================================

    rainfall = _safe_number(
        analysis.get("rainfall", 0)
    )

    temperature = _safe_number(
        analysis.get("temperature", 25)
    )

    ndvi = _safe_number(
        analysis.get("mean_ndvi", 0)
    )

    flood_risk = str(
        analysis.get("flood_risk", "Low")
        or "Low"
    ).lower()

    land_suitability = str(
        analysis.get("land_suitability", "")
        or ""
    ).lower()

    # =========================================================
    # SOIL DATA
    # =========================================================

    soil = _get_soil(analysis)

    ph = _safe_number(
        soil.get("ph", 7),
        7
    )

    organic_carbon = _safe_number(
        soil.get("organic_carbon", 0)
    )

    nitrogen = _safe_number(
        soil.get("nitrogen", 0)
    )

    phosphorus = _safe_number(
        soil.get("phosphorus", 0)
    )

    potassium = _safe_number(
        soil.get("potassium", 0)
    )

    clay = _safe_number(
        soil.get("clay", 0)
    )

    sand = _safe_number(
        soil.get("sand", 0)
    )

    silt = _safe_number(
        soil.get("silt", 0)
    )

    # =========================================================
    # RESULT CONTAINERS
    # =========================================================

    crop_scores = {}
    crop_reasons = {}

    vegetable_scores = {}
    vegetable_reasons = {}

    soil_rehabilitation = []

    # =========================================================
    # CROP PROFILES
    #
    # These are broad screening profiles.
    # They should NOT be interpreted as exact agronomic limits.
    # =========================================================

    crops = [
        "Maize",
        "Sorghum",
        "Pearl Millet (Mahangu)",
        "Cowpeas",
        "Groundnut",
        "Bambara Groundnuts",
    ]

    # =========================================================
    # RAINFALL SCORING
    # =========================================================

    # Maize
    if 500 <= rainfall <= 1500:
        _add_score(
            crop_scores,
            crop_reasons,
            "Maize",
            25,
            "Rainfall is within a generally favorable range for maize."
        )
    elif 300 <= rainfall < 500 or 1500 < rainfall <= 2000:
        _add_score(
            crop_scores,
            crop_reasons,
            "Maize",
            12,
            "Rainfall may support maize with suitable water management."
        )
    else:
        _add_score(
            crop_scores,
            crop_reasons,
            "Maize",
            3,
            "Rainfall is outside the preferred screening range for maize."
        )

    # Sorghum
    if 300 <= rainfall <= 1000:
        _add_score(
            crop_scores,
            crop_reasons,
            "Sorghum",
            25,
            "Sorghum is well suited to relatively dry conditions."
        )
    elif 1000 < rainfall <= 1500:
        _add_score(
            crop_scores,
            crop_reasons,
            "Sorghum",
            12,
            "Rainfall can support sorghum with appropriate management."
        )
    else:
        _add_score(
            crop_scores,
            crop_reasons,
            "Sorghum",
            5,
            "Rainfall is less favorable for sorghum under this screening."
        )

    # Pearl Millet
    if rainfall <= 700:
        _add_score(
            crop_scores,
            crop_reasons,
            "Pearl Millet (Mahangu)",
            28,
            "Pearl millet is a strong option under relatively dry rainfall conditions."
        )
    elif rainfall <= 1000:
        _add_score(
            crop_scores,
            crop_reasons,
            "Pearl Millet (Mahangu)",
            15,
            "Pearl millet can tolerate relatively dry conditions."
        )
    else:
        _add_score(
            crop_scores,
            crop_reasons,
            "Pearl Millet (Mahangu)",
            3,
            "High rainfall is less favorable for pearl millet."
        )

    # Cowpeas
    if 400 <= rainfall <= 1200:
        _add_score(
            crop_scores,
            crop_reasons,
            "Cowpeas",
            25,
            "Rainfall is broadly favorable for cowpeas."
        )
    elif 250 <= rainfall < 400:
        _add_score(
            crop_scores,
            crop_reasons,
            "Cowpeas",
            12,
            "Cowpeas can be considered under lower rainfall with suitable water management."
        )
    else:
        _add_score(
            crop_scores,
            crop_reasons,
            "Cowpeas",
            5,
            "Rainfall is less favorable for cowpeas under this screening."
        )

    # Groundnut
    if 500 <= rainfall <= 1200:
        _add_score(
            crop_scores,
            crop_reasons,
            "Groundnut",
            25,
            "Rainfall is broadly favorable for groundnut."
        )
    elif 300 <= rainfall < 500:
        _add_score(
            crop_scores,
            crop_reasons,
            "Groundnut",
            12,
            "Groundnut may be considered with appropriate water management."
        )
    else:
        _add_score(
            crop_scores,
            crop_reasons,
            "Groundnut",
            5,
            "Rainfall is outside the preferred screening range for groundnut."
        )

    # Bambara Groundnut
    if 400 <= rainfall <= 1200:
        _add_score(
            crop_scores,
            crop_reasons,
            "Bambara Groundnuts",
            25,
            "Rainfall is broadly favorable for Bambara groundnuts."
        )
    elif rainfall < 400:
        _add_score(
            crop_scores,
            crop_reasons,
            "Bambara Groundnuts",
            15,
            "Bambara groundnuts can be considered under relatively dry conditions."
        )
    else:
        _add_score(
            crop_scores,
            crop_reasons,
            "Bambara Groundnuts",
            8,
            "High rainfall requires careful water management."
        )

    # =========================================================
    # TEMPERATURE
    # =========================================================

    if 20 <= temperature <= 30:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                8,
                "Temperature is broadly favorable for crop production."
            )

    elif temperature < 15 or temperature > 35:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                -5,
                "Temperature may limit crop performance."
            )

    else:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                3,
                "Temperature is within a moderate agricultural range."
            )

    # =========================================================
    # SOIL pH
    # =========================================================

    # Broad screening only.
    if 5.5 <= ph <= 7.5:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                10,
                "Soil pH is within a broadly favorable range."
            )

    elif 5.0 <= ph < 5.5:

        # Acid-tolerant crops receive a relative advantage.
        for crop in [
            "Sorghum",
            "Cowpeas",
            "Groundnut",
            "Bambara Groundnuts"
        ]:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                8,
                "The crop can be considered under moderately acidic soil conditions."
            )

        for crop in [
            "Maize",
            "Pearl Millet (Mahangu)"
        ]:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                2,
                "Acidic soil may require attention before cultivation."
            )

    elif ph < 5.0:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                -5,
                "Strong soil acidity may restrict crop performance."
            )

    elif 7.5 < ph <= 8.5:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                3,
                "Slightly alkaline soil should be considered when selecting crops."
            )

    else:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                -5,
                "Strong alkalinity may restrict nutrient availability."
            )

    # =========================================================
    # SOIL TEXTURE
    # =========================================================

    if sand >= 40:

        for crop in [
            "Groundnut",
            "Bambara Groundnuts",
            "Sorghum",
            "Pearl Millet (Mahangu)"
        ]:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                8,
                "Higher sand content can provide favorable drainage for this crop."
            )

    if clay >= 40:

        for crop in [
            "Maize",
            "Sorghum",
            "Cowpeas"
        ]:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                5,
                "Higher clay content can provide greater water-holding capacity."
            )

    if silt >= 30:

        for crop in [
            "Maize",
            "Cowpeas",
            "Groundnut"
        ]:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                3,
                "The soil contains a meaningful silt fraction."
            )

    # =========================================================
    # ORGANIC CARBON
    # =========================================================

    # The actual meaning depends on the units used by the LARA
    # SoilGrids processing. We therefore use this only as a
    # relative screening signal.
    if organic_carbon > 0:

        if organic_carbon < 10:

            for crop in crops:
                _add_score(
                    crop_scores,
                    crop_reasons,
                    crop,
                    -2,
                    "Organic carbon is relatively low in the available analysis."
                )

        else:

            for crop in crops:
                _add_score(
                    crop_scores,
                    crop_reasons,
                    crop,
                    3,
                    "Organic carbon provides a positive soil-condition signal."
                )

    # =========================================================
    # NITROGEN
    # =========================================================

    if nitrogen > 0:

        if nitrogen < 1:

            for crop in crops:
                _add_score(
                    crop_scores,
                    crop_reasons,
                    crop,
                    -2,
                    "Available nitrogen is relatively low in the analysis."
                )

        else:

            for crop in crops:
                _add_score(
                    crop_scores,
                    crop_reasons,
                    crop,
                    2,
                    "Available nitrogen provides a positive nutrient signal."
                )

    # =========================================================
    # PHOSPHORUS / POTASSIUM
    # =========================================================

    if phosphorus > 0:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                1,
                "Phosphorus information is available for the analysis."
            )

    if potassium > 0:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                1,
                "Potassium information is available for the analysis."
            )

    # =========================================================
    # NDVI
    # =========================================================

    if ndvi > 0:

        if ndvi < 0.2:

            for crop in crops:
                _add_score(
                    crop_scores,
                    crop_reasons,
                    crop,
                    -2,
                    "Current vegetation signal is low."
                )

        elif ndvi >= 0.5:

            for crop in crops:
                _add_score(
                    crop_scores,
                    crop_reasons,
                    crop,
                    3,
                    "The current vegetation signal is relatively strong."
                )

    # =========================================================
    # FLOOD RISK
    # =========================================================

    if "very high" in flood_risk:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                -15,
                "Very high flood risk is a major limitation."
            )

    elif "high" in flood_risk:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                -8,
                "High flood risk should be considered before cultivation."
            )

    elif "medium" in flood_risk or "moderate" in flood_risk:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                -3,
                "Moderate flood risk should be considered."
            )

    else:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                2,
                "Flood-risk conditions are not a major limitation in the available analysis."
            )

    # =========================================================
    # LAND SUITABILITY
    # =========================================================

    if "high" in land_suitability or "good" in land_suitability:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                5,
                "LARA land-suitability information is favorable."
            )

    elif "poor" in land_suitability or "low" in land_suitability:

        for crop in crops:
            _add_score(
                crop_scores,
                crop_reasons,
                crop,
                -5,
                "LARA land-suitability information indicates a limitation."
            )

    # =========================================================
    # VEGETABLE SCORING
    # =========================================================

    vegetables = [
        "Pumpkins",
        "Watermelon",
        "Spinach",
        "Kale",
        "Carrots",
        "Beetroots",
        "Squash",
        "Butternut",
        "Tomatoes",
        "Green Pepper",
        "Eggplant",
        "Beans",
    ]

    # ---------------------------------------------------------
    # Rainfall / water-demand screening
    # ---------------------------------------------------------

    for vegetable in vegetables:

        # General baseline
        _add_score(
            vegetable_scores,
            vegetable_reasons,
            vegetable,
            5,
            "Included in the LARA vegetable screening set."
        )

    if rainfall >= 600:

        for vegetable in [
            "Pumpkins",
            "Watermelon",
            "Squash",
            "Butternut",
            "Tomatoes",
            "Green Pepper",
            "Eggplant",
            "Beans"
        ]:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                8,
                "Rainfall provides a favorable water-availability signal."
            )

    elif rainfall >= 300:

        for vegetable in [
            "Spinach",
            "Kale",
            "Carrots",
            "Beetroots",
            "Tomatoes",
            "Green Pepper",
            "Eggplant"
        ]:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                5,
                "Rainfall can support the crop with suitable water management."
            )

        for vegetable in [
            "Pumpkins",
            "Watermelon",
            "Squash",
            "Butternut"
        ]:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                3,
                "The crop may require additional water management."
            )

    else:

        for vegetable in vegetables:

            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -3,
                "Low rainfall means irrigation or reliable water management may be required."
            )

    # ---------------------------------------------------------
    # pH
    # ---------------------------------------------------------

    if 5.5 <= ph <= 7.5:

        for vegetable in vegetables:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                8,
                "Soil pH is broadly favorable for vegetable production."
            )

    elif 5.0 <= ph < 5.5:

        for vegetable in [
            "Pumpkins",
            "Squash",
            "Butternut",
            "Carrots",
            "Beans"
        ]:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                4,
                "This vegetable can be considered under moderately acidic conditions."
            )

        for vegetable in vegetables:

            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -2,
                "Soil acidity should be considered before vegetable production."
            )

    elif ph < 5.0:

        for vegetable in vegetables:

            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -6,
                "Strong acidity may limit vegetable performance."
            )

    elif ph > 7.5:

        for vegetable in vegetables:

            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -2,
                "Alkaline conditions should be considered when selecting vegetables."
            )

    # ---------------------------------------------------------
    # Soil texture
    # ---------------------------------------------------------

    if sand >= 40:

        for vegetable in [
            "Carrots",
            "Beetroots",
            "Watermelon",
            "Pumpkins",
            "Squash",
            "Butternut"
        ]:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                5,
                "Higher sand content can provide useful drainage for this crop."
            )

    if clay >= 40:

        for vegetable in [
            "Spinach",
            "Kale",
            "Beans"
        ]:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                3,
                "Higher clay content can improve water-holding capacity."
            )

    # ---------------------------------------------------------
    # Organic carbon
    # ---------------------------------------------------------

    if organic_carbon > 0 and organic_carbon < 10:

        for vegetable in vegetables:

            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -2,
                "Low organic carbon indicates a need for soil-improvement practices."
            )

    # ---------------------------------------------------------
    # Nitrogen
    # ---------------------------------------------------------

    if nitrogen > 0 and nitrogen < 1:

        for vegetable in [
            "Spinach",
            "Kale",
            "Tomatoes",
            "Green Pepper"
        ]:
            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -2,
                "Low nitrogen may limit leafy and fruiting vegetable performance."
            )

    # ---------------------------------------------------------
    # Flood risk
    # ---------------------------------------------------------

    if "very high" in flood_risk:

        for vegetable in vegetables:

            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -12,
                "Very high flood risk is a major limitation."
            )

    elif "high" in flood_risk:

        for vegetable in vegetables:

            _add_score(
                vegetable_scores,
                vegetable_reasons,
                vegetable,
                -7,
                "High flood risk should be considered before planting."
            )

    # =========================================================
    # SOIL REHABILITATION
    # =========================================================

    # pH
    if ph < 5.5:

        soil_rehabilitation.append(
            "Soil is acidic. Consider soil testing and appropriate pH management before applying amendments."
        )

    elif ph < 6.5:

        soil_rehabilitation.append(
            "Soil is moderately acidic. Monitor pH and use crop selection and appropriate soil-management practices."
        )

    elif ph <= 7.5:

        soil_rehabilitation.append(
            "Soil pH is in a broadly neutral range."
        )

    elif ph <= 8.5:

        soil_rehabilitation.append(
            "Soil is slightly alkaline. Monitor pH and nutrient availability when selecting crops."
        )

    else:

        soil_rehabilitation.append(
            "Soil is strongly alkaline. Soil testing and appropriate management are recommended."
        )

    # Organic carbon
    if organic_carbon > 0:

        if organic_carbon < 10:

            soil_rehabilitation.append(
                "Organic carbon is relatively low in the available analysis; consider suitable organic-matter and residue-management practices."
            )

        else:

            soil_rehabilitation.append(
                "Maintain organic matter through residue management, suitable soil cover and appropriate organic inputs."
            )

    # Nitrogen
    if nitrogen > 0:

        if nitrogen < 1:

            soil_rehabilitation.append(
                "Nitrogen appears relatively low in the available analysis; confirm nutrient requirements through soil testing."
            )

        else:

            soil_rehabilitation.append(
                "Continue monitoring nitrogen and maintain balanced nutrient management."
            )

    # Sand
    if sand >= 40:

        soil_rehabilitation.append(
            "Higher sand content may increase drainage; maintain organic matter and manage water carefully."
        )

    # Clay
    if clay >= 40:

        soil_rehabilitation.append(
            "Higher clay content may affect drainage and workability; monitor water management."
        )

    # General
    soil_rehabilitation.append(
        "Use crop rotation to diversify the cropping sequence and avoid continuous cultivation of the same crop."
    )

    soil_rehabilitation.append(
        "Maintain suitable ground cover and reduce unnecessary soil exposure where practical."
    )

    # =========================================================
    # RANK RESULTS
    # =========================================================

    ranked_crops = _rank_items(crop_scores)

    ranked_vegetables = _rank_items(vegetable_scores)

    # =========================================================
    # CROP ROTATION
    # =========================================================

    if previous_crops:

        excluded_crops = set()

        for previous_crop in previous_crops:
            if "maize" in previous_crop:
                excluded_crops.add("Maize")
            if "cowpea" in previous_crop:
                excluded_crops.add("Cowpeas")
            if "sorghum" in previous_crop:
                excluded_crops.add("Sorghum")
            if "pearl millet" in previous_crop or "millet" in previous_crop or "mahangu" in previous_crop:
                excluded_crops.add("Pearl Millet (Mahangu)")
            if "groundnut" in previous_crop:
                excluded_crops.add("Groundnut")
            if "bambara" in previous_crop:
                excluded_crops.add("Bambara Groundnuts")

        ranked_crops = [
            crop for crop in ranked_crops
            if crop not in excluded_crops
        ]

    # Keep useful number of recommendations.
    # The AI Advisor can later explain the ranking.
    ranked_crops = ranked_crops[:6]

    ranked_vegetables = ranked_vegetables[:8]

    # =========================================================
    # REMOVE DUPLICATES
    # =========================================================

    ranked_crops = list(
        dict.fromkeys(ranked_crops)
    )

    ranked_vegetables = list(
        dict.fromkeys(ranked_vegetables)
    )

    soil_rehabilitation = list(
        dict.fromkeys(soil_rehabilitation)
    )

    # =========================================================
    # RETURN
    # =========================================================

    return {

        "crops": ranked_crops,

        "vegetables": ranked_vegetables,

        "soil_rehabilitation": soil_rehabilitation,

    }