# Personalized Travel Itinerary Planner

A Streamlit capstone application for generating mood-aware, day-by-day travel plans with nearby-attraction grouping, activity cost estimates, activity swaps, session trip history, and offline PDF export.

## Features

- **Preference capture:** destination or open-ended vibe, dates, duration, budget, party, pace, and interests.
- **Destination recommender:** top three sample-city recommendations using mood, party, budget, and general seasonal fit.
- **Day-wise planner:** four sequential time slots per day and a nearest-neighbour geographic clustering heuristic to reduce backtracking.
- **Budget tracker:** activity estimates shown in destination-local currency and converted to a selected display currency using approximate fixed conversion rates.
- **Customization:** replace an individual activity slot or regenerate one day without replacing the rest of the plan.
- **Trip history:** session-based trip library (not permanent database persistence).
- **Offline export:** downloadable PDF guide with day-by-day tables and an emergency/practical checklist; trip JSON export.
- **Optional LLM:** Gemini or Groq key can be entered in the sidebar. The application falls back to its built-in demo planner if no key is supplied or an API call fails.

## Run locally

Python 3.9+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## AI mode

Open the sidebar, choose Gemini or Groq, and enter your API key in the password field. The key is used only for the current app session and is not written to files. For public deployments, prefer Streamlit Secrets rather than asking users to paste personal keys. Never commit API keys.

- Gemini uses the Generative Language API.
- Groq uses the OpenAI-compatible chat completions endpoint.
- If an API request fails or returns malformed JSON, the demo itinerary generator is used.

## Deploy to Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. Create a new app in Streamlit Community Cloud.
3. Select the repository, branch, and `app.py` as the entry point.
4. Deploy. No external database is required for the demo version.

## Notes and limitations

- Trip history uses Streamlit session state. It is not a permanent, multi-user database.
- The destination and attraction catalog is intentionally small and editable in `CITIES`.
- Route optimization is a straight-line nearest-neighbour heuristic over sample coordinates, not a live road-routing service.
- Prices, currency conversion, opening hours, weather, visa details, transit, and venue suggestions are estimates or general guidance. Verify them with official sources before travelling.
- AI output is not guaranteed to be factually correct. Check venue names, coordinates, and costs before relying on a plan.
- Project prompt specifies zero external database dependencies for one-click deployment; this version follows that constraint with session persistence.

## Project structure

```text
personalized_travel_itinerary_planner/
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```
