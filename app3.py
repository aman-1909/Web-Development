import streamlit as st
import requests

# --- Title ---
st.title("🌱  Krishi Mitra : An AI Assistant")

# --- User Inputs ---
city = st.text_input("Enter your city:", "Patna")
farm_size = st.number_input("Enter your farm size (in Katha):", min_value=1, step=1)

if st.button("Get Crop Recommendation"):
    if not city:
        st.warning("Please enter a city")
    else:
        # --- Fetch Weather Data ---
        api_key = "b4b4eb62fa9355c78b3509efd7f3cf3c"  # your API key
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['list'][0]['main']['temp']
            weather = data['list'][0]['weather'][0]['description']

            st.success(f"🌍 Location: {city}")
            st.info(f"🌡️ Temperature: {temp} °C | 🌦️ Weather: {weather}")

            # --- Simple Crop Recommendation (Rule-based) ---
            if 20 <= temp <= 30:
                crop = "Wheat 🌾"
            elif temp > 30:
                crop = "Paddy 🌾"
            else:
                crop = "Mustard 🌻"

            st.write(f"👉 Recommended Crop: **{crop}**")

            # --- Basic Seed Estimate (very rough demo logic) ---
            if crop == "Wheat 🌾":
                seed_rate = 40  # kg per Katha (example)
            elif crop == "Paddy 🌾":
                seed_rate = 50
            else:
                seed_rate = 30

            total_seed = farm_size * seed_rate
            st.write(f"🪴 Estimated Seed Requirement: **{total_seed} kg** for {farm_size} Katha land")

        else:
            st.error("Failed to fetch weather data. Please check the city name.")