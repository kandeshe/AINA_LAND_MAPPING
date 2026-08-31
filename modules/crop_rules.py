# =============================================================
# LARA - CROP AND VEGETABLE RECOMMENDATION RULES
# =============================================================

def _safe_number(value, default=0.0):

    try:

        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):

        return default


def _get_soil(analysis):

    soil = analysis.get(
        "soil",
        {}
    )

    if not isinstance(
        soil,
        dict
    ):

        soil = {}

    return soil


# =============================================================
# MAIN RECOMMENDATION FUNCTION
# =============================================================

def generate_recommendations(analysis):

    if not isinstance(
        analysis,
        dict
    ):

        analysis = {}


    # =========================================================
    # LAND DATA
    # =========================================================

    rainfall = _safe_number(
        analysis.get(
            "rainfall",
            0
        )
    )


    temperature = _safe_number(
        analysis.get(
            "temperature",
            25
        )
    )


    ndvi = _safe_number(
        analysis.get(
            "mean_ndvi",
            0
        )
    )


    flood_risk = str(
        analysis.get(
            "flood_risk",
            "Low"
        )
        or "Low"
    ).lower()


    # =========================================================
    # SOIL DATA
    # =========================================================

    soil = _get_soil(
        analysis
    )


    ph = _safe_number(
        soil.get(
            "ph",
            7
        ),
        7
    )


    organic_carbon = _safe_number(
        soil.get(
            "organic_carbon",
            0
        )
    )


    nitrogen = _safe_number(
        soil.get(
            "nitrogen",
            0
        )
    )


    clay = _safe_number(
        soil.get(
            "clay",
            0
        )
    )


    sand = _safe_number(
        soil.get(
            "sand",
            0
        )
    )


    silt = _safe_number(
        soil.get(
            "silt",
            0
        )
    )


    # =========================================================
    # RESULT LISTS
    # =========================================================

    crops = []

    vegetables = []

    soil_rehabilitation = []


    # =========================================================
    # CROP RECOMMENDATIONS
    #
    # These are broad screening rules for the university
    # project. They are NOT intended as field-level guarantees.
    # =========================================================


    # ---------------------------------------------------------
    # LOW RAINFALL
    # ---------------------------------------------------------

    if rainfall < 300:

        crops.extend([

            "Pearl Millet (Mahangu)",

            "Sorghum",

            "Cowpeas",

            "Bambara Groundnuts"

        ])


    # ---------------------------------------------------------
    # MODERATE RAINFALL
    # ---------------------------------------------------------

    elif rainfall < 600:

        crops.extend([

            "Pearl Millet (Mahangu)",

            "Maize",

            "Groundnut",

            "Cowpeas",

            "Bambara Groundnuts",

            "Sorghum"

        ])


    # ---------------------------------------------------------
    # HIGH RAINFALL
    # ---------------------------------------------------------

    else:

        crops.extend([

            "Maize",

            "Cowpeas",

            "Bambara Groundnuts",

            "Sorghum",

            "Groundnut"

        ])


    # =========================================================
    # SOIL-BASED CROP ADDITIONS
    # =========================================================


    # Sandy soils
    if sand >= 40:

        crops.append(
            "Watermelon"
        )


    # More balanced / loamy soil
    if (

        sand < 60

        and

        clay < 45

    ):

        crops.append(
            "Groundnut"
        )


    # Lower pH
    if ph < 6.0:

        crops.append(
            "Bambara Groundnuts"
        )

        crops.append(
            "Cowpeas"
        )


    # =========================================================
    # FLOOD RISK
    # =========================================================

    if (
        "high" in flood_risk
        or
        "very high" in flood_risk
    ):

        # Remove crops that we don't want to present as
        # the first choice under high flood risk.

        crops = [
            crop
            for crop in crops
            if crop not in [
                "Groundnut",
                "Bambara Groundnuts"
            ]
        ]


        crops.extend([

            "Sorghum",

            "Pearl Millet (Mahangu)"

        ])


    # =========================================================
    # VEGETABLE RECOMMENDATIONS
    #
    # Namibia vegetables requested for the project:
    #
    # Pumpkin
    # Watermelon
    # Spinach
    # Kale
    # Carrots
    # Beetroots
    # Squash
    # Butternut
    # Tomatoes
    # Green Pepper
    # Eggplant
    # =========================================================


    # ---------------------------------------------------------
    # GENERAL VEGETABLE BASE
    # ---------------------------------------------------------

    vegetables.extend([

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

        "Beans"

    ])


    # =========================================================
    # RAINFALL FILTERING
    # =========================================================

    # Very dry conditions
    if rainfall < 300:

        # Keep vegetables that can be considered with
        # appropriate irrigation / water management.

        vegetables = [

            "Pumpkins",

            "Watermelon",

            "Spinach",

            "Kale",

            "Carrots",

            "Beetroots",

            "Squash",

            "Butternut",

            "Beans"

        ]


    # Moderate rainfall
    elif rainfall < 600:

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

            "Beans"

        ]


    # Higher rainfall
    else:

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

            "Beans"

        ]


    # =========================================================
    # SOIL pH CONSIDERATION
    # =========================================================

    if ph < 5.5:

        soil_rehabilitation.append(
            "Soil is strongly acidic; consider soil testing and appropriate pH management."
        )


    elif ph < 6.5:

        soil_rehabilitation.append(
            "Soil is moderately acidic; monitor soil pH and consider appropriate soil-management practices."
        )


    elif ph <= 7.5:

        soil_rehabilitation.append(
            "Soil pH is in a broadly neutral range."
        )


    elif ph <= 8.5:

        soil_rehabilitation.append(
            "Soil is slightly alkaline; monitor pH and crop suitability."
        )


    else:

        soil_rehabilitation.append(
            "Soil is strongly alkaline; soil testing and appropriate management are recommended."
        )


    # =========================================================
    # ORGANIC CARBON
    # =========================================================

    if organic_carbon < 10:

        soil_rehabilitation.append(
            "Consider increasing organic matter through suitable organic amendments and residue management."
        )

    else:

        soil_rehabilitation.append(
            "Maintain organic matter through residue management and suitable soil-cover practices."
        )


    # =========================================================
    # NITROGEN
    # =========================================================

    if nitrogen < 1:

        soil_rehabilitation.append(
            "Nitrogen management should be considered; confirm nutrient requirements through soil testing."
        )

    else:

        soil_rehabilitation.append(
            "Continue monitoring soil nitrogen and maintain balanced nutrient management."
        )


    # =========================================================
    # SAND
    # =========================================================

    if sand >= 40:

        soil_rehabilitation.append(
            "Higher sand content may increase drainage; maintain organic matter and manage water carefully."
        )


    # =========================================================
    # CLAY
    # =========================================================

    if clay >= 40:

        soil_rehabilitation.append(
            "Higher clay content may affect drainage and soil workability; monitor water management."
        )


    # =========================================================
    # CROP ROTATION
    # =========================================================

    soil_rehabilitation.append(
        "Use crop rotation to diversify the cropping sequence and avoid continuous cultivation of the same crop."
    )


    # =========================================================
    # GROUND COVER
    # =========================================================

    soil_rehabilitation.append(
        "Maintain suitable soil cover and reduce unnecessary soil exposure where practical."
    )


    # =========================================================
    # REMOVE DUPLICATES
    # =========================================================

    crops = list(
        dict.fromkeys(
            crops
        )
    )


    vegetables = list(
        dict.fromkeys(
            vegetables
        )
    )


    soil_rehabilitation = list(
        dict.fromkeys(
            soil_rehabilitation
        )
    )


    # =========================================================
    # RETURN
    # =========================================================

    return {

        "crops":
            crops,

        "vegetables":
            vegetables,

        "soil_rehabilitation":
            soil_rehabilitation

    }