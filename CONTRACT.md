# ORCA API & Data Contract

## 1. Status and Rules

**Status: PROPOSAL, pending confirmation from teammate A (frontend) and teammate B (backend). Any change to this file must be announced to the whole team immediately.**

### Change Log

| Date | Change | Who |
| :--- | :--- | :--- |
| 2026-09-19 | Initial contract proposal drafted covering question types, planner output, and POST /ask schemas | Person C (AI Reasoning) |

---

## 2. Supported Question Types

| Question Type | Description | Example Query |
| :--- | :--- | :--- |
| `sea_conditions` | Wind speed and wave height conditions | "Is it safe to take a small boat out near Mangaluru today?" |
| `protected_area` | Distance to a Marine Protected Area (MPA) boundary | "Can I fish near Goa without entering a protected zone?" |
| `unsupported` | Anything outside marine safety or unsupported queries (refusal path, not a third supported type) | "What is the capital of France?" |

### Processing Rules
- The deterministic rules engine always computes one verdict from all three values (`windSpeedKmh`, `waveHeightM`, and `mpaDistanceKm`) for both supported types.
- `questionType` only changes which reasons the synthesis explanation leads with (e.g., wind/wave conditions first for `sea_conditions`, MPA proximity first for `protected_area`).
- Only current conditions (`now`/`today`) are supported. Historical queries and multi-day forecasts are treated as `unsupported`.

---

## 3. Planner Output

The planner LLM extracts the target location and question type from the user's raw query.

### Schema
- `location` (`string | null`): `null` if the question names no place; otherwise verbatim place name as written by the user (not coordinates).
- `questionType` (`"sea_conditions" | "protected_area" | "unsupported"`): Category of query.

```json
{
  "location": "Mangaluru",
  "questionType": "sea_conditions"
}
```

---

## 4. POST /ask Request

Endpoint: `POST /ask`

```json
{
  "question": "Is it safe to take a small boat out near Mangaluru today?"
}
```

---

## 5. POST /ask Response

### Field Specification

| Field | Type | Nullable | Units | Produced By |
| :--- | :--- | :--- | :--- | :--- |
| `status` | string (`"ok"` \| `"unsupported"` \| `"missing_location"` \| `"error"`) | No | None | Teammate B Backend |
| `questionType` | string (`"sea_conditions"` \| `"protected_area"` \| `"unsupported"`) | Yes | None | Planner (AI) |
| `location` | object (`{ "name": string, "lat": number, "lon": number }`) | Yes | None | Teammate B Backend |
| `verdict` | string (`"SAFE"` \| `"CAUTION"` \| `"UNSAFE"`) | Yes | None | Teammate B Backend (Rules Engine) |
| `riskScore` | number (`0 - 100`) | Yes | None | Teammate B Backend (Rules Engine) |
| `reasons` | array of strings | No | None | Teammate B Backend (Rules Engine) |
| `data` | object (`{ "windSpeedKmh", "waveHeightM", "mpaDistanceKm" }`) | Yes | None | Teammate B Backend |
| `data.windSpeedKmh` | number | Yes | km/h | Teammate B Backend (Open-Meteo) |
| `data.waveHeightM` | number | Yes | m | Teammate B Backend (Open-Meteo) |
| `data.mpaDistanceKm` | number | Yes | km | Teammate B Backend (MPA Boundary) |
| `explanation` | string | No | None | Synthesis LLM Call |
| `sources` | array of objects (`{ "name": string, "url": string }`) | No | None | Teammate B Backend |

### Producers Summary
- **Planner (AI)**: `questionType`
- **Teammate B (Backend)**: `location` coordinates, `verdict`, `riskScore`, `reasons`, `data`, `sources` (only sources successfully fetched for this request)
- **Synthesis LLM Call**: `explanation`

### Behaviour by Status
- `ok`: All fields filled with valid values.
- `unsupported`: `verdict`, `riskScore`, and `data` are `null`; `reasons` and `sources` are empty arrays (`[]`); `explanation` provides a fixed polite redirect.
- `missing_location`: `location`, `verdict`, `riskScore`, and `data` are `null`; `reasons` and `sources` are empty arrays (`[]`); `explanation` asks the user to specify a coastal city.
- `error`: `location`, `verdict`, `riskScore`, and `data` are `null`; `reasons` and `sources` are empty arrays (`[]`); `explanation` provides a short apology.

---

## 6. Examples

*Note: All numerical values and distances in the following examples are illustrative only.*

### Example 1: `status = "ok"` (`sea_conditions`)

