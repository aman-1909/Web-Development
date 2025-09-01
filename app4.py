import streamlit as st
import requests
import random

# OpenWeather API key
API_KEY = "b4b4eb62fa9355c78b3509efd7f3cf3c"

# Mock soil dataset (replace later with real soil API)
soil_data = {
    "Patna": "Alluvial",
    "Gaya": "Loamy",
    "Nalanda": "Sandy loam",
    "Bhagalpur": "Clay",
    "Darbhanga": "Silty loam"
}

# Crop recommendations by soil + season
crop_data = {
    "Alluvial": ["Wheat", "Rice", "Maize", "Sugarcane"],
    "Loamy": ["Pulses", "Mustard", "Potato", "Wheat"],
    "Sandy loam": ["Groundnut", "Vegetables", "Potato"],
    "Clay": ["Paddy", "Jute", "Sugarcane"],
    "Silty loam": ["Maize", "Wheat", "Vegetables"]
}

# Average profit per Katha (mock ₹ values in INR)
profit_data = {
    "Wheat": 2500,
    "Rice": 3000,
    "Maize": 2200,
    "Sugarcane": 4000,
    "Pulses": 2000,
    "Mustard": 2700,
    "Potato": 5000,
    "Groundnut": 3500,
    "Vegetables": 6000,
    "Jute": 3200
}


def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if "list" in data:
            temp = data["list"][0]["main"]["temp"]
            rain = data["list"][0]["weather"][0]["main"]
            return temp, rain
        else:
            return None, None
    except:
        return None, None


def main():
    st.title("🌱 KrishiAlert – Smart Crop Recommendation")

    # User inputs
    city = st.text_input("Enter your location (City/Village):", "Patna")
    farm_size = st.number_input("Enter your farm size (in Katha):", min_value=1, value=10)

    if st.button("Get Recommendations"):
        temp, rain = get_weather(city)

        if temp is None:
            st.error("⚠️ Weather data not found! Please try another location.")
            return

        # Soil type detection (mock)
        soil_type = soil_data.get(city, random.choice(list(soil_data.values())))

        st.subheader("📍 Location Insights")
        st.write(f"🌡️ Temperature: {temp}°C")
        st.write(f"🌧️ Weather: {rain}")
        st.write(f"🌎 Soil Type: {soil_type}")

        # Crop recommendations
        recommended_crops = crop_data.get(soil_type, [])
        st.subheader("🌾 Recommended Crops")
        for crop in recommended_crops:
            if crop in profit_data:
                profit = profit_data[crop] * farm_size
                st.success(f"✅ {crop} → Estimated Profit: ₹{profit:,}")

        st.info("💡 These crops are suggested based on soil + season. Future versions will use live soil API & real mandi price data.")

if __name__ == "__main__":
    main()