import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Dummy crop dataset
# -----------------------------
data = {
    "crop": ["Wheat", "Rice", "Maize", "Pulses", "Veggies"],
    "soil_type": ["Loamy", "Clayey", "Sandy", "Loamy", "Alluvial"],
    "rainfall_mm": [400, 1200, 600, 300, 500],
    "cost_per_acre": [15000, 18000, 12000, 10000, 20000],
    "yield_per_acre": [3200, 4000, 2800, 1500, 5000],  # in kg
    "mandi_price_per_kg": [22, 20, 18, 45, 30]
}

df = pd.DataFrame(data)

# -----------------------------
# Hardcoded location → soil mapping
# -----------------------------
location_soil_map = {
    "Patna": "Loamy",
    "Gaya": "Sandy",
    "Darbhanga": "Clayey",
    "Bhagalpur": "Alluvial"
}

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="KrishiProfit", page_icon="🌾", layout="wide")

st.title("🌾 KrishiProfit – Smart Crop Advisor")
st.write("Helping farmers choose **profitable crops** based on soil, rainfall, and mandi prices.")

# Input section
location = st.text_input("Enter your district (e.g., Patna, Gaya, Darbhanga, Bhagalpur):")
rainfall = st.number_input("Enter average rainfall in your area (mm):", min_value=0, max_value=2000, step=50)

if location in location_soil_map:
    soil_type = location_soil_map[location]
    st.info(f"📍 Soil type for {location}: **{soil_type}**")
else:
    soil_type = st.selectbox("Select your soil type:", df['soil_type'].unique())

# -----------------------------
# Recommendation Logic
# -----------------------------
if st.button("Get Crop Recommendation"):
    suitable_crops = df[
        (df['soil_type'] == soil_type) &
        (df['rainfall_mm'] <= rainfall + 200) &
        (df['rainfall_mm'] >= rainfall - 200)
    ]

    if suitable_crops.empty:
        st.warning("⚠️ No matching crop found. Try adjusting inputs.")
    else:
        # Calculate profit
        suitable_crops["profit"] = (
            suitable_crops["yield_per_acre"] * suitable_crops["mandi_price_per_kg"]
        ) - suitable_crops["cost_per_acre"]

        top_crops = suitable_crops.sort_values(by="profit", ascending=False).head(3)

        st.subheader("✅ Recommended Crops with Expected Profit")
        st.dataframe(top_crops[["crop", "profit"]])

        # -----------------------------
        # Chart: Profit comparison
        # -----------------------------
        fig, ax = plt.subplots()
        ax.bar(top_crops["crop"], top_crops["profit"], color="green")
        ax.set_ylabel("Profit per acre (₹)")
        ax.set_title("Profitability of Recommended Crops")
        st.pyplot(fig)

        st.success("🎉 These crops are most profitable for your region!")