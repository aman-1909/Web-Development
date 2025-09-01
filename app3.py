import streamlit as st
import requests
import datetime

# 🔑 Your OpenWeather API Key
API_KEY = "b4b4eb62fa9355c78b3509efd7f3cf3c"
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

# -------------------- Helper Functions --------------------
def get_weather(city):
    """Fetch 5-day forecast from OpenWeather"""
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def get_season():
    """Decide current season in India based on month"""
    month = datetime.datetime.now().month
    if 6 <= month <= 10:
        return "Kharif"
    elif 11 <= month <= 3:
        return "Rabi"
    else:
        return "Zaid"

def recommend_crops(weather_data):
    """Recommend crops based on weather + season"""
    if not weather_data:
        return ["No data available"]

    # Extract rainfall and temperature from next 5 days
    temps = []
    rainfall = 0
    for item in weather_data["list"][:5]:
        temps.append(item["main"]["temp"])
        if "rain" in item and "3h" in item["rain"]:
            rainfall += item["rain"]["3h"]

    avg_temp = sum(temps) / len(temps)
    season = get_season()
    crops = []

    if season == "Kharif":
        if rainfall > 100:
            crops = ["Rice (Paddy)", "Maize", "Soybean"]
        elif 50 <= rainfall <= 100:
            crops = ["Millets", "Groundnut"]
        else:
            crops = ["Pulses (Arhar, Moong)"]

    elif season == "Rabi":
        if 10 <= avg_temp <= 20:
            crops = ["Wheat", "Mustard", "Gram (Chana)"]
        elif 20 < avg_temp <= 25:
            crops = ["Barley", "Lentils", "Peas"]
        else:
            crops = ["Rabi Vegetables"]

    elif season == "Zaid":
        if 25 <= avg_temp <= 35:
            crops = ["Cucumber", "Melon", "Watermelon"]
        else:
            crops = ["Summer Moong", "Vegetables"]

    return crops

# -------------------- Streamlit UI --------------------
st.title("🌱 KrishiMitra : An AI assistant")
st.write("Get best seed recommendations based on weather + season")

city = st.text_input("Enter your city:")

if st.button("Get Recommendation"):
    data = get_weather(city)
    if data:
        crops = recommend_crops(data)
        st.success(f"✅ Best crops to sow in {city} this season:")
        for crop in crops:
            st.write(f"- {crop}")
    else:
        st.error("⚠️ Could not fetch weather data. Try again.")