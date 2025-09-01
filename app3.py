# app.py
import streamlit as st
import requests
import datetime
from statistics import mean

# ---------------------------
# Configuration / API keys
# ---------------------------
OPENWEATHER_KEY = "b4b4eb62fa9355c78b3509efd7f3cf3c"   # your key (already provided)
OPENWEATHER_GEOCODE = "http://api.openweathermap.org/geo/1.0/direct"
OPENWEATHER_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"
SOILGRIDS_QUERY = "https://rest.soilgrids.org/query"   # no key required

# Katha to hectare conversion (approx.)
# 1 Katha ≈ 126.5 m^2 -> 0.01265 hectares (approx)
KATHA_TO_HA = 0.01265

# ---------------------------
# Crop knowledge base (demo)
# Replace these numbers with ICAR/agmarknet data in production
# yield_kg_per_ha = typical yield (kg per hectare)
# cost_per_ha = typical input+labour cost per hectare (INR)
# price_per_kg = market price (INR/kg) (replace with Agmarknet)
# Suitable soil types and seasons are encoded below.
# ---------------------------
CROP_DB = {
    "Rice (Paddy)": {
        "suitable_soil": ["Clay", "Clay loam", "Loam", "Silty clay"],
        "seasons": ["Kharif"],
        "yield_kg_per_ha": 4000,
        "cost_per_ha": 40000,
        "price_per_kg": 20
    },
    "Maize": {
        "suitable_soil": ["Loam", "Sandy loam", "Silt loam"],
        "seasons": ["Kharif","Rabi"],
        "yield_kg_per_ha": 3000,
        "cost_per_ha": 30000,
        "price_per_kg": 18
    },
    "Wheat": {
        "suitable_soil": ["Loam", "Silty loam"],
        "seasons": ["Rabi"],
        "yield_kg_per_ha": 3500,
        "cost_per_ha": 32000,
        "price_per_kg": 22
    },
    "Soybean": {
        "suitable_soil": ["Loam", "Sandy loam"],
        "seasons": ["Kharif"],
        "yield_kg_per_ha": 1200,
        "cost_per_ha": 25000,
        "price_per_kg": 35
    },
    "Pulses": {
        "suitable_soil": ["Loam", "Sandy loam"],
        "seasons": ["Kharif","Rabi"],
        "yield_kg_per_ha": 1000,
        "cost_per_ha": 20000,
        "price_per_kg": 50
    },
    "Watermelon": {
        "suitable_soil": ["Loam", "Sandy loam"],
        "seasons": ["Zaid"],
        "yield_kg_per_ha": 8000,
        "cost_per_ha": 50000,
        "price_per_kg": 5
    }
}

# ---------------------------
# Helpers: Geo -> Soil -> Weather
# ---------------------------
def geocode_place(place_name: str):
    """Return (lat, lon) for a place using OpenWeather geocoding"""
    params = {"q": place_name, "limit": 1, "appid": OPENWEATHER_KEY}
    r = requests.get(OPENWEATHER_GEOCODE, params=params, timeout=15)
    if r.status_code != 200:
        return None
    j = r.json()
    if not j:
        return None
    return j[0]["lat"], j[0]["lon"]

def fetch_soil(lat: float, lon: float):
    """Query SoilGrids for the point. Returns properties dict (raw).
       We'll try to extract a human-friendly texture or fall back."""
    params = {"lat": lat, "lon": lon}
    r = requests.get(SOILGRIDS_QUERY, params=params, timeout=20)
    if r.status_code != 200:
        return None
    return r.json().get("properties", {})

