# ORCA Marine — Frontend Guide (Next.js)

Welcome, **Teammate A (Frontend Engineer)**! 👋

This directory is the dedicated home for the **ORCA Marine Frontend**.  
You can initialize or drop your Next.js / React application directly in this folder.

---

## 1. Quick Integration Points

- **Backend API Base URL**:
  - Local Development: `http://localhost:8000`
  - Cloud Production: (Set via `NEXT_PUBLIC_API_URL` environment variable)
- **Shared API Contract**: See [`../CONTRACT.md`](../CONTRACT.md) for the exact TypeScript types, request payloads, and response JSON formats.
- **5-Minute Presentation Script**: See [`../DEMO_SCRIPT.md`](../DEMO_SCRIPT.md) for presentation timing, rehearsed queries, and live speaking cues.

---

## 2. API Endpoint Specification

### `POST /ask`
Submit user natural-language questions to the AI Reasoning layer:

```typescript
// Request Body
interface AskRequest {
  question: string;                 // e.g. "Is it safe to take a small boat out near Mangaluru today?"
  demo_mode?: boolean;              // Optional: set to true for instant offline fixtures (Mangaluru/Goa/Mumbai)
  simulate_broken_sources?: string[]; // Optional fault injection: e.g. ["wave", "mpa"]
}

// Response Body
interface AskResponse {
  status: "ok" | "unsupported" | "missing_location" | "error";
  questionType?: "sea_conditions" | "protected_area" | "unsupported";
  location?: {
    name: string;
    lat: number;
    lon: number;
  };
  verdict?: "SAFE" | "CAUTION" | "UNSAFE";
  riskScore?: number;               // 0 to 100
  reasons: string[];
  data?: {
    windSpeedKmh?: number | null;
    waveHeightM?: number | null;
    mpaDistanceKm?: number | null;
  };
  explanation: string;              // Synthesized advisory (zero hallucinated numbers)
  sources: Array<{ name: string; url: string }>;
}
```

---

## 3. Staged Loading UI (CONTRACT.md Section 8)

While the AI pipeline processes the query (typically 1.5s – 3.0s), please display dynamic progress messages to the user:

1. **Phase 1 (0.0s – 0.8s)**:  
   *`"Analyzing question and identifying coastal sector..."`*
2. **Phase 2 (0.8s – 1.6s)**:  
   *`"Retrieving live weather, wave, and sanctuary boundaries..."`*
3. **Phase 3 (1.6s+)**:  
   *`"Synthesizing maritime safety advisory..."`*

---

## 4. Deploying to Vercel

When deploying to Vercel:
1. Connect the GitHub repository.
2. In **Project Settings** $\rightarrow$ **General**, set **Root Directory** to `frontend`.
3. Under **Environment Variables**, configure:
   ```env
   NEXT_PUBLIC_API_URL=https://<YOUR_DEPLOYED_BACKEND_URL>
   ```