```json
{
  "status": "ok",
  "questionType": "sea_conditions",
  "location": {
    "name": "Mangaluru",
    "lat": 12.87,
    "lon": 74.88
  },
  "verdict": "SAFE",
  "riskScore": 18,
  "reasons": [
    "Wind speed is calm at 14.2 km/h.",
    "Wave height is low at 0.8 m.",
    "Distance to nearest Marine Protected Area is 18.5 km."
  ],
  "data": {
    "windSpeedKmh": 14.2,
    "waveHeightM": 0.8,
    "mpaDistanceKm": 18.5
  },
  "explanation": "Current sea conditions off Mangaluru are calm with gentle winds of 14.2 km/h and wave heights of 0.8 m. You are well clear of protected boundaries at 18.5 km, making it safe for small boat operations.",
  "sources": [
    {
      "name": "Open-Meteo Marine API",
      "url": "https://open-meteo.com/en/docs/marine-weather-api"
    },
    {
      "name": "Protected Planet Marine Dataset",
      "url": "https://www.protectedplanet.net/en/thematic-areas/marine-protected-areas"
    }
  ]
}
```

### Example 2: `status = "ok"` (`protected_area`)

```json
{
  "status": "ok",
  "questionType": "protected_area",
  "location": {
    "name": "Goa",
    "lat": 15.49,
    "lon": 73.82
  },
  "verdict": "CAUTION",
  "riskScore": 55,
  "reasons": [
    "Within 2.1 km of Netravali Marine Sanctuary boundary.",
    "Wind speed is moderate at 22.0 km/h.",
    "Wave height is moderate at 1.4 m."
  ],
  "data": {
    "windSpeedKmh": 22.0,
    "waveHeightM": 1.4,
    "mpaDistanceKm": 2.1
  },
  "explanation": "Caution is advised near Goa as your target area is only 2.1 km from protected marine zone boundaries where fishing restrictions apply. While winds are 22.0 km/h and waves 1.4 m, ensure you do not cross into sanctuary limits.",
  "sources": [
    {
      "name": "Open-Meteo Marine API",
      "url": "https://open-meteo.com/en/docs/marine-weather-api"
    },
    {
      "name": "Protected Planet Marine Dataset",
      "url": "https://www.protectedplanet.net/en/thematic-areas/marine-protected-areas"
    }
  ]
}
```

### Example 3: `status = "unsupported"`

```json
{
  "status": "unsupported",
  "questionType": "unsupported",
  "location": null,
  "verdict": null,
  "riskScore": null,
  "reasons": [],
  "data": null,
  "explanation": "I can only answer marine safety questions regarding current wind, wave conditions, and Marine Protected Areas for coastal cities. Please ask a question related to coastal marine safety.",
  "sources": []
}
```

### Example 4: `status = "missing_location"`

```json
{
  "status": "missing_location",
  "questionType": "sea_conditions",
  "location": null,
  "verdict": null,
  "riskScore": null,
  "reasons": [],
  "data": null,
  "explanation": "Please specify a coastal city or region (such as Mangaluru, Goa, or Mumbai) so I can retrieve live weather and marine boundary data for you.",
  "sources": []
}
```

---

## 7. Open Items for the Team

- **(a) Emergency Message Wording & Helpline**: Agree on standard wording and national marine emergency contact numbers (e.g., Indian Coast Guard emergency toll-free number 1554) to be displayed on risk cards.
- **(b) City-Name-to-Coordinates Mapping**: Teammate B to establish and document the supported coastal cities list and coordinate resolution mechanism.
- **(c) Open-Meteo Units**: Teammate B to confirm default API units (wind speed in `km/h`, wave height in `m`).

---

## 8. Frontend Loading Copy & Latency Recommendations

*(Reference for Teammate A — Next.js Frontend)*

Live requests execute two sequential LLM calls (Planner + Synthesis) alongside oceanographic API fetches, taking an average of **1.5 – 3.0 seconds**. To maintain an interactive and responsive user experience, the frontend should display a dynamic multi-stage loading indicator rather than a static spinner.

### Recommended Staged Loading Copy:
- **Phase 1 (0.0s – 0.8s)**: `"Analyzing inquiry and detecting coastal location..."`
- **Phase 2 (0.8s – 1.6s)**: `"Retrieving live weather, wave, and sanctuary boundaries..."`
- **Phase 3 (1.6s+)**: `"Synthesizing verified maritime safety advisory..."`

### DEMO_MODE:
When `DEMO_MODE=true` is enabled, responses are returned from pre-compiled local fixtures in **< 20 ms** (near-instantaneous), requiring no staged progress indicators.