def summarize_soil(properties: dict):
    """Try to extract a simple soil texture class (best-effort).
       SoilGrids has different property names; we'll attempt common patterns.
       If we cannot determine a textual class, we return None -> user will choose manually.
    """
    # 1) Try for texture class variable name (TEXMHT or similar)
    for key in properties:
        kl = key.lower()
        if "tex" in kl and properties.get(key):
            val = properties[key]
            # val may contain depth keys; find first non-empty string value
            if isinstance(val, dict):
                # attempt classic path: val.get('0-5cm', {}).get('values', ...)
                for depth_key in val:
                    d = val[depth_key]
                    # if it contains 'value' or 'w' or string, try to sniff
                    if isinstance(d, dict):
                        for subk in d:
                            subv = d[subk]
                            if isinstance(subv, str) and subv.strip():
                                return subv
                            if isinstance(subv, dict) and "value" in subv:
                                return str(subv["value"])
            elif isinstance(val, str):
                return val

    # 2) Look for sand/clay/silt percentages -> compute simple texture class
    # find numeric arrays under keys containing 'sand' 'clay' 'silt'
    def find_any(key_substr):
        for k in properties:
            if key_substr in k.lower():
                return properties[k]
        return None

    sand = find_any("sand")
    clay = find_any("clay")
    silt = find_any("silt")
    # Try to extract mean values if available
    def extract_mean(obj):
        if obj is None:
            return None
        # If dict with depths, take first depth
        if isinstance(obj, dict):
            for depthk in obj:
                v = obj[depthk]
                # v may have 'mean' or 'value' or 'values'
                if isinstance(v, dict):
                    for candidate in ("mean", "value"):
                        if candidate in v and isinstance(v[candidate], (int, float)):
                            return float(v[candidate])
                    # some responses have numeric inside 'values' dict
                    if "values" in v and isinstance(v["values"], dict):
                        for sub in v["values"]:
                            val = v["values"][sub]
                            if isinstance(val, (int, float)):
                                return float(val)
                elif isinstance(v, (int, float)):
                    return float(v)
        # fallback numeric
        if isinstance(obj, (int, float)):
            return float(obj)
        return None

    sand_v = extract_mean(sand)
    clay_v = extract_mean(clay)
    silt_v = extract_mean(silt)

    if all(x is not None for x in (sand_v, clay_v, silt_v)):
        # crude classification:
        # if clay > 35% -> Clay
        # elif sand > 50% -> Sandy
        # elif silt > 50% -> Silty
        # else Loam
        if clay_v >= 35:
            return "Clay"
        if sand_v >= 50:
            return "Sandy"
        if silt_v >= 50:
            return "Silty"
        return "Loam"

    # If nothing found, return None (we'll ask user)
    return None

def fetch_forecast(lat: float, lon: float):
    """Return the JSON forecast for the lat/lon (OpenWeather 5-day)."""
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_KEY, "units": "metric"}
    r = requests.get(OPENWEATHER_FORECAST, params=params, timeout=15)
    if r.status_code != 200:
        return None
    return r.json()

def summarize_forecast(forecast_json):
    """Return avg_temp (°C) and total_rainfall (mm) over available forecast entries."""
    if not forecast_json or "list" not in forecast_json:
        return None, None
    temps = []
    total_rain = 0.0
    for entry in forecast_json["list"]:
        temps.append(entry["main"]["temp"])
        total_rain += entry.get("rain", {}).get("3h", 0.0)
    avg_temp = mean(temps) if temps else None
    return avg_temp, total_rain

def current_season(dt=None):
    m = (dt or datetime.datetime.now()).month
    if 6 <= m <= 10:
        return "Kharif"
    elif m >= 11 or m <= 3:
        return "Rabi"
    else:
        return "Zaid"

# ---------------------------
# Business logic: matching + profit calc
# ---------------------------
def match_crops(soil_text, season, avg_temp, total_rain_mm):
    """Return candidate crops from CROP_DB ranked by simple match score."""
    candidates = []
    for crop, info in CROP_DB.items():
        score = 0
        # season match
        if season in info["seasons"]:
            score += 3
        # soil match (loose textual match)
        if soil_text:
            for s in info["suitable_soil"]:
                if s.lower() in soil_text.lower() or soil_text.lower() in s.lower():
                    score += 2
                    break
        # weather heuristics (simple)
        # e.g., rice needs more rain
        if crop.lower().find("rice") >= 0 and total_rain_mm and total_rain_mm > 100:
            score += 1
        if crop.lower().find("wheat") >= 0 and avg_temp and 8 <= avg_temp <= 22:
            score += 1
        candidates.append((crop, score))
    # sort by score desc
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [c for c, s in candidates if s >= 1]  # only reasonable ones

