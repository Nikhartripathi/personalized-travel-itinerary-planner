import json
import math
import os
from datetime import date, timedelta
from io import BytesIO
from typing import Any

import requests
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

APP_NAME = "Personalized Travel Itinerary Planner"
INR_PER_USD = 83.0  # planning estimate; update before real-world budgeting
CITIES = {
    "Goa, India": {"country": "India", "currency": "INR", "symbol": "₹", "mood": ["Beach", "Food", "Nightlife", "Friends", "Couple"], "season": "Nov–Mar", "lat": 15.49, "lon": 73.83,
        "places": [("Baga Beach", 15.555, 73.751, "Beach", 0), ("Fort Aguada", 15.492, 73.773, "History", 150), ("Fontainhas", 15.498, 73.831, "Cultural", 0), ("Dona Paula Viewpoint", 15.458, 73.803, "Outdoor", 0), ("Anjuna Flea Market", 15.573, 73.741, "Shopping", 100), ("Basilica of Bom Jesus", 15.500, 73.911, "History", 50), ("Miramar Beach", 15.477, 73.808, "Beach", 0), ("Goan Spice Lunch", 15.501, 73.829, "Food", 500), ("Sunset Seafood Dinner", 15.555, 73.751, "Food", 700)]},
    "Manali, India": {"country": "India", "currency": "INR", "symbol": "₹", "mood": ["Mountains", "Adventure", "Friends", "Couple", "Family"], "season": "Mar–Jun / Dec–Feb", "lat": 32.24, "lon": 77.19,
        "places": [("Hadimba Devi Temple", 32.243, 77.181, "History", 30), ("Old Manali Café Walk", 32.257, 77.185, "Food", 350), ("Manu Temple", 32.260, 77.186, "Cultural", 0), ("Solang Valley", 32.316, 77.158, "Adventure", 800), ("Vashisht Hot Springs", 32.251, 77.192, "Relaxed", 30), ("Mall Road", 32.239, 77.189, "Shopping", 200), ("Naggar Castle", 32.115, 77.173, "History", 100), ("Riverside Picnic", 32.252, 77.177, "Outdoor", 250)]},
    "Jaipur, India": {"country": "India", "currency": "INR", "symbol": "₹", "mood": ["Cultural", "History", "Food", "Family", "Couple"], "season": "Oct–Mar", "lat": 26.91, "lon": 75.79,
        "places": [("Hawa Mahal", 26.923, 75.826, "History", 100), ("City Palace", 26.925, 75.823, "History", 300), ("Jantar Mantar", 26.924, 75.824, "History", 200), ("Johari Bazaar Walk", 26.919, 75.826, "Shopping", 250), ("Amber Fort", 26.985, 75.851, "History", 500), ("Jal Mahal Viewpoint", 26.953, 75.846, "Outdoor", 0), ("Rajasthani Thali Lunch", 26.920, 75.821, "Food", 450), ("Cultural Folk Dinner", 26.923, 75.820, "Cultural", 800)]},
    "Mumbai, India": {"country": "India", "currency": "INR", "symbol": "₹", "mood": ["Urban", "Food", "History", "Nightlife", "Friends"], "season": "Nov–Feb", "lat": 19.08, "lon": 72.88,
        "places": [("Gateway of India", 18.922, 72.834, "History", 0), ("Colaba Causeway", 18.915, 72.827, "Shopping", 200), ("Marine Drive", 18.944, 72.823, "Outdoor", 0), ("Chhatrapati Shivaji Terminus", 18.940, 72.835, "History", 0), ("Bandra Street Food", 19.060, 72.836, "Food", 350), ("Sanjay Gandhi National Park", 19.214, 72.910, "Adventure", 85), ("Kala Ghoda Art Walk", 18.928, 72.832, "Cultural", 100)]},
    "Paris, France": {"country": "France", "currency": "EUR", "symbol": "€", "mood": ["Cultural", "History", "Food", "Couple", "Urban"], "season": "Apr–Jun / Sep–Oct", "lat": 48.86, "lon": 2.35,
        "places": [("Eiffel Tower area", 48.858, 2.295, "History", 25), ("Louvre Museum", 48.860, 2.337, "History", 22), ("Tuileries Garden", 48.863, 2.327, "Outdoor", 0), ("Latin Quarter Café", 48.852, 2.344, "Food", 20), ("Notre-Dame area", 48.853, 2.349, "Cultural", 0), ("Montmartre Walk", 48.886, 2.343, "Cultural", 0), ("Seine Riverside Dinner", 48.858, 2.350, "Food", 45)]},
}
# Correct coordinates for final Paris item (kept separate to make dataset easy to edit)
CITIES["Paris, France"]["places"][-1] = ("Seine Riverside Dinner", 48.858, 2.350, "Food", 45)

