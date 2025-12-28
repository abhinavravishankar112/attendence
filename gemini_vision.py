"""
Gemini Vision helper for detecting 'Mark Attendance' presence in a page screenshot.
"""
import logging
from typing import Optional

import google.generativeai as genai
from PIL import Image

logger = logging.getLogger(__name__)


def _init_model(api_key: str, model_name: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def detect_attendance_in_image(image_path: str, api_key: str, model_name: str = "gemini-1.5-flash") -> Optional[bool]:
    """
    Return True if Gemini sees a visible 'Mark Attendance' button or clear
    attendance-live indicator in the given screenshot; False if not found; None on error.
    """
    try:
        if not api_key:
            logger.error("GEMINI_API_KEY is missing. Set it in environment.")
            return None

        model = _init_model(api_key, model_name)

        img = Image.open(image_path)
        prompt = (
            "You are analyzing a screenshot of a web page. "
            "Answer ONLY 'YES' or 'NO'. "
            "Respond 'YES' if you clearly see a button, link, or call-to-action that says 'Mark Attendance', "
            "or text indicating attendance is live (e.g., 'Attendance is live', a countdown timer for attendance, etc.). "
            "Otherwise respond 'NO'."
        )

        resp = model.generate_content([prompt, img])
        text = (resp.text or "").strip().upper()
        logger.info(f"Gemini vision response: {text}")

        if "YES" in text and "NO" not in text:
            return True
        if "NO" in text and "YES" not in text:
            return False

        # Fallback: simple heuristic if the model replies with additional wording
        if text.startswith("YES"):
            return True
        if text.startswith("NO"):
            return False

        logger.warning("Unexpected Gemini response; cannot determine reliably.")
        return None
    except Exception as e:
        logger.error(f"Gemini vision detection failed: {e}")
        return None
