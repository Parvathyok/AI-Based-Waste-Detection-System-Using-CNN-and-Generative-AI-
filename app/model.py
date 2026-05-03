"""
model.py — EfficientNet-B2 Waste Classification Inference Engine
Uses timm (PyTorch Image Models) to load and run EfficientNet-B2
for 7-class waste classification, mirroring the detect-waste repo approach.
"""

import io
import os
import logging
import urllib.request

import torch
import torch.nn as nn
import timm
import numpy as np
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)

# ── Waste classes aligned with detect-waste dataset ──────────────────────────
WASTE_CLASSES = [
    "bio",           # Organic / biodegradable
    "glass",         # Glass bottles & jars
    "metals_plastics",  # Metals and plastics
    "non_recyclable",   # Non-recyclable waste
    "other",         # Miscellaneous
    "paper",         # Paper & cardboard
    "unknown",       # Unknown / unidentifiable
]

# Detailed metadata for each class used by GenAI and the UI
CLASS_META = {
    "bio": {
        "label": "Biological / Organic",
        "recyclable": True,
        "bin_color": "Green",
        "icon": "🌿",
    },
    "glass": {
        "label": "Glass",
        "recyclable": True,
        "bin_color": "Blue",
        "icon": "🫙",
    },
    "metals_plastics": {
        "label": "Metals & Plastics",
        "recyclable": True,
        "bin_color": "Yellow",
        "icon": "♻️",
    },
    "non_recyclable": {
        "label": "Non-Recyclable",
        "recyclable": False,
        "bin_color": "Black/Grey",
        "icon": "🗑️",
    },
    "other": {
        "label": "Other Waste",
        "recyclable": False,
        "bin_color": "Grey",
        "icon": "❓",
    },
    "paper": {
        "label": "Paper & Cardboard",
        "recyclable": True,
        "bin_color": "Blue",
        "icon": "📄",
    },
    "unknown": {
        "label": "Unknown",
        "recyclable": False,
        "bin_color": "Grey",
        "icon": "🔍",
    },
}

# ── Image preprocessing (ImageNet stats) ─────────────────────────────────────
TRANSFORM = transforms.Compose([
    transforms.Resize((260, 260)),
    transforms.CenterCrop(260),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

# ── Model URL (public EfficientNet-B2 weights fine-tuned on waste) ────────────
# Falls back to ImageNet pre-trained weights if custom weights not available
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "efficientnet_b2_waste.pth")


class WasteClassifier:
    """
    Wraps EfficientNet-B2 for single-image waste classification.
    Loads pre-trained weights; falls back to ImageNet weights if
    fine-tuned weights are unavailable (useful for demo/dev).
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Inference device: {self.device}")
        self.model = self._load_model()
        self.model.eval()

    def _load_model(self) -> nn.Module:
        """Build EfficientNet-B2 and load weights."""
        model = timm.create_model(
            "efficientnet_b2",
            pretrained=True,          # ImageNet pre-trained backbone
            num_classes=len(WASTE_CLASSES),
        )
        # Load fine-tuned weights if available
        if os.path.exists(MODEL_PATH):
            try:
                state = torch.load(MODEL_PATH, map_location=self.device)
                model.load_state_dict(state)
                logger.info("Loaded fine-tuned waste-classification weights.")
            except Exception as exc:
                logger.warning(f"Could not load custom weights: {exc}. Using ImageNet pre-trained.")
        else:
            logger.warning(
                "Fine-tuned weights not found at %s. "
                "Running with ImageNet pre-trained backbone (demo mode).",
                MODEL_PATH,
            )
        return model.to(self.device)

    @torch.no_grad()
    def predict(self, image: Image.Image) -> dict:
        """
        Classify a PIL image.

        Returns
        -------
        dict with keys:
            class_name   : str   — detected waste class key
            label        : str   — human-readable label
            confidence   : float — top-1 confidence (0-1)
            all_scores   : dict  — {class_name: confidence}
            meta         : dict  — recyclability, bin colour, icon
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        tensor = TRANSFORM(image).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs  = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        top_idx   = int(np.argmax(probs))
        class_key = WASTE_CLASSES[top_idx]

        all_scores = {WASTE_CLASSES[i]: float(probs[i]) for i in range(len(WASTE_CLASSES))}

        return {
            "class_name": class_key,
            "label":      CLASS_META[class_key]["label"],
            "confidence": float(probs[top_idx]),
            "all_scores": all_scores,
            "meta":       CLASS_META[class_key],
        }


# ── Module-level singleton (loaded once at import time) ───────────────────────
_classifier: WasteClassifier | None = None


def get_classifier() -> WasteClassifier:
    global _classifier
    if _classifier is None:
        _classifier = WasteClassifier()
    return _classifier
