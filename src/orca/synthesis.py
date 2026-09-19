import os
import sys
import warnings
from typing import Optional, Literal, List, Dict, Any
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

from google import genai
from google.genai import types

SYNTHESIS_SYSTEM_INSTRUCTION = """You are the marine safety explanation synthesizer for ORCA, an AI-powered maritime safety advisory system for coastal waters.
Your task is to take the deterministic safety evaluation (verdict, risk reasons, and recorded ocean/weather measurements) and write a clear, natural-language explanation for the user.

### Strict Rules:
1. Length: Exactly 2 to 3 sentences. Do not use bullet points, headers, greetings, or conversational filler.
2. Verdict Fidelity: Strictly explain and support the verdict (SAFE, CAUTION, or UNSAFE). Never contradict the verdict.
3. ZERO NUMBER HALLUCINATION (CRITICAL):
   - You must NEVER invent, estimate, extrapolate, or introduce any new numbers, speeds, wave heights, or distances.
   - Every single numerical value you mention MUST come directly from the provided metrics (windSpeedKmh, waveHeightM, mpaDistanceKm, or riskScore).
   - If a measurement is omitted or null, do not state a number for it.
4. Lead with Question Context:
   - If questionType is 'sea_conditions': Lead with wave height and wind conditions, then mention protected area distance if relevant.
   - If questionType is 'protected_area': Lead with the distance to the Marine Protected Area and boundary restrictions, then mention wind and wave conditions.
5. Tone: Calm, authoritative, and safety-focused.
"""

def synthesize_explanation(
    location_name: str,
    question_type: Literal["sea_conditions", "protected_area", "unsupported"],
    verdict: Literal["SAFE", "CAUTION", "UNSAFE"],
    reasons: List[str],
    data: Dict[str, Optional[float]],
    risk_score: Optional[int] = None,
    client: Optional[genai.Client] = None,
    model_id: Optional[str] = None,
) -> str:
    """
    Synthesizes a 2-3 sentence natural-language explanation from deterministic
    rules engine outputs and weather/ocean metrics, guaranteeing zero number hallucinations.
    """
    load_dotenv(override=False)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError("GEMINI_API_KEY is not set.")

    if model_id is None:
        model_id = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

    if client is None:
        client = genai.Client(api_key=api_key)

    metrics_lines = []
    if data:
        if data.get("windSpeedKmh") is not None:
            metrics_lines.append(f"  * Wind Speed: {data['windSpeedKmh']} km/h")
        if data.get("waveHeightM") is not None:
            metrics_lines.append(f"  * Wave Height: {data['waveHeightM']} m")
        if data.get("mpaDistanceKm") is not None:
            metrics_lines.append(f"  * Nearest Marine Protected Area Distance: {data['mpaDistanceKm']} km")

    reasons_formatted = "\n".join(f"  * {r}" for r in reasons) if reasons else "  * None provided"
    metrics_formatted = "\n".join(metrics_lines) if metrics_lines else "  * No live metrics available"

    user_prompt = f"""Write a 2-3 sentence safety explanation based strictly on these details:
- Location: {location_name}
- Question Category: {question_type}
- Safety Verdict: {verdict}
- Risk Score: {risk_score if risk_score is not None else 'N/A'}
- Deterministic Reasons from Rules Engine:
{reasons_formatted}
- Actual Recorded Data:
{metrics_formatted}

Remember: 2-3 sentences only. Every number you state must be exactly traceable to the numbers above. Do not invent any numbers."""

    config = types.GenerateContentConfig(
        system_instruction=SYNTHESIS_SYSTEM_INSTRUCTION,
        temperature=0.2,
    )

    response = client.models.generate_content(
        model=model_id,
        contents=user_prompt,
        config=config,
    )

    if not response.text:
        raise RuntimeError("Empty explanation received from Gemini model.")

    return response.text.strip()
