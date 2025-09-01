import streamlit as st
import requests
import pandas as pd

# App Title
st.title("🌾 KrishiMitra - An AI Assistant")

# ---- Farmer Info (Day 1 Part) ----
st.header("👨‍🌾 Farmer Information")
name = st.text_input("Enter your Name:", "")
city = st.text_input("Enter your City/Village:", "Patna")

# ---- Weather Forecast (Day 2 Part) ----
API_KEY = "b4b4eb62fa9355c78b3509efd7f3cf3c"

if st.button("Get Weather Forecast"):
    if city.strip() == "":
        st.warning("⚠️ Please enter a city or village name.")
    else:
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
            response = requests.get(url)
            data = response.json()

            if data.get("cod") != "200":
                st.error("❌ Could not fetch data. Please check the city/village name.")
            else:
                forecast_list = []
                for entry in data["list"]:
                    dt_txt = entry["dt_txt"]
                    temp = entry["main"]["temp"]
                    humidity = entry["main"]["humidity"]
                    rain = entry.get("rain", {}).get("3h", 0)  # rainfall in mm (3hr)
                    wind = entry["wind"]["speed"]

                    forecast_list.append([dt_txt, temp, humidity, rain, wind])

                # Convert to DataFrame
                df = pd.DataFrame(
                    forecast_list,
                    columns=["Date/Time", "Temp (°C)", "Humidity (%)", "Rain (mm)", "Wind (m/s)"]
                )

                # Greeting Farmer
                st.success(f"👋 Hello {name if name else 'Farmer'}! Here is your forecast for **{city}**:")

                # Show table
                st.dataframe(df)

                # Show graph (Temp + Rainfall)
                st.line_chart(df[["Temp (°C)", "Rain (mm)"]].set_index(df["Date/Time"]))

        except Exception as e:
            st.error(f"⚠️ Error: {e}")