def estimate_profit(crop, farm_katha):
    """Estimate expected yield, revenue, cost, profit for given crop & farm size (katha)."""
    info = CROP_DB[crop]
    ha = farm_katha * KATHA_TO_HA
    yield_total = info["yield_kg_per_ha"] * ha        # kg
    revenue = yield_total * info["price_per_kg"]
    total_cost = info["cost_per_ha"] * ha
    profit = revenue - total_cost
    # seed estimate rough: assume seed kg/ha ~ 50 for paddy etc -> not accurate; keep simple demo
    # Use seed rate mapping (kg/ha) approximations
    seed_rate_kg_per_ha = {
        "Rice (Paddy)": 50,
        "Maize": 25,
        "Wheat": 60,
        "Soybean": 60,
        "Pulses": 30,
        "Watermelon": 5
    }
    seed_rate = seed_rate_kg_per_ha.get(crop, 30)
    seed_needed_kg = seed_rate * ha
    return {
        "ha": ha,
        "yield_kg_total": yield_total,
        "revenue_inr": revenue,
        "total_cost_inr": total_cost,
        "profit_inr": profit,
        "seed_needed_kg": seed_needed_kg
    }

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="KrishiProfit — SoilAware Crop Profit", page_icon="🌾", layout="wide")
st.title("🌾 KrishiProfit — soil + weather informed crop & profit advisor")

col1, col2 = st.columns([2,1])
with col1:
    place = st.text_input("Enter your village / city (e.g., Patna):", "Patna")
    farm_katha = st.number_input("Farm size (Katha):", min_value=1, value=5, step=1)
    do_recommend = st.button("Get Recommendation")
with col2:
    st.markdown("**Hints:**\n- Use district/town name for best geocode.\n- We'll auto-detect soil; if not found you'll be asked to choose.")

if do_recommend:
    if not place.strip():
        st.error("Please enter a place name.")
    else:
        # 1) Geocode
        geocode = geocode_place(place)
        if not geocode:
            st.error("Could not geocode the place. Try 'Patna,IN' or a nearby town.")
        else:
            lat, lon = geocode
            st.write(f"📍 Location: {place} → lat {lat:.4f}, lon {lon:.4f}")
            # 2) Soil
            with st.spinner("Fetching soil data from SoilGrids..."):
                soil_props = fetch_soil(lat, lon)
            soil_text = summarize_soil(soil_props)
            if soil_text:
                st.success(f"🟩 Soil detected: **{soil_text}** (from SoilGrids)")
            else:
                st.warning("⚠️ Could not auto-detect a clear soil class. Please select below:")
                soil_text = st.selectbox("Select soil type (if you know):", ["Loam", "Clay", "Sandy", "Silty", "Clay loam"], index=0)
            # 3) Weather
            with st.spinner("Fetching weather forecast..."):
                forecast = fetch_forecast(lat, lon)
            avg_temp, total_rain = summarize_forecast(forecast)
            if avg_temp is None:
                st.warning("Could not fetch weather summary.")
            else:
                st.info(f"🌡 5-day avg temp: {avg_temp:.1f} °C | 🌧 total rain (5-day): {total_rain:.1f} mm")
            # 4) Season & candidate crops
            season = current_season()
            st.write(f"🗓 Current season (auto): **{season}**")
            candidates = match_crops(soil_text, season, avg_temp, total_rain)
            if not candidates:
                st.warning("No candidate crops found by logic. Showing all crops for manual pick.")
                candidates = list(CROP_DB.keys())
            st.success("✅ Candidate crops (ranked):")
            for c in candidates:
                st.write(f"- {c}")
            # 5) Profit estimation for top 2 candidates
            st.subheader("Profit Estimates")
            topk = candidates[:2]
            for c in topk:
                est = estimate_profit(c, farm_katha)
                st.markdown(f"### {c}")
                st.write(f"• Area: **{farm_katha} Katha** = **{est['ha']:.4f} ha**")
                st.write(f"• Expected total yield: **{est['yield_kg_total']:.0f} kg**")
                st.write(f"• Market price used: **₹{CROP_DB[c]['price_per_kg']}/kg** (replace with Agmarknet for accuracy)")
                st.write(f"• Expected revenue: **₹{est['revenue_inr']:.0f}**")
                st.write(f"• Estimated total cost: **₹{est['total_cost_inr']:.0f}**")
                st.write(f"• **Estimated profit:** **₹{est['profit_inr']:.0f}**")
                st.write(f"• Seed needed (approx): **{est['seed_needed_kg']:.1f} kg**")
                st.markdown("---")

            st.info("⚠️ Notes: Prices & yields are demo values. For production, we will replace prices with Agmarknet and yields with ICAR/state data.")