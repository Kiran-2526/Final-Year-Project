import os
import torch
import torch.nn as nn
from PIL import Image
import numpy as np
import logging
from backend_python.config import Config
from ml.src.model import load_trained_model
from ml.src.preprocess import get_inference_transform, CLASS_MAPPING, CLASS_KEYS

logger = logging.getLogger(__name__)

from backend_python.services.image_validator import validate_thermal_image

class PyTorchInferenceService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = None
        self._load_model()

    def _load_model(self):
        model_path = Config.MODEL_PATH
        if not os.path.exists(model_path):
            logger.error(f"PyTorch model checkpoint not found at {model_path}")
            raise FileNotFoundError(f"Model checkpoint not found at {model_path}")

        logger.info(f"Loading PyTorch ResNet50 model from: {model_path} on device: {self.device}")
        try:
            self.model = load_trained_model(model_path, device=self.device)
            self.transform = get_inference_transform()
            logger.info("PyTorch ResNet50 model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {e}")
            raise e

    def predict(self, image_input):
        """
        Executes ResNet50 inference and OOD validation on image_input.
        Returns dict containing validImage, diseaseName, diseaseKey, confidence, status, message, etc.
        """
        if self.model is None or self.transform is None:
            self._load_model()

        try:
            if isinstance(image_input, Image.Image):
                pil_img = image_input
            else:
                pil_img = Image.open(image_input)
        except Exception as img_err:
            return {
                "validImage": False,
                "classIndex": None,
                "diseaseName": None,
                "diseaseKey": None,
                "confidence": None,
                "status": "INVALID_FILE",
                "message": "The uploaded file could not be decoded as a valid image.",
                "probabilities": []
            }

        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')

        # Apply exact PyTorch preprocessing pipeline
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        best_idx = int(np.argmax(probs))
        confidence = float(probs[best_idx])

        disease_name = CLASS_MAPPING.get(best_idx, "Unknown")
        disease_key = CLASS_KEYS.get(best_idx, "unknown")

        raw_result = {
            "classIndex": best_idx,
            "diseaseName": disease_name,
            "diseaseKey": disease_key,
            "confidence": confidence,
            "probabilities": probs.tolist()
        }

        # Run multi-signal OOD & visual validation
        is_valid, status_code, message = validate_thermal_image(pil_img, raw_result)

        if not is_valid:
            return {
                "validImage": False,
                "classIndex": None,
                "diseaseName": None,
                "diseaseKey": None,
                "confidence": None,
                "status": status_code,
                "message": message,
                "probabilities": probs.tolist()
            }

        if confidence >= 0.70:
            status = "HIGH_CONFIDENCE"
        elif confidence >= 0.45:
            status = "MODERATE_CONFIDENCE"
        else:
            status = "LOW_CONFIDENCE"

        return {
            "validImage": True,
            "classIndex": best_idx,
            "diseaseName": disease_name,
            "diseaseKey": disease_key,
            "confidence": confidence,
            "status": status,
            "message": "Valid thermal paddy leaf image.",
            "probabilities": probs.tolist()
        }

# Global singleton service instance
pytorch_inference_service = None

def get_inference_service():
    global pytorch_inference_service
    if pytorch_inference_service is None:
        pytorch_inference_service = PyTorchInferenceService()
    return pytorch_inference_service
