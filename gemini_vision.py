"""
Gemini Vision helper for detecting 'Mark Attendance' presence in a page screenshot.
"""
import logging
from typing import Optional
import os

import google.generativeai as genai
from PIL import Image
import cv2
import numpy as np

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


def detect_attendance_local(image_path: str, template_path: str, threshold: float = 0.85) -> Optional[bool]:
    """
    Use OpenCV template matching to detect the reference button image inside a screenshot.
    Returns True if a match >= threshold is found, False if not, None on error.
    """
    try:
        if not template_path or not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return None

        img = cv2.imread(image_path)
        tpl = cv2.imread(template_path)
        if img is None or tpl is None:
            logger.error("Failed to read image or template for local detection")
            return None

        # Convert to grayscale for template matching
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        tpl_gray = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)

        # If template is larger than image, downscale template proportionally
        ih, iw = img_gray.shape
        th, tw = tpl_gray.shape
        if th > ih or tw > iw:
            scale = min(ih / th, iw / tw, 1.0)
            new_size = (max(1, int(tw * scale)), max(1, int(th * scale)))
            tpl_gray = cv2.resize(tpl_gray, new_size, interpolation=cv2.INTER_AREA)

        res = cv2.matchTemplate(img_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        logger.info(f"Local template match max val: {max_val:.3f}; threshold: {threshold:.2f}")
        return max_val >= threshold
    except Exception as e:
        logger.error(f"Local detection failed: {e}")
        return None
