# farmer_form.py
import streamlit as st
import pandas as pd
import os

# Title
st.title("🌱 KrishiMitra- An Ai Assistant")

st.write("Enter your farm details below 👇")

# Input fields
name = st.text_input("👨‍🌾 Farmer Name")
location = st.text_input("📍 Location (Village/District)")
land_size = st.number_input("🌾 Land Size (in acres)", min_value=0.0, step=0.1)
current_crop = st.text_input("🌱 Current Crop (if any)")

# Submit button
if st.button("Submit"):
    farmer_data = {
        "Name": name,
        "Location": location,
        "Land Size (acres)": land_size,
        "Current Crop": current_crop
    }

    # Save to CSV
    file_path = "farmers.csv"

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = df.append(farmer_data, ignore_index=True)
    else:
        df = pd.DataFrame([farmer_data])

    df.to_csv(file_path, index=False)
    st.success("✅ Farmer data saved successfully!")

    st.write("### Current Records")
    st.dataframe(df)