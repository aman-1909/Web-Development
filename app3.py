import streamlit as st
import requests

# --- API KEYS ---
OPENWEATHER_API_KEY = "b4b4eb62fa9355c78b3509efd7f3cf3c"

# --- Helper Functions ---

def get_weather(city):
    """Fetch 7-day forecast from OpenWeather API"""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or "list" not in data:
        return None

    temps = [entry["main"]["temp"] for entry in data["list"]]
    avg_temp = sum(temps) / len(temps)
    return avg_temp


def get_coordinates(city):
    """Get lat/lon of city using OpenWeather Geocoding API"""
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data:
        return data[0]["lat"], data[0]["lon"]
    return None, None


def get_soil_info(lat, lon):
    """Fetch soil info from SoilGrids API"""
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=clay&property=sand&property=silt&depth=sl1"
    response = requests.get(url)
    data = response.json()

    if "properties" not in data:
        return None

    clay = data["properties"]["layers"][0]["depths"][0]["values"]["mean"]
    sand = data["properties"]["layers"][1]["depths"][0]["values"]["mean"]
    silt = data["properties"]["layers"][2]["depths"][0]["values"]["mean"]

    # Simple classification
    if clay > 35:
        soil_type = "Clay"
    elif sand > 50:
        soil_type = "Sandy"
    elif silt > 40:
        soil_type = "Loamy"
    else:
        soil_type = "Mixed"

    return soil_type


def recommend_crop(temp, soil, farm_size):
    """Recommend crops based on soil + temperature"""
    crops = {
        "Rice": {"temp_range": (20, 35), "soil": ["Clay", "Loamy"], "yield_per_katha": 30, "price_per_kg": 20},
        "Wheat": {"temp_range": (10, 25), "soil": ["Loamy"], "yield_per_katha": 20, "price_per_kg": 22},
        "Maize": {"temp_range": (18, 30), "soil": ["Sandy", "Loamy"], "yield_per_katha": 15, "price_per_kg": 18},
        "Pulses": {"temp_range": (20, 30), "soil": ["Sandy", "Loamy"], "yield_per_katha": 12, "price_per_kg": 60},
    }

    best_crop = None
    best_profit = 0

    for crop, details in crops.items():
        min_temp, max_temp = details["temp_range"]
        if min_temp <= temp <= max_temp and soil in details["soil"]:
            yield_est = details["yield_per_katha"] * farm_size
            profit_est = yield_est * details["price_per_kg"]
            if profit_est > best_profit:
                best_profit = profit_est
                best_crop = (crop, yield_est, profit_est)

    return best_crop


# --- Streamlit App ---

st.title("🌾 Smart Crop Recommendation System")
st.write("Enter your location and farm size to get the best crop suggestion with profit estimation.")

city = st.text_input("Enter your City:", "Patna")
farm_size = st.number_input("Enter your farm size (in Katha):", min_value=1, step=1)

if st.button("Get Recommendation"):
    temp = get_weather(city)
    lat, lon = get_coordinates(city)
    soil_type = get_soil_info(lat, lon)

    if temp and soil_type:
        recommendation = recommend_crop(temp, soil_type, farm_size)
        if recommendation:
            crop, yield_est, profit_est = recommendation
            st.success(f"🌍 Location: {city}")
            st.info(f"🌡 Avg Temp: {temp:.2f}°C | 🪨 Soil Type: {soil_type}")
            st.success(f"✅ Recommended Crop: **{crop}**")
            st.write(f"🌱 Estimated Yield: {yield_est} kg")
            st.write(f"💰 Estimated Profit: ₹{profit_est}")
        else:
            st.warning("⚠️ No suitable crop found for your conditions.")
    else:
        st.error("Could not fetch weather or soil info. Try another location.")