VIBE_TAGS = {
    "Beach": ["Beach", "Outdoor", "Food"], "Mountains": ["Outdoor", "Adventure", "Relaxed"],
    "Cultural": ["Cultural", "History", "Food"], "Urban": ["Shopping", "Food", "Cultural"],
    "Adventure": ["Adventure", "Outdoor"], "Food": ["Food"], "History": ["History", "Cultural"],
    "Nightlife": ["Food", "Shopping"], "Relaxed": ["Outdoor", "Relaxed"]
}
TIME_SLOTS = ["Morning Sightseeing", "Lunch Recommendation", "Afternoon Leisure", "Evening Dining & Entertainment"]

st.set_page_config(page_title=APP_NAME, page_icon="🧭", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background:linear-gradient(180deg,#f7fbfa 0%,#fffaf3 100%);}
.hero {padding:1.8rem 2rem;border-radius:22px;background:linear-gradient(120deg,#123d3b,#26766c);color:white;margin-bottom:1rem;}
.hero h1 {font-family:'Playfair Display',serif;font-size:2.5rem;margin:0;}
.hero p {color:#e2f2ec;margin:.45rem 0 0 0;font-size:1.02rem;}
.eyebrow {letter-spacing:.14em;text-transform:uppercase;font-size:.75rem;font-weight:700;color:#f5c98b;}
.card {padding:1rem 1.1rem;border:1px solid #e4ebe7;border-radius:16px;background:white;margin:.35rem 0;box-shadow:0 3px 12px rgba(25,65,55,.04);}
.tag {display:inline-block;padding:.22rem .6rem;border-radius:999px;background:#e7f4ee;color:#216458;font-size:.78rem;margin:2px;}
.small {color:#64756f;font-size:.88rem;}
div[data-testid="stMetric"] {background:white;border:1px solid #e4ebe7;padding:12px;border-radius:14px;}
</style>
""", unsafe_allow_html=True)

if "trips" not in st.session_state: st.session_state.trips = []
if "current_trip" not in st.session_state: st.session_state.current_trip = None
if "chat" not in st.session_state: st.session_state.chat = []

def haversine(a, b):
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2-lat1, lon2-lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(h))

def clustered_places(city, interests, vibe, budget, days):
    data = CITIES[city]
    wanted = set(interests)
    wanted.update(VIBE_TAGS.get(vibe, []))
    places = [p for p in data["places"] if p[3] in wanted]
    if len(places) < days*3: places = data["places"][:]
    # Budget-aware filtering for paid attractions; keep at least 3 options.
    cap = {"Budget": 350, "Moderate": 900, "Luxury": 100000}[budget]
    filtered = [p for p in places if p[4] <= cap]
    places = filtered if len(filtered) >= min(3, len(places)) else places
    # Greedy nearest-neighbour ordering; days are chunks from this proximity-aware order.
    ordered, remaining = [], places[:]
    current = (data["lat"], data["lon"])
    while remaining:
        idx = min(range(len(remaining)), key=lambda i: haversine(current, (remaining[i][1], remaining[i][2])))
        p = remaining.pop(idx)
        ordered.append(p); current = (p[1], p[2])
    return ordered

def cost_for(place, budget):
    base = place[4]
    multiplier = {"Budget": .75, "Moderate": 1.0, "Luxury": 1.8}[budget]
    return round(base * multiplier)

def build_demo_itinerary(prefs):
    city, days = prefs["destination"], prefs["duration"]
    info = CITIES[city]
    places = clustered_places(city, prefs["interests"], prefs["vibe"], prefs["budget"], days)
    plan = []
    idx = 0
    for day in range(1, days+1):
        day_places = []
        for slot in range(4):
            if idx >= len(places): idx = 0
            place = places[idx]; idx += 1
            label = TIME_SLOTS[slot]
            if slot == 0: time = "09:00–11:30"
            elif slot == 1: time = "12:00–13:30"
            elif slot == 2: time = "14:30–17:00"
            else: time = "18:30–21:00"
            desc = {
                0: f"Explore {place[0]} and nearby highlights. Keep walking/transit within the same area where possible.",
                1: f"Try a local meal near {place[0]}. Check opening hours and dietary options before visiting.",
                2: f"Enjoy {place[0]} at a comfortable pace; leave room for rest and spontaneous discoveries.",
                3: f"Wrap up with {place[0]} and local dining or entertainment nearby."
            }[slot]
            day_places.append({"slot": label, "time": time, "name": place[0], "category": place[3],
                               "description": desc, "cost": cost_for(place, prefs["budget"]),
                               "lat": place[1], "lon": place[2]})
        plan.append({"day": day, "date": (prefs["start_date"] + timedelta(days=day-1)).isoformat(),
                     "area_note": "Nearby attractions are grouped to reduce backtracking; confirm local transit and opening times.",
                     "activities": day_places})
    return plan

def llm_generate(prefs, api_provider, api_key):
    """Optional LLM enhancement. Any failure gracefully falls back to the local demo planner."""
    prompt = f"""You are a careful travel itinerary planner. Return ONLY valid JSON with key 'days', an array of {prefs['duration']} objects. Each object has day, date, area_note, activities. Each day must have four activities with slot, time, name, category, description, cost, lat, lon. Slots in order: {TIME_SLOTS}. Destination: {prefs['destination']}; vibe: {prefs['vibe']}; budget: {prefs['budget']}; party: {prefs['party']}; pace: {prefs['pace']}; interests: {prefs['interests']}; dates: {prefs['start_date']} for {prefs['duration']} days. Use plausible cost estimates in destination local currency and coordinates when known. Do not claim real-time availability. Include geographically nearby activities together. Output JSON only."""
    if not api_key: return None, "Demo mode active — no API key supplied."
    try:
        if api_provider == "Gemini":
            model = "gemini-2.0-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            r = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}],
                                         "generationConfig":{"temperature":0.5,"responseMimeType":"application/json"}}, timeout=45)
            r.raise_for_status()
            raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            url = "https://api.groq.com/openai/v1/chat/completions"
            r = requests.post(url, headers={"Authorization":f"Bearer {api_key}"},
                json={"model":"llama-3.3-70b-versatile","messages":[{"role":"system","content":"Return only valid JSON."},{"role":"user","content":prompt}],"temperature":0.5}, timeout=45)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"]
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        days = parsed.get("days", [])
        if not days: return None, "The AI response did not include a valid days list; using demo mode."
        return days, f"Generated with {api_provider}."
    except Exception as exc:
        return None, f"AI service unavailable ({type(exc).__name__}); using demo mode."

def fmt_money(amount, currency):
    symbols = {"INR":"₹","USD":"$","EUR":"€","GBP":"£","JPY":"¥"}
    return f"{symbols.get(currency, currency+' ')}{amount:,.0f}"

def total_cost(trip):
    return sum(float(a.get("cost",0) or 0) for d in trip["days"] for a in d.get("activities",[]))

def generate_pdf(trip):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TripTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=colors.HexColor("#174d46"), alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="DayTitle", parent=styles["Heading2"], textColor=colors.HexColor("#216b5d"), spaceBefore=12))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=8.7, leading=12, spaceAfter=3))
    story = [Paragraph("Your Journey, Thoughtfully Planned", styles["TripTitle"]),
             Paragraph(trip["destination"], styles["Heading1"]),
             Paragraph(f"{trip['start_date']} · {trip['duration']} days · {trip['party']} · {trip['budget']} budget", styles["BodyText"]),
             Spacer(1, 5*mm),
             Paragraph("Trip snapshot", styles["Heading2"]),
             Paragraph(f"Vibe: {trip['vibe']} | Pace: {trip['pace']} | Interests: {', '.join(trip['interests'])}", styles["BodyText"]),
             Paragraph(f"Estimated activity costs: {fmt_money(total_cost(trip), trip['currency'])}", styles["BodyText"]),
             Spacer(1, 5*mm)]
    for day in trip["days"]:
        story.append(Paragraph(f"Day {day.get('day')} — {day.get('date','')}", styles["DayTitle"]))
        story.append(Paragraph(day.get("area_note","Nearby stops are grouped where possible."), styles["BodySmall"]))
        rows = [["Time", "Plan", "Details", "Est. cost"]]
        for a in day.get("activities", []):
            rows.append([a.get("time",""), a.get("name",""), a.get("description",""), fmt_money(float(a.get("cost",0) or 0), trip["currency"])])
        table = Table([[Paragraph(str(cell), styles["BodySmall"]) for cell in row] for row in rows],
                      colWidths=[24*mm, 34*mm, 85*mm, 25*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#174d46")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),.35,colors.HexColor("#d9e4df")),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f2f8f5")]),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)
        ]))
        story += [table, Spacer(1, 3*mm)]
    story += [PageBreak(), Paragraph("Before You Go", styles["Heading1"]),
              Paragraph("Emergency & practical checklist", styles["Heading2"])]
    checklist = [
        "Save the local emergency number and your country's embassy/consulate contact if travelling internationally.",
        "Keep copies of ID, tickets, accommodation details, insurance, and prescriptions in a secure offline location.",
        "Share your itinerary and check-in plan with a trusted contact.",
        "Verify attraction opening hours, ticket rules, weather, transit disruptions, and visa requirements before departure.",
        "Keep a small first-aid kit, water, charged phone, power bank, and emergency funds.",
        "For emergencies, contact the official local emergency services. This guide does not replace local advice."
    ]
    for item in checklist: story.append(Paragraph("☐ " + item, styles["BodyText"])); story.append(Spacer(1, 4))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Planning note: Costs, routes, and suggestions are estimates, not live prices or reservations. Confirm details with official providers.", styles["Italic"]))
    doc.build(story)
    return buffer.getvalue()

st.markdown(f"""<div class="hero"><div class="eyebrow">TRAVEL, WITH A LITTLE MORE WONDER</div><h1>🧭 {APP_NAME}</h1><p>Build a trip around your mood, keep each day flowing, and take your guide offline.</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ✨ Planner settings")
    provider = st.selectbox("AI provider", ["Gemini", "Groq"])
    api_key = st.text_input(f"{provider} API key (optional)", type="password", help="Stored only in this active session. Leave blank to use the built-in demo planner.")
    st.caption("🔒 Demo mode works without a key. Do not paste keys into public code or share screenshots containing them.")
    st.divider()
    st.markdown("### 🧳 Your trip")
    destination_options = ["Surprise me"] + list(CITIES.keys())
    destination_choice = st.selectbox("Destination", destination_options)
    vibe = st.selectbox("Travel mood / vibe", ["Beach", "Mountains", "Cultural", "Urban", "Adventure", "Food", "History", "Nightlife", "Relaxed"])
    duration = st.slider("Trip duration (days)", 1, 10, 3)
    start_date = st.date_input("Start date", value=date.today() + timedelta(days=14), min_value=date.today())
    budget = st.select_slider("Budget level", options=["Budget", "Moderate", "Luxury"], value="Moderate")
    party = st.selectbox("Travel party", ["Solo", "Couple", "Family", "Friends"])
    pace = st.select_slider("Pace", options=["Relaxed", "Moderate", "Fast-Paced"], value="Moderate")
    interests = st.multiselect("Interests", ["Food", "Adventure", "History", "Nightlife", "Cultural", "Outdoor", "Shopping", "Relaxed"], default=["Food", "History", "Outdoor"])
    currency = st.selectbox("Display cost currency", ["INR", "USD", "EUR", "GBP", "JPY"], index=0)
    generate = st.button("✨ Create my trip", type="primary", use_container_width=True)

def recommend_destinations(vibe, budget, party, start_date):
    scores = []
    month = start_date.month
    for city, info in CITIES.items():
        score = 0
        if vibe in info["mood"]: score += 3
        if party in info["mood"]: score += 1
        season_months = {"Goa, India":[11,12,1,2,3], "Manali, India":[3,4,5,6,12,1,2], "Jaipur, India":[10,11,12,1,2,3], "Mumbai, India":[11,12,1,2], "Paris, France":[4,5,6,9,10]}
        if month in season_months.get(city, []): score += 2
        if budget == "Budget" and info["country"] == "India": score += 1
        tags = list(dict.fromkeys(info["mood"][:3] + [info["season"]]))
        scores.append((score, city, tags, info["season"]))
    return sorted(scores, reverse=True)[:3]

if generate:
    if destination_choice == "Surprise me":
        recommendations = recommend_destinations(vibe, budget, party, start_date)
        chosen = recommendations[0][1]
    else:
        chosen = destination_choice
    prefs = {"destination":chosen, "vibe":vibe, "duration":duration, "start_date":start_date, "budget":budget,
             "party":party, "pace":pace, "interests":interests or ["Food","Outdoor"], "currency":CITIES[chosen]["currency"]}
    with st.spinner("Curating your journey…"):
        ai_days, status = llm_generate(prefs, provider, api_key)
        days = ai_days if ai_days else build_demo_itinerary(prefs)
    trip = {**prefs, "days":days, "created_at":date.today().isoformat(), "ai_status":status}
    st.session_state.current_trip = trip
    st.session_state.trips.insert(0, trip)
    st.session_state.trips = st.session_state.trips[:20]
    st.session_state.chat = []
    st.toast("Your trip is ready!")

if destination_choice == "Surprise me":
    st.markdown("### 🌍 Not sure where to go?")
    recs = recommend_destinations(vibe, budget, party, start_date)
    cols = st.columns(3)
    for col, (score, city, tags, season) in zip(cols, recs):
        with col:
            st.markdown(f"""<div class="card"><h3>{city}</h3><p class="small">Best season: {season}</p>{''.join(f'<span class="tag">{tag}</span>' for tag in tags)}</div>""", unsafe_allow_html=True)
            if st.button(f"Plan a trip to {city}", key=f"rec_{city}"):
                st.session_state["quick_destination"] = city
                st.info("Choose this destination in the sidebar and click Create my trip.")

tab1, tab2, tab3, tab4 = st.tabs(["🌍 Destination ideas", "🗓️ Day-by-day itinerary", "🎨 Customize & swap", "🧳 Saved trips & PDF"])

with tab1:
    st.subheader("Find a destination that matches your mood")
    st.write("Recommendations consider your selected vibe, travel party, budget, and seasonal fit. These are planning suggestions, not live weather forecasts.")
    recs = recommend_destinations(vibe, budget, party, start_date)
    cols = st.columns(3)
    for col, (score, city, tags, season) in zip(cols, recs):
        info = CITIES[city]
        with col:
            st.markdown(f"""<div class="card"><h3>{city}</h3><p>🗓️ Suggested season: <b>{season}</b></p><p>💸 Budget fit: {'Value-friendly' if budget == 'Budget' and info['country']=='India' else 'Flexible'}</p>{''.join(f'<span class="tag">{t}</span>' for t in tags)}</div>""", unsafe_allow_html=True)
    st.caption("The sample destination catalog can be extended in app.py. Seasonal labels are general guidance; check forecasts and official travel advisories.")

with tab2:
    trip = st.session_state.current_trip
    if not trip:
        st.info("Set your preferences in the sidebar and click **Create my trip** to see a day-by-day plan.")
    else:
        st.markdown(f"## {trip['destination']} · {trip['duration']} days")
        st.caption(trip.get("ai_status",""))
        total = total_cost(trip)
        cur = trip.get("currency", "INR")
        fx = {"INR":1, "USD":1/INR_PER_USD, "EUR":1/90, "GBP":1/105, "JPY":1/0.56}
        st.metric("Estimated activity costs", fmt_money(total*fx.get(currency,1), currency))
        st.caption("Activity estimates only; transport, lodging, flights and personal spending may be additional.")
        for day in trip["days"]:
            with st.expander(f"Day {day.get('day', '?')} · {day.get('date','')} — {day.get('area_note','')}", expanded=(day.get("day")==1)):
                for activity in day.get("activities", []):
                    st.markdown(f"""<div class="card"><b>{activity.get('time','')}</b> · <span class="tag">{activity.get('slot','Activity')}</span><h4>{activity.get('name','Explore')}</h4><p>{activity.get('description','')}</p><span class="small">Category: {activity.get('category','General')} · Est. cost: {fmt_money(float(activity.get('cost',0) or 0)*fx.get(currency,1), currency)}</span></div>""", unsafe_allow_html=True)
        st.info("Route optimization uses a nearest-neighbour distance heuristic over the included sample coordinates. Verify real routes, accessibility, opening hours, and travel time before departure.")

with tab3:
    trip = st.session_state.current_trip
    if not trip:
        st.info("Create a trip first to customize activities.")
    else:
        st.subheader("Make the itinerary feel more like you")
        day_num = st.selectbox("Choose a day to regenerate", [int(d.get("day",i+1)) for i,d in enumerate(trip["days"])], key="regen_day")
        day_obj = next((d for d in trip["days"] if int(d.get("day",0)) == day_num), None)
        if day_obj:
            st.caption("Regenerate only this day; the rest of your trip stays as it is.")
            if st.button("🔄 Regenerate this day", type="primary"):
                prefs = {k:trip[k] for k in ["destination","vibe","duration","start_date","budget","party","pace","interests","currency"]}
                fresh = build_demo_itinerary(prefs)
                replacement = next((d for d in fresh if d["day"] == day_num), fresh[0])
                trip["days"] = [replacement if int(d.get("day",0)) == day_num else d for d in trip["days"]]
                st.session_state.current_trip = trip
                st.success(f"Day {day_num} refreshed. Other days were preserved.")
                st.rerun()
            st.divider()
            st.markdown(f"### Day {day_num} activities")
            for i, activity in enumerate(day_obj.get("activities", [])):
                with st.container(border=True):
                    st.write(f"**{activity.get('time','')} · {activity.get('name','')}**")
                    st.caption(activity.get("description",""))
                    c1, c2 = st.columns([3,1])
                    with c1:
                        request = st.text_input("What would you prefer instead?", placeholder="e.g. vegetarian lunch spot, outdoor market, quiet garden", key=f"swap_text_{day_num}_{i}")
                    with c2:
                        st.write("")
                        st.write("")
                        if st.button("Swap slot", key=f"swap_{day_num}_{i}"):
                            new_name = request.strip() or "Local alternative to explore"
                            activity["name"] = new_name
                            activity["description"] = f"Customized suggestion: {new_name}. Check current opening hours, location, dietary options, and reviews before visiting."
                            activity["category"] = "Custom"
                            activity["cost"] = 0
                            trip["days"] = [dict(d) for d in trip["days"]]
                            st.session_state.current_trip = trip
                            st.success("Only this activity slot was updated.")
                            st.rerun()
        st.caption("Slot swaps are saved to this session's trip. For a real venue recommendation, verify the place and its current details before travelling.")

with tab4:
    trip = st.session_state.current_trip
    left, right = st.columns([1,1])
    with left:
        st.subheader("Your trip library")
        if not st.session_state.trips:
            st.info("Trips you create appear here for this session.")
        else:
            for i, saved in enumerate(st.session_state.trips):
                with st.container(border=True):
                    st.write(f"**{saved['destination']}**")
                    st.caption(f"{saved['start_date']} · {saved['duration']} days · {saved['budget']} budget")
                    if st.button("Open this trip", key=f"open_trip_{i}"):
                        st.session_state.current_trip = saved
                        st.rerun()
            st.caption("Persistence is simulated with Streamlit session state; trips are not stored permanently on a server.")
    with right:
        st.subheader("Take your guide offline")
        if not trip:
            st.info("Create or open a trip to export its PDF guide.")
        else:
            st.write(f"**{trip['destination']}** — {trip['duration']} days")
            st.write("Includes daily plans, time slots, cost estimates, and a practical emergency checklist.")
            try:
                pdf = generate_pdf(trip)
                st.download_button("📄 Download itinerary PDF", data=pdf, file_name=f"{trip['destination'].lower().replace(',','').replace(' ','_')}_itinerary.pdf", mime="application/pdf", type="primary", use_container_width=True)
            except Exception as e:
                st.error(f"Could not create the PDF: {e}")
            st.download_button("⬇️ Download trip JSON", data=json.dumps(trip, default=str, indent=2), file_name="trip_plan.json", mime="application/json", use_container_width=True)

st.divider()
st.markdown("<p class='small'>Made for curious travellers · Estimates are illustrative, not bookings. AI-generated venue details may be inaccurate; verify all logistics with official sources.</p>", unsafe_allow_html=True)
