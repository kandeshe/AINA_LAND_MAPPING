from pathlib import Path

from llama_cpp import Llama

from modules.crop_rules import generate_recommendations
from modules.knowledge_loader import KnowledgeLoader


# =============================================================
# MODEL PATH
# =============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent


MODEL_PATH = (
    BASE_DIR
    / "models"
    / "Phi-3-mini-4k-instruct-q4.gguf"
)


# =============================================================
# AI ADVISOR
# =============================================================

class AIAdvisor:

    def __init__(self):

        print(
            "Loading AI Model..."
        )

        # -----------------------------------------------------
        # Check model
        # -----------------------------------------------------

        if not MODEL_PATH.exists():

            raise FileNotFoundError(

                "\nAI model not found:\n"

                f"{MODEL_PATH}"

                "\n\nExpected location:\n"

                "LARA-project\\models\\"
                "Phi-3-mini-4k-instruct-q4.gguf"

            )

        # -----------------------------------------------------
        # Load model
        # -----------------------------------------------------

        self.llm = Llama(

            model_path=str(
                MODEL_PATH
            ),

            n_ctx=4096,

            n_threads=8,

            verbose=False,

            chat_format="chatml"

        )

        # -----------------------------------------------------
        # Knowledge loader
        # -----------------------------------------------------

        self.knowledge = KnowledgeLoader()

        print(
            "AI Ready!"
        )


    # =========================================================
    # ASK
    # =========================================================

    def ask(
        self,
        analysis,
        question
    ):

        # -----------------------------------------------------
        # Validate analysis
        # -----------------------------------------------------

        if not isinstance(
            analysis,
            dict
        ):

            analysis = {}


        # -----------------------------------------------------
        # Validate question
        # -----------------------------------------------------

        if question is None:

            question = ""


        question = str(
            question
        ).strip()


        q = question.lower()


        # -----------------------------------------------------
        # Generate recommendations
        # -----------------------------------------------------

        try:

            recommendations = (
                generate_recommendations(
                    analysis
                )
            )

        except Exception as e:

            print(
                "Recommendation error:",
                e
            )

            recommendations = {

                "crops": [],

                "vegetables": [],

                "soil_rehabilitation": []

            }


        crops = recommendations.get(
            "crops",
            []
        )


        vegetables = recommendations.get(
            "vegetables",
            []
        )


        soil_rehabilitation = (
            recommendations.get(
                "soil_rehabilitation",
                []
            )
        )


        # =====================================================
        # QUESTION TYPE DETECTION
        # =====================================================

        # -----------------------------------------------------
        # Vegetable rotation MUST be checked before normal
        # vegetable questions.
        # -----------------------------------------------------

        if self._is_vegetable_rotation_question(
            q
        ):

            return self._vegetable_rotation_answer(

                analysis,

                vegetables,

                question

            )


        # -----------------------------------------------------
        # Crop rotation
        # -----------------------------------------------------

        if self._is_rotation_question(
            q
        ):

            return self._crop_rotation_answer(

                analysis,

                crops,

                question

            )


        # -----------------------------------------------------
        # Grazing / land-use question
        # -----------------------------------------------------

        if self._is_grazing_question(
            q
        ):

            return self._grazing_answer(
                analysis,
                question
            )


        # -----------------------------------------------------
        # Barren / land condition question
        # -----------------------------------------------------

        if self._is_barren_question(
            q
        ):

            return self._barren_land_answer(
                analysis,
                question
            )


        # -----------------------------------------------------
        # CNN / satellite land-cover question
        # -----------------------------------------------------

        if self._is_landcover_question(
            q
        ):

            return self._cnn_landcover_answer(
                analysis
            )


        # -----------------------------------------------------
        # Vegetable question
        # -----------------------------------------------------

        vegetable_keywords = [

            "vegetable",

            "vegetables",

            "what vegetable",

            "which vegetable",

            "what vegetables",

            "which vegetables",

            "grow vegetable",

            "grow vegetables"

        ]


        if any(

            keyword in q

            for keyword in vegetable_keywords

        ):

            context = self._build_context(

                analysis,

                crops,

                vegetables,

                soil_rehabilitation

            )

            return self._generate_agricultural_ai_response(

                question,

                context,

                focus="vegetables"

            )


        # -----------------------------------------------------
        # Soil question
        # -----------------------------------------------------

        soil_keywords = [

            "soil",

            "soil health",

            "soil fertility",

            "fertility",

            "rehabilitation",

            "improve soil",

            "improve the soil",

            "soil improvement",

            "improve my soil"

        ]


        if any(

            keyword in q

            for keyword in soil_keywords

        ):

            context = self._build_context(

                analysis,

                crops,

                vegetables,

                soil_rehabilitation

            )

            return self._generate_agricultural_ai_response(

                question,

                context,

                focus="soil"

            )


        # -----------------------------------------------------
        # Normal crop question
        # -----------------------------------------------------

        crop_keywords = [

            "crop",

            "crops",

            "what crop",

            "which crop",

            "what crops",

            "which crops",

            "what should i grow",

            "what can i grow",

            "which crop should i grow"

        ]


        if any(

            keyword in q

            for keyword in crop_keywords

        ):

            context = self._build_context(

                analysis,

                crops,

                vegetables,

                soil_rehabilitation

            )

            return self._generate_agricultural_ai_response(

                question,

                context,

                focus="crops"

            )


        # =====================================================
        # BUILD LAND CONTEXT
        # =====================================================

        context = self._build_context(

            analysis,

            crops,

            vegetables,

            soil_rehabilitation

        )


        # =====================================================
        # GENERAL AI
        # =====================================================

        system_message = """

You are LARA, an Agricultural Intelligence Advisor.

Use the land-analysis information supplied by LARA.

Rules:

1. Use actual supplied land-analysis values.

2. Do not invent measurements.

3. Do not change numerical values.

4. Do not claim a crop is guaranteed to grow.

5. Do not invent crops outside the supplied recommendation
   lists.

6. If the farmer provides previous crops, consider them.

7. If the farmer says a crop cannot be grown or planted
   anymore, do not recommend it.

8. Explain why recommendations were made.

9. Use simple language.

10. Be practical.

11. Clearly distinguish analysis from certainty.

12. Do not claim that one agricultural practice is
    guaranteed to solve a problem.

13. Encourage appropriate soil testing and local
    agricultural validation when necessary.

14. Do not say you are an AI model.

15. Treat CNN land-cover predictions as supporting
    evidence, not as ground-truth measurements.

16. Do not use CNN predictions to override actual
    measured or derived LARA environmental data such
    as soil, rainfall, NDVI, NDWI, groundwater,
    flood risk or land suitability.

17. The CNN does not diagnose plant disease.

18. The CNN does not directly measure soil properties.

19. The CNN does not determine legal land ownership,
    legal grazing status or legal land designation.

20. When CNN and other LARA data differ, clearly explain
    that they represent different types of evidence.

21. Do not combine CNN percentages with NDVI or NDWI
    percentages as if they represent the same measurement.

22. Use CNN land-cover information to provide contextual
    evidence about the observed satellite scene.

"""


        user_message = f"""

LARA LAND ANALYSIS

{context}


FARMER QUESTION

{question}


Answer using the supplied LARA analysis.

Give a clear, practical answer.

"""


        # =====================================================
        # MODEL CALL
        # =====================================================

        try:

            response = (
                self.llm.create_chat_completion(

                    messages=[

                        {
                            "role":
                                "system",

                            "content":
                                system_message

                        },

                        {
                            "role":
                                "user",

                            "content":
                                user_message

                        }

                    ],

                    max_tokens=220,

                    temperature=0.2,

                    stop=[

                        "<|end|>",

                        "<|user|>",

                        "<|assistant|>"

                    ]

                )
            )


            answer = response[
                "choices"
            ][0][
                "message"
            ][
                "content"
            ].strip()


            if answer:

                return answer


        except Exception as e:

            print(
                "AI generation error:",
                e
            )


        # -----------------------------------------------------
        # Fallback
        # -----------------------------------------------------

        return self._fallback_answer(

            analysis,

            question,

            recommendations

        )


    # =========================================================
    # AI AGRICULTURAL RESPONSE
    # =========================================================

    def _generate_agricultural_ai_response(
    self,
    question,
    context,
    focus="crops"
    ):

     if focus == "vegetables":

      focus_instruction = """
        The farmer is asking specifically about vegetables.

        Do NOT simply list all vegetables.

        From the LARA RECOMMENDED VEGETABLES list, identify the
        BEST 1 to 3 options for the farmer's actual conditions.

        Rank them:
        1. Best option
        2. Second option
        3. Third option, only if useful

        For each selected vegetable, explain briefly why it fits
        the actual soil, rainfall, temperature and other available
        conditions.

        Do not recommend vegetables that are not in the LARA
        RECOMMENDED VEGETABLES list.
        """

     elif focus == "soil":

        focus_instruction = """
        The farmer is asking about soil.

        Explain the actual soil measurements in simple language.

        Separate:
        - What the measurements show
        - What that means for farming
        - What the farmer should pay attention to

        Do not invent threshold values or nutrient interpretations
        that are not supported by the supplied LARA data.
        """

     else:

                focus_instruction = """
        The farmer is asking about crops.

        Do NOT simply list all recommended crops.

        From the LARA RECOMMENDED CROPS list, identify the
        BEST 1 to 3 options for the farmer's actual conditions.

        Rank them:
        1. Best option
        2. Second option
        3. Third option, only if useful

        For each selected crop, explain briefly why it fits
        the actual soil, rainfall, temperature and other available
        conditions.

        Do not recommend crops that are not in the LARA
        RECOMMENDED CROPS list.
        """

     system_message = f"""
        You are LARA, a practical agricultural advisor.

        {focus_instruction}

        IMPORTANT:

        1. Use the actual LARA land-analysis data supplied in the context.

        2. Never invent soil, rainfall, temperature, groundwater,
        flood-risk, NDVI, NDWI or CNN values.

        3. Never change a numerical value.

        4. Soil pH must be interpreted correctly.

        5. A pH of 7 is approximately neutral.
        Values below 7 are acidic.
        Values above 7 are alkaline.

        6. Do not call soil alkaline when the supplied pH is acidic.

        7. Do not call soil acidic when the supplied pH is alkaline.

        8. Do not assume that a nutrient is deficient merely because
        a number looks small. Only make a deficiency claim when
        the LARA data or supplied interpretation supports it.

        9. Do not automatically describe organic carbon as high,
        medium or low unless the supplied LARA information
        supports that interpretation.

        10. Do not automatically describe nitrogen as deficient,
            high or low unless the supplied LARA information
            supports that interpretation.

        11. Do not simply repeat the recommendation list.

        12. Prioritize the strongest options.

        13. Explain WHY the selected option fits the available data.

        14. If two options are similarly suitable, say so.

        15. If the available data is insufficient to rank options
            confidently, clearly say that.

        16. Do not guarantee crop success.

        17. Consider soil pH, soil texture, nutrients, rainfall,
            temperature, water availability, flood risk and
            land suitability when those values are available.

        18. CNN land-cover information is supporting image evidence only.

        19. CNN does not directly measure soil properties.

        20. CNN does not diagnose plant disease.

        21. CNN does not determine legal land designation.

        22. Do not combine CNN percentages with NDVI or NDWI percentages.

        23. Do not invent fertilizer rates or chemical doses.

        24. Mention soil testing when it would materially improve
            the recommendation.

        25. Answer naturally, like an agricultural advisor speaking
            directly to a farmer.

        26. Avoid generic phrases such as:
            "These crops are suitable because they are resilient."

        27. Use the actual numbers when they help explain the answer.

        28. Do not mention that you are an AI model.

        29. Keep the response practical and reasonably concise.
        """

     user_message = f"""
        LARA LAND ANALYSIS:

        {context}

        FARMER QUESTION:

        {question}

        Answer the farmer directly.

        IMPORTANT:
        Do not just repeat the available recommendation list.

        Select and prioritize the strongest option(s) based on
        the actual LARA data.

        Explain the reasoning using the actual measurements
        where appropriate.

        If the farmer asks for vegetables, discuss vegetables.

        If the farmer asks for crops, discuss crops.

        If the farmer asks about soil, explain the soil measurements
        rather than giving a generic soil-management paragraph.
        """

     try:

                response = self.llm.create_chat_completion(

                    messages=[

                        {
                            "role": "system",
                            "content": system_message
                        },

                        {
                            "role": "user",
                            "content": user_message
                        }

                    ],

                    max_tokens=500,

                    temperature=0.25,

                    top_p=0.90,

                    repeat_penalty=1.15,

                    stop=[
                        "<|end|>",
                        "<|user|>",
                        "<|assistant|>",
                        "assistant.",
                        "assistant:"
                    ]
                )

                answer = (
                    response["choices"][0]
                    ["message"]
                    ["content"]
                    .strip()
                )

                if answer:
                    return answer

     except Exception as e:

                print(
                    "Agricultural AI response error:",
                    e
                )

            # ---------------------------------------------------------
            # SAFE FALLBACK
            # ---------------------------------------------------------

     if focus == "vegetables":

        return (
                    "<b>Vegetable Recommendation</b><br><br>"
                    "LARA has identified suitable vegetable options "
                    "from the current land analysis, but the detailed "
                    "AI explanation is temporarily unavailable."
                )

     if focus == "soil":

            return (
                    "<b>Soil Assessment</b><br><br>"
                    "LARA has soil-analysis information available, "
                    "but the detailed AI explanation is temporarily "
                    "unavailable."
                )

     return (
                "<b>Crop Recommendation</b><br><br>"
                "LARA has identified suitable crop options from "
                "the current land analysis, but the detailed AI "
                "explanation is temporarily unavailable."
            )

    # =========================================================
    # BUILD CONTEXT
    # =========================================================

    def _build_context(

        self,

        analysis,

        crops,

        vegetables,

        soil_rehabilitation

    ):

        # -----------------------------------------------------
        # Soil
        # -----------------------------------------------------

        soil = analysis.get(
            "soil",
            {}
        )


        if not isinstance(
            soil,
            dict
        ):

            soil = {}


        # -----------------------------------------------------
        # Groundwater
        # -----------------------------------------------------

        groundwater = analysis.get(
            "groundwater",
            {}
        )


        if not isinstance(
            groundwater,
            dict
        ):

            groundwater = {}


        # -----------------------------------------------------
        # CNN
        # -----------------------------------------------------

        cnn = analysis.get(
            "cnn_landcover",
            {}
        )


        if not isinstance(
            cnn,
            dict
        ):

            cnn = {}


        cnn_dominant = cnn.get(
            "dominant_land_cover",
            "Not available"
        )


        cnn_coverage = cnn.get(
            "dominant_coverage_percent",
            "Not available"
        )


        cnn_confidence = cnn.get(
            "average_prediction_confidence",
            "Not available"
        )


        cnn_scores = cnn.get(
            "scene_class_scores",
            []
        )


        if not isinstance(
            cnn_scores,
            list
        ):

            cnn_scores = []


        cnn_score_lines = []


        for item in cnn_scores[:5]:

            if not isinstance(
                item,
                dict
            ):

                continue


            class_name = item.get(
                "class",
                "Unknown"
            )


            score = item.get(
                "score",
                0
            )


            try:

                score_percent = (
                    float(score)
                    * 100
                )

            except (
                TypeError,
                ValueError
            ):

                score_percent = 0


            cnn_score_lines.append(

                f"- {class_name}: "
                f"{score_percent:.2f}%"

            )


        if cnn_score_lines:

            cnn_score_text = (
                "\n".join(
                    cnn_score_lines
                )
            )

        else:

            cnn_score_text = (
                "Not available"
            )


        # -----------------------------------------------------
        # Existing LARA land classification
        # -----------------------------------------------------

        land_cover = analysis.get(
            "land_cover",
            {}
        )


        if not isinstance(
            land_cover,
            dict
        ):

            land_cover = {}


        # -----------------------------------------------------
        # Recommendations
        # -----------------------------------------------------

        crop_text = "\n".join(

            f"- {crop}"

            for crop in crops

        )


        if not crop_text:

            crop_text = "None available"


        vegetable_text = "\n".join(

            f"- {vegetable}"

            for vegetable in vegetables

        )


        if not vegetable_text:

            vegetable_text = "None available"


        rehabilitation_text = "\n".join(

            f"- {item}"

            for item in soil_rehabilitation

        )


        if not rehabilitation_text:

            rehabilitation_text = (
                "None available"
            )


        # =====================================================
        # CONTEXT
        # =====================================================

        return f"""

LOCATION

Location:
{analysis.get("location", "Unknown")}

District:
{analysis.get("district", "Unknown")}

Region:
{analysis.get("region", "Unknown")}

Country:
{analysis.get("country", "Unknown")}


REMOTE SENSING

NDVI:
{analysis.get("mean_ndvi", "Not available")}

NDWI:
{analysis.get("mean_ndwi", "Not available")}

SAVI:
{analysis.get("mean_savi", "Not available")}


LARA LAND-COVER CLASSIFICATION

Water:
{land_cover.get("water", "Not available")}%

Bare land:
{land_cover.get("bare", "Not available")}%

Sparse vegetation:
{land_cover.get("sparse", "Not available")}%

Moderate vegetation:
{land_cover.get("moderate", "Not available")}%

Dense vegetation:
{land_cover.get("dense", "Not available")}%


CNN LAND-COVER ANALYSIS

The CNN provides image-based supporting evidence.

Dominant CNN land-cover:
{cnn_dominant}

Dominant CNN coverage:
{cnn_coverage}%

Average CNN confidence:
{cnn_confidence}

Top CNN scene classes:

{cnn_score_text}


CLIMATE

Rainfall:
{analysis.get("rainfall", "Not available")} mm

Temperature:
{analysis.get("temperature", "Not available")}


GROUNDWATER

Average depth:
{groundwater.get("average_depth", "Not available")}

Recharge potential:
{groundwater.get("recharge_potential", "Not available")}


FLOOD

Flood risk:
{analysis.get("flood_risk", "Not available")}


SOIL

pH:
{soil.get("ph", "Not available")}

Organic Carbon:
{soil.get("organic_carbon", "Not available")}

Nitrogen:
{soil.get("nitrogen", "Not available")}

Clay:
{soil.get("clay", "Not available")}

Sand:
{soil.get("sand", "Not available")}

Silt:
{soil.get("silt", "Not available")}

Bulk Density:
{soil.get("bulk_density", "Not available")}

CEC:
{soil.get("cec", "Not available")}


LAND SUITABILITY

{analysis.get("land_suitability", "Not available")}


LARA RECOMMENDED CROPS

{crop_text}


LARA RECOMMENDED VEGETABLES

{vegetable_text}


SOIL REHABILITATION

{rehabilitation_text}

"""


    # =========================================================
    # LAND-COVER QUESTION DETECTOR
    # =========================================================

    def _is_landcover_question(
        self,
        question
    ):

        keywords = [

            "land cover",

            "landcover",

            "land cover type",

            "what type of land",

            "type of land",

            "satellite classification",

            "satellite image",

            "cnn",

            "what does the image show",

            "what does the satellite show",

            "satellite show",

            "image show"

        ]


        return any(

            word in question

            for word in keywords

        )


    # =========================================================
    # CNN LAND-COVER ANSWER
    # =========================================================

    def _cnn_landcover_answer(
        self,
        analysis
    ):

        cnn = analysis.get(
            "cnn_landcover",
            {}
        )


        if not isinstance(
            cnn,
            dict
        ):

            cnn = {}


        dominant = cnn.get(
            "dominant_land_cover"
        )


        coverage = cnn.get(
            "dominant_coverage_percent"
        )


        confidence = cnn.get(
            "average_prediction_confidence"
        )


        scores = cnn.get(
            "scene_class_scores",
            []
        )


        html = (
            "<b>CNN Land-Cover Analysis</b>"
            "<br><br>"
        )


        if dominant is None:

            return (
                html
                +
                "CNN land-cover information "
                "is not currently available."
            )


        html += (

            f"<b>Dominant CNN land cover:</b> "
            f"{dominant}<br>"

        )


        if coverage is not None:

            try:

                html += (

                    f"<b>Dominant coverage:</b> "
                    f"{float(coverage):.2f}%<br>"

                )

            except (
                TypeError,
                ValueError
            ):

                pass


        if confidence is not None:

            try:

                html += (

                    f"<b>Average CNN confidence:</b> "
                    f"{float(confidence) * 100:.2f}%<br>"

                )

            except (
                TypeError,
                ValueError
            ):

                pass


        html += (
            "<br><b>Top CNN classes:</b><br>"
        )


        shown = 0


        for item in scores:

            if not isinstance(
                item,
                dict
            ):

                continue


            name = item.get(
                "class",
                "Unknown"
            )


            score = item.get(
                "score",
                0
            )


            try:

                percentage = (
                    float(score)
                    * 100
                )

            except (
                TypeError,
                ValueError
            ):

                continue


            html += (
                f"• {name}: "
                f"{percentage:.2f}%<br>"
            )


            shown += 1


            if shown >= 5:

                break


        html += (
            "<br><b>Important:</b><br>"
            "The CNN provides supporting image-based "
            "land-cover evidence. It does not directly "
            "measure soil properties, diagnose plant "
            "disease, or determine legal land designation."
        )


        return html


    # =========================================================
    # GRAZING QUESTION DETECTOR
    # =========================================================

    def _is_grazing_question(
        self,
        question
    ):

        keywords = [

            "grazing",

            "graze",

            "grazing land",

            "pasture",

            "livestock",

            "cattle",

            "animal feed",

            "fodder",

            "forage"

        ]


        return any(

            word in question

            for word in keywords

        )


    # =========================================================
    # GRAZING ANSWER
    # =========================================================

    def _grazing_answer(
        self,
        analysis,
        question
    ):

        cnn = analysis.get(
            "cnn_landcover",
            {}
        )


        if not isinstance(
            cnn,
            dict
        ):

            cnn = {}


        dominant = cnn.get(
            "dominant_land_cover",
            "Not available"
        )


        confidence = cnn.get(
            "average_prediction_confidence",
            None
        )


        land_suitability = analysis.get(
            "land_suitability",
            "Not available"
        )


        flood = analysis.get(
            "flood_risk",
            "Not available"
        )


        html = (
            "<b>Grazing / Pasture Assessment</b>"
            "<br><br>"
        )


        html += (
            f"• CNN dominant land-cover indication: "
            f"{dominant}.<br>"
        )


        if confidence is not None:

            try:

                html += (
                    f"• CNN average confidence: "
                    f"{float(confidence) * 100:.2f}%.<br>"
                )

            except (
                TypeError,
                ValueError
            ):

                pass


        html += (
            f"• LARA land suitability: "
            f"{land_suitability}.<br>"
        )


        html += (
            f"• Flood risk: "
            f"{flood}.<br><br>"
        )


        html += (
            "<b>Interpretation:</b><br>"
            "The CNN can provide supporting evidence "
            "that pasture or other vegetation may be "
            "present, but it cannot by itself establish "
            "that land is suitable or legally designated "
            "for grazing.<br><br>"
        )


        html += (
            "<b>Before grazing:</b><br>"
            "Consider vegetation availability, water "
            "availability, terrain, seasonal conditions, "
            "animal carrying capacity and local "
            "agricultural guidance."
        )


        return html


    # =========================================================
    # BARREN LAND QUESTION DETECTOR
    # =========================================================

    def _is_barren_question(
        self,
        question
    ):

        keywords = [

            "barren",

            "bare land",

            "bare",

            "unused land",

            "uncultivated",

            "nothing grows",

            

        ]


        return any(

            word in question

            for word in keywords

        )


    # =========================================================
    # BARREN LAND ANSWER
    # =========================================================

    def _barren_land_answer(
        self,
        analysis,
        question
    ):

        land_cover = analysis.get(
            "land_cover",
            {}
        )


        if not isinstance(
            land_cover,
            dict
        ):

            land_cover = {}


        cnn = analysis.get(
            "cnn_landcover",
            {}
        )


        if not isinstance(
            cnn,
            dict
        ):

            cnn = {}


        bare = land_cover.get(
            "bare",
            "Not available"
        )


        ndvi = analysis.get(
            "mean_ndvi",
            "Not available"
        )


        suitability = analysis.get(
            "land_suitability",
            "Not available"
        )


        cnn_class = cnn.get(
            "dominant_land_cover",
            "Not available"
        )


        html = (
            "<b>Land Condition Assessment</b>"
            "<br><br>"
        )


        html += (
            f"• LARA bare-land classification: "
            f"{bare}%.<br>"
        )


        html += (
            f"• Mean NDVI: "
            f"{ndvi}.<br>"
        )


        html += (
            f"• Land suitability: "
            f"{suitability}.<br>"
        )


        html += (
            f"• CNN dominant image class: "
            f"{cnn_class}.<br><br>"
        )


        html += (
            "<b>Interpretation:</b><br>"
            "These indicators should be considered together. "
            "A bare or sparsely vegetated classification "
            "does not automatically mean that the land is "
            "permanently barren or unsuitable for agriculture."
            "<br><br>"
        )


        html += (
            "Soil condition, rainfall, water availability, "
            "terrain and land suitability should be checked "
            "before deciding whether the land can be "
            "cultivated."
        )


        return html


    # =========================================================
    # VEGETABLE ROTATION DETECTOR
    # =========================================================

    def _is_vegetable_rotation_question(
        self,
        question
    ):

        vegetable_words = [

            "vegetable rotation",

            "rotate vegetables",

            "rotating vegetables",

            "next vegetable",

            "next vegetables",

            "vegetable next",

            "vegetables next",

            "after tomato",

            "after tomatoes",

            "after spinach",

            "after kale",

            "after carrot",

            "after carrots",

            "after beetroot",

            "after beetroots",

            "after pumpkin",

            "after pumpkins",

            "after watermelon",

            "after squash",

            "after butternut",

            "after green pepper",

            "after green peppers",

            "after eggplant",

            "after eggplants",

            "after beans",

            "after bean"

        ]


        if any(

            word in question

            for word in vegetable_words

        ):

            return True


        vegetables = [

            "tomato",

            "tomatoes",

            "spinach",

            "kale",

            "carrot",

            "carrots",

            "beetroot",

            "beetroots",

            "pumpkin",

            "pumpkins",

            "watermelon",

            "squash",

            "butternut",

            "green pepper",

            "green peppers",

            "eggplant",

            "eggplants",

            "beans",

            "bean"

        ]


        has_vegetable = any(

            vegetable in question

            for vegetable in vegetables

        )


        has_next = (

            "next" in question

            or

            "rotation" in question

            or

            "rotate" in question

            or

            "after" in question

        )


        return (
            has_vegetable
            and
            has_next
        )


    # =========================================================
    # CROP ROTATION DETECTOR
    # =========================================================

    def _is_rotation_question(
        self,
        question
    ):

        rotation_words = [

            "crop rotation",

            "rotation",

            "rotate",

            "rotating",

            "next crop",

            "what should i grow next",

            "what can i grow next",

            "what should i plant next",

            "what can i plant next",

            "after maize",

            "after cowpea",

            "after cowpeas",

            "after sorghum",

            "after millet",

            "after beans",

            "after groundnut",

            "after groundnuts",

            "after bambara",

            "after sunflower",

            "after pearl millet",

            "follow maize",

            "follow cowpea",

            "follow cowpeas",

            "follow sorghum"

        ]


        return any(

            word in question

            for word in rotation_words

        )


    # =========================================================
    # VEGETABLE ROTATION ANSWER
    # =========================================================

    def _vegetable_rotation_answer(

        self,

        analysis,

        vegetables,

        question

    ):

        q = question.lower()


        # =====================================================
        # SOIL
        # =====================================================

        soil = analysis.get(
            "soil",
            {}
        )


        if not isinstance(
            soil,
            dict
        ):

            soil = {}


        ph = soil.get(
            "ph",
            None
        )


        nitrogen = soil.get(
            "nitrogen",
            None
        )


        organic_carbon = soil.get(
            "organic_carbon",
            None
        )


        sand = soil.get(
            "sand",
            None
        )


        clay = soil.get(
            "clay",
            None
        )


        rainfall = analysis.get(
            "rainfall",
            None
        )


        flood = analysis.get(
            "flood_risk",
            "Not available"
        )


        # =====================================================
        # VEGETABLE DICTIONARY
        # =====================================================

        known_vegetables = {

            "tomato":
                "Tomatoes",

            "tomatoes":
                "Tomatoes",

            "spinach":
                "Spinach",

            "kale":
                "Kale",

            "carrot":
                "Carrots",

            "carrots":
                "Carrots",

            "beetroot":
                "Beetroots",

            "beetroots":
                "Beetroots",

            "pumpkin":
                "Pumpkins",

            "pumpkins":
                "Pumpkins",

            "watermelon":
                "Watermelon",

            "squash":
                "Squash",

            "butternut":
                "Butternut",

            "green pepper":
                "Green Pepper",

            "green peppers":
                "Green Pepper",

            "eggplant":
                "Eggplant",

            "eggplants":
                "Eggplant",

            "beans":
                "Beans",

            "bean":
                "Beans"

        }


        # =====================================================
        # PREVIOUS VEGETABLES
        # =====================================================

        previous_vegetables = []


        for keyword, vegetable in (
            known_vegetables.items()
        ):

            if keyword in q:

                if vegetable not in previous_vegetables:

                    previous_vegetables.append(
                        vegetable
                    )


        # =====================================================
        # EXPLICIT EXCLUSIONS
        # =====================================================

        restriction_words = [

            "cannot grow",

            "can't grow",

            "cannot plant",

            "can't plant",

            "cannot use",

            "can't use",

            "no longer grow",

            "no longer plant",

            "not anymore",

            "anymore"

        ]


        has_restriction = any(

            word in q

            for word in restriction_words

        )


        excluded_vegetables = []


        if has_restriction:

            for keyword, vegetable in (
                known_vegetables.items()
            ):

                if keyword in q:

                    if vegetable not in excluded_vegetables:

                        excluded_vegetables.append(
                            vegetable
                        )


        # =====================================================
        # BLOCKED
        # =====================================================

        blocked = []


        for vegetable in previous_vegetables:

            if vegetable not in blocked:

                blocked.append(
                    vegetable
                )


        for vegetable in excluded_vegetables:

            if vegetable not in blocked:

                blocked.append(
                    vegetable
                )


        # =====================================================
        # FILTER LARA VEGETABLE RECOMMENDATIONS
        # =====================================================

        candidates = []


        for vegetable in vegetables:

            name = str(
                vegetable
            ).strip()


            if not name:

                continue


            is_blocked = False


            for blocked_name in blocked:

                current = name.lower()

                blocked_lower = (
                    blocked_name.lower()
                )


                if (

                    current == blocked_lower

                    or

                    blocked_lower in current

                    or

                    current in blocked_lower

                ):

                    is_blocked = True

                    break


            if not is_blocked:

                if name not in candidates:

                    candidates.append(
                        name
                    )


        # =====================================================
        # ROTATION PRIORITY
        # =====================================================

        preferred_order = [

            "Beans",

            "Spinach",

            "Kale",

            "Pumpkins",

            "Squash",

            "Butternut",

            "Carrots",

            "Beetroots",

            "Watermelon",

            "Green Pepper",

            "Eggplant",

            "Tomatoes"

        ]


        recommended = None


        for preferred in preferred_order:

            for candidate in candidates:

                if (
                    candidate.lower()
                    ==
                    preferred.lower()
                ):

                    recommended = candidate

                    break


            if recommended:

                break


        # -----------------------------------------------------
        # Fallback
        # -----------------------------------------------------

        if recommended is None:

            if candidates:

                recommended = candidates[0]


        # =====================================================
        # RESPONSE
        # =====================================================

        html = (

            "<b>Vegetable Crop Rotation Guidance</b>"
            "<br><br>"

        )


        if previous_vegetables:

            html += (

                "<b>Previous vegetable(s):</b> "

                +

                ", ".join(
                    previous_vegetables
                )

                +

                "<br>"

            )

        else:

            html += (

                "<b>Previous vegetable(s):</b> "
                "Not provided<br>"

            )


        if excluded_vegetables:

            html += (

                "<b>Excluded for next cycle:</b> "

                +

                ", ".join(
                    excluded_vegetables
                )

                +

                "<br>"

            )


        html += "<br>"


        if recommended:

            html += (

                "<b>Suggested next vegetable:</b> "

                +

                recommended

                +

                "<br><br>"

            )

        else:

            html += (

                "<b>Suggested next vegetable:</b> "

                "No alternative vegetable was found "
                "in the current LARA recommendation list."

                "<br><br>"

            )


        # =====================================================
        # EXPLANATION
        # =====================================================

        html += (
            "<b>Why:</b><br>"
        )


        if previous_vegetables:

            html += (

                "• LARA identified the previous "
                "vegetable crop(s) from your question: "

                +

                ", ".join(
                    previous_vegetables
                )

                +

                ".<br>"

            )


        if excluded_vegetables:

            html += (

                "• The vegetables that you explicitly "
                "said cannot be grown again have been "
                "excluded.<br>"

            )


        html += (

            "• Vegetable rotation can diversify the "
            "cropping sequence and reduce continuous "
            "cultivation of the same crop.<br>"

        )


        html += (

            "• Alternating crops with different "
            "characteristics can also help as part of "
            "integrated pest and disease management.<br>"

        )


        # =====================================================
        # LAND DATA
        # =====================================================

        if ph is not None:

            html += (

                f"• Soil pH: {ph}. "
                "Soil reaction should be considered "
                "when selecting the next vegetable.<br>"

            )


        if nitrogen is not None:

            html += (

                f"• Soil nitrogen: {nitrogen}. "
                "Nutrient management should be considered "
                "for the next crop.<br>"

            )


        if organic_carbon is not None:

            html += (

                f"• Organic carbon: {organic_carbon}. "
                "Maintaining organic matter is relevant "
                "for long-term soil health.<br>"

            )


        if sand is not None:

            html += (

                f"• Sand content: {sand}. "
                "Water-management and organic-matter "
                "practices should be considered.<br>"

            )


        if clay is not None:

            html += (

                f"• Clay content: {clay}. "
                "Soil texture should be considered "
                "for water management.<br>"

            )


        if rainfall is not None:

            html += (

                f"• Annual rainfall reported by LARA: "
                f"{rainfall} mm.<br>"

            )


        if flood != "Not available":

            html += (

                f"• Flood-risk classification: "
                f"{flood}.<br>"

            )


        # =====================================================
        # DISCLAIMER
        # =====================================================

        html += (

            "<br>"

            "<b>Important:</b><br>"

            "This is a LARA recommendation based on the "
            "available land-analysis data and the crops "
            "mentioned by the farmer. It is not a guarantee "
            "of crop performance. Final selection should "
            "also consider season, field observations, "
            "local agronomic guidance, market requirements "
            "and appropriate soil testing."

        )


        return html


    # =========================================================
    # NORMAL CROP ANSWER
    # =========================================================

    def _crop_answer(
        self,
        crops
    ):

        if not crops:

            return (

                "<b>Recommended Crops</b>"
                "<br><br>"

                "No crop recommendations are currently "
                "available from the LARA analysis."

            )


        return (

            "<b>Recommended Crops</b>"
            "<br><br>"

            +

            "<br>".join(

                f"• {crop}"

                for crop in crops

            )

            +

            "<br><br>"

            "<b>Why:</b><br>"

            "These recommendations are based on the "
            "available LARA land-analysis information."

        )


    # =========================================================
    # NORMAL VEGETABLE ANSWER
    # =========================================================

    def _vegetable_answer(
        self,
        vegetables
    ):

        if not vegetables:

            return (

                "<b>Recommended Vegetables</b>"
                "<br><br>"

                "No vegetable recommendations are "
                "currently available from the LARA analysis."

            )


        return (

            "<b>Recommended Vegetables</b>"
            "<br><br>"

            +

            "<br>".join(

                f"• {vegetable}"

                for vegetable in vegetables

            )

            +

            "<br><br>"

            "<b>Why:</b><br>"

            "The recommendations consider the available "
            "land-analysis information including soil, "
            "rainfall and other environmental indicators."

        )


    # =========================================================
    # SOIL ANSWER
    # =========================================================

    def _soil_answer(
        self,
        soil_rehabilitation
    ):

        if not soil_rehabilitation:

            return (

                "<b>Soil Rehabilitation</b>"
                "<br><br>"

                "No specific soil rehabilitation "
                "recommendations are currently available."

            )


        return (

            "<b>Soil Rehabilitation "
            "Recommendations</b>"

            "<br><br>"

            +

            "<br>".join(

                f"• {item}"

                for item in soil_rehabilitation

            )

            +

            "<br><br>"

            "<b>Note:</b><br>"

            "Soil-management decisions should be "
            "confirmed through appropriate soil testing "
            "and local agricultural guidance."

        )


    # =========================================================
    # CROP ROTATION
    # =========================================================

    def _crop_rotation_answer(

        self,

        analysis,

        crops,

        question

    ):

        q = question.lower()

        # -----------------------------------------------------
        # Soil and field information
        # -----------------------------------------------------

        soil = analysis.get(
            "soil",
            {}
        )

        if not isinstance(
            soil,
            dict
        ):
            soil = {}

        ph = soil.get(
            "ph",
            None
        )

        nitrogen = soil.get(
            "nitrogen",
            None
        )

        sand = soil.get(
            "sand",
            None
        )

        rainfall = analysis.get(
            "rainfall",
            None
        )

        flood = analysis.get(
            "flood_risk",
            "Not available"
        )

        # -----------------------------------------------------
        # Crop dictionary
        # -----------------------------------------------------

        known_crops = {

            "maize":
                "Maize",

            "cowpea":
                "Cowpeas",

            "cowpeas":
                "Cowpeas",

            "sorghum":
                "Sorghum",

            "pearl millet":
                "Pearl Millet (Mahangu)",

            "millet":
                "Pearl Millet (Mahangu)",

            "mahangu":
                "Pearl Millet (Mahangu)",

            "beans":
                "Beans",

            "bean":
                "Beans",

            "groundnut":
                "Groundnut",

            "groundnuts":
                "Groundnut",

            "bambara groundnut":
                "Bambara Groundnuts",

            "bambara groundnuts":
                "Bambara Groundnuts",

            "sunflower":
                "Sunflower",

            "watermelon":
                "Watermelon"

        }

        # -----------------------------------------------------
        # Identify crops mentioned by the farmer
        # -----------------------------------------------------

        previous = []

        for keyword, crop in known_crops.items():

            if keyword in q:

                if crop not in previous:

                    previous.append(
                        crop
                    )

        # -----------------------------------------------------
        # Explicit restrictions
        # -----------------------------------------------------

        restrictions = [

            "cannot grow",

            "can't grow",

            "cannot plant",

            "can't plant",

            "cannot use",

            "can't use",

            "not anymore",

            "anymore",

            "no longer grow",

            "no longer plant"

        ]

        has_restriction = any(
            item in q
            for item in restrictions
        )

        excluded = []

        if has_restriction:

            for keyword, crop in known_crops.items():

                if keyword in q:

                    if crop not in excluded:

                        excluded.append(
                            crop
                        )

        # -----------------------------------------------------
        # Block crops already grown
        # -----------------------------------------------------

        blocked = []

        for crop in previous:

            if crop not in blocked:

                blocked.append(
                    crop
                )

        for crop in excluded:

            if crop not in blocked:

                blocked.append(
                    crop
                )

        # -----------------------------------------------------
        # Keep only crops already recommended by LARA
        # -----------------------------------------------------

        candidates = []

        for crop in crops:

            name = str(
                crop
            ).strip()

            if not name:
                continue

            is_blocked = False

            for blocked_crop in blocked:

                current = name.lower()

                blocked_name = (
                    blocked_crop.lower()
                )

                if (
                    current == blocked_name
                    or
                    blocked_name in current
                    or
                    current in blocked_name
                ):
                    is_blocked = True
                    break

            if not is_blocked:

                if name not in candidates:

                    candidates.append(
                        name
                    )

        # -----------------------------------------------------
        # Rotation preference
        # -----------------------------------------------------

        preferred = [

            "Sunflower",

            "Groundnut",

            "Bambara Groundnuts",

            "Sorghum",

            "Pearl Millet (Mahangu)",

            "Beans",

            "Watermelon"

        ]

        recommendation = None

        for item in preferred:

            for candidate in candidates:

                if (
                    candidate.lower()
                    ==
                    item.lower()
                ):

                    recommendation = candidate
                    break

            if recommendation:
                break

        if recommendation is None and candidates:

            recommendation = candidates[0]

        # -----------------------------------------------------
        # HUMAN-FRIENDLY RESPONSE
        # -----------------------------------------------------

        html = (
            "<b>🌱 Crop Rotation Advice</b><br><br>"
        )

        if previous:

            html += (
                "You previously grew "
                + ", ".join(previous)
                + ". "
            )

            if len(previous) == 1:
                html += (
                    "I would avoid putting the same crop straight "
                    "back into the field if you are planning a rotation."
                )
            else:
                html += (
                    "I would avoid putting those crops straight back "
                    "into the field if you are planning a rotation."
                )

            html += "<br><br>"

        if recommendation:

            html += (
                "<b>My next choice: "
                + recommendation
                + "</b><br><br>"
            )

            html += (
                "Based on the field information available to LARA, "
                + recommendation
                + " looks like a reasonable next crop for this field."
            )

            # Build only useful, meaningful reasons.
            reasons = []

            if ph is not None:

                try:
                    ph_value = float(ph)

                    if 5.5 <= ph_value <= 7.5:
                        reasons.append(
                            f"the soil pH is {ph_value:g}, which is in a generally suitable range"
                        )
                    elif ph_value < 5.5:
                        reasons.append(
                            f"the soil is acidic, with a pH of {ph_value:g}"
                        )
                    else:
                        reasons.append(
                            f"the soil is alkaline, with a pH of {ph_value:g}"
                        )

                except (
                    TypeError,
                    ValueError
                ):
                    pass

            if rainfall is not None:
                try:
                    rainfall_value = float(rainfall)
                    reasons.append(
                        f"annual rainfall is about {rainfall_value:.1f} mm"
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    reasons.append(
                        f"the available rainfall estimate is {rainfall} mm"
                    )

            if flood is not None:

                flood_text = str(
                    flood
                ).strip()

                if flood_text.lower() not in {
                    "",
                    "none",
                    "not available",
                    "unknown"
                }:

                    if flood_text.lower() == "low":
                        reasons.append(
                            "the current flood-risk assessment is low"
                        )
                    else:
                        reasons.append(
                            f"the current flood-risk assessment is {flood_text.lower()}"
                        )

            if reasons:

                html += (
                    "<br><br><b>Why it fits:</b> "
                    + ", ".join(reasons)
                    + "."
                )

            soil_details = []

            if nitrogen is not None:
                soil_details.append(
                    f"nitrogen is {nitrogen}"
                )

            if sand is not None:
                try:
                    sand_value = float(sand)
                    soil_details.append(
                        f"sand content is {sand_value:.1f}%"
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    soil_details.append(
                        f"sand content is {sand}%"
                    )

            if soil_details:
                html += (
                    "<br><br>The soil analysis also shows "
                    + " and ".join(soil_details)
                    + "."
                )

            if previous:
                html += (
                    "<br><br>So, rather than immediately repeating "
                    + ", ".join(previous)
                    + ", "
                    + recommendation
                    + " gives you a different crop in the rotation while still fitting the current LARA assessment."
                )

        else:

            html += (
                "I couldn't find a suitable next crop among the crops "
                "currently recommended by LARA for this field. "
                "I would not force a rotation choice without a stronger "
                "match to the field conditions."
            )

        html += (
            "<br><br><b>Keep in mind:</b> This is a LARA-based recommendation "
            "using the available field data and your cropping history. "
            "Before planting, it is still worth considering the local field "
            "condition, variety, irrigation and soil-test results."
        )

        return html


    # =========================================================
    # FALLBACK
    # =========================================================

    def _fallback_answer(

        self,

        analysis,

        question,

        recommendations

    ):

        q = question.lower()


        crops = recommendations.get(
            "crops",
            []
        )


        vegetables = recommendations.get(
            "vegetables",
            []
        )


        soil = recommendations.get(
            "soil_rehabilitation",
            []
        )


        # -----------------------------------------------------
        # Vegetable rotation
        # -----------------------------------------------------

        if self._is_vegetable_rotation_question(
            q
        ):

            return self._vegetable_rotation_answer(

                analysis,

                vegetables,

                question

            )


        # -----------------------------------------------------
        # Crop rotation
        # -----------------------------------------------------

        if self._is_rotation_question(
            q
        ):

            return self._crop_rotation_answer(

                analysis,

                crops,

                question

            )


        # -----------------------------------------------------
        # Grazing
        # -----------------------------------------------------

        if self._is_grazing_question(
            q
        ):

            return self._grazing_answer(
                analysis,
                question
            )


        # -----------------------------------------------------
        # Barren
        # -----------------------------------------------------

        if self._is_barren_question(
            q
        ):

            return self._barren_land_answer(
                analysis,
                question
            )


        # -----------------------------------------------------
        # CNN
        # -----------------------------------------------------

        if self._is_landcover_question(
            q
        ):

            return self._cnn_landcover_answer(
                analysis
            )


        # -----------------------------------------------------
        # Vegetables
        # -----------------------------------------------------

        if (

            "vegetable" in q

            or

            "vegetables" in q

        ):

            return self._vegetable_answer(
                vegetables
            )


        # -----------------------------------------------------
        # Soil
        # -----------------------------------------------------

        if (

            "soil" in q

            or

            "rehabilitation" in q

            or

            "fertility" in q

        ):

            return self._soil_answer(
                soil
            )


        # -----------------------------------------------------
        # Crops
        # -----------------------------------------------------

        return self._crop_answer(
            crops
        )