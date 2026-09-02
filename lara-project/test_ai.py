from modules.ai_advisor import AIAdvisor

analysis = {
    "location": "Windhoek, Namibia",
    "latitude": -22.5609,
    "longitude": 17.0658,
    "area": 5,
    "elevation": 1650,
    "mean_ndvi": 0.16,
    "mean_ndwi": 0.02,
    "water_percent": 0,
    "rainfall": 320,
    "soil": "Sandy Loam",
    "groundwater": "Moderate",
    "flood_risk": "Low"
}

ai = AIAdvisor()

answer = ai.ask(
    analysis,
    "Which crops are suitable and why?"
)

print(answer)
