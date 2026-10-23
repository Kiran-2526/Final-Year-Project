import numpy as np
from PIL import Image
import cv2
import logging

logger = logging.getLogger(__name__)

def validate_thermal_image(pil_img, model_result=None):
    """
    Conservative multi-signal thermal image validator.
    Determines if pil_img is a valid thermal paddy leaf image.
    
    Returns tuple: (is_valid: bool, status_code: str, message: str)
    Status codes:
    - VALID_IMAGE
    - INVALID_FILE
    - INVALID_IMAGE
    - OOD_UNKNOWN_IMAGE
    """
    if pil_img is None:
        return False, "INVALID_FILE", "The uploaded file could not be decoded as a valid image."

    try:
        w, h = pil_img.size
    except Exception:
        return False, "INVALID_FILE", "Failed to read image dimensions."

    # 1. Image Geometry & Dimensions
    if w < 50 or h < 50:
        return False, "INVALID_FILE", "Image dimensions are too small (minimum 50x50 pixels required)."

    aspect = max(w / h, h / w)
    if aspect > 5.0:
        return False, "INVALID_IMAGE", "Extreme aspect ratio detected (likely a web banner or document screenshot)."

    arr = np.array(pil_img.convert('RGB'))
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # 2. Digital UI / Code Screenshot Canvas Checks
    pure_white_pct = np.mean((r > 245) & (g > 245) & (b > 245)) * 100
    mean_r, mean_g, mean_b = np.mean(r), np.mean(g), np.mean(b)

    # Light Mode UI / Document Screenshot (large white canvas background)
    if pure_white_pct > 25.0:
        return False, "INVALID_IMAGE", f"The uploaded image contains an excessive white document/UI canvas ({pure_white_pct:.1f}%)."

    # Dark Mode Code Editor / Terminal Screenshot Check (R, G, B means all < 75.0)
    if mean_r < 75.0 and mean_g < 75.0 and mean_b < 75.0:
        return False, "INVALID_IMAGE", f"Dark code editor/terminal screenshot detected (Mean RGB: {mean_r:.1f}, {mean_g:.1f}, {mean_b:.1f})."

    # 3. Daylight Visible-Light RGB Plant Photo Check
    # Standard daylight RGB plant photos have green heavily dominating over red & blue
    daylight_green_pct = np.mean((g > r * 1.15) & (g > b * 1.15)) * 100
    if daylight_green_pct > 55.0:
        return False, "OOD_UNKNOWN_IMAGE", "Standard daylight visible-light foliage detected. Please upload a thermal image of a paddy leaf."

    # 4. Thermal Texture & High-Frequency Noise Checks
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var > 35000.0:
        return False, "OOD_UNKNOWN_IMAGE", "High-frequency artificial noise image detected."

    # 5. Out-Of-Distribution Softmax Model Uncertainty Check
    if model_result:
        probs = model_result.get("probabilities", [])
        confidence = model_result.get("confidence", 0.0)
        if probs:
            probs_arr = np.array(probs)
            entropy = -float(np.sum(probs_arr * np.log2(probs_arr + 1e-12)))

            # Conservative OOD check: only reject if prediction distribution is extremely flat/uncertain AND confidence < 38%
            if entropy > 2.20 and confidence < 0.38:
                return False, "OOD_UNKNOWN_IMAGE", f"Prediction distribution is out-of-distribution (Entropy: {entropy:.2f})."

    return True, "VALID_IMAGE", "Valid thermal paddy leaf image."
