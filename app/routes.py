"""
routes.py — Flask REST API routes for WasteWise AI
Endpoints:
  GET  /           → Serve frontend
  POST /predict    → Image → classification + GenAI explanation
  GET  /health     → Health check (for Docker/K8s probes)
"""

import time
import logging
from flask import (
    Blueprint, request, jsonify, render_template, current_app
)
from app.model import get_classifier
from app.genai_explainer import get_explainer
from app.utils import allowed_file, load_image_from_bytes, format_confidence

logger = logging.getLogger(__name__)
bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Serve the WasteWise AI frontend."""
    return render_template("index.html")


@bp.route("/health")
def health():
    """Docker/K8s health probe endpoint."""
    return jsonify({"status": "healthy", "service": "wastewise-ai"}), 200


@bp.route("/predict", methods=["POST"])
def predict():
    """
    POST /predict
    Accepts:  multipart/form-data with field 'image'
    Returns:  JSON with classification + GenAI explanation

    Response schema:
    {
      "success": true,
      "class_name": "glass",
      "label": "Glass",
      "confidence": 0.923,
      "confidence_pct": "92.3%",
      "icon": "🫙",
      "recyclable": true,
      "bin_color": "Blue",
      "all_scores": { ... },
      "explanation": "...",
      "disposal_method": "...",
      "recyclability": "...",
      "environmental_impact": "...",
      "reuse_tips": "...",
      "sdg_contribution": "...",
      "processing_time_ms": 342
    }
    """
    start = time.time()

    # ── Validate request ──────────────────────────────────────────────────────
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image field in request."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename."}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Unsupported file type. Use PNG, JPG, WEBP."}), 400

    # ── Load image ────────────────────────────────────────────────────────────
    try:
        image_bytes = file.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            return jsonify({"success": False, "error": "Image too large (max 10 MB)."}), 413
        image = load_image_from_bytes(image_bytes)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 422

    # ── Run classification ────────────────────────────────────────────────────
    try:
        classifier = get_classifier()
        result = classifier.predict(image)
    except Exception as exc:
        logger.exception("Model inference failed")
        return jsonify({"success": False, "error": f"Model error: {exc}"}), 500

    # ── Generate GenAI explanation ────────────────────────────────────────────
    try:
        explainer = get_explainer()
        explanation = explainer.explain(
            class_name=result["class_name"],
            label=result["label"],
            confidence=result["confidence"],
        )
    except Exception as exc:
        logger.exception("GenAI explanation failed")
        explanation = {
            "explanation": "Explanation unavailable.",
            "disposal_method": "Please consult your local waste authority.",
            "recyclability": "Unknown",
            "environmental_impact": "Unknown",
            "reuse_tips": "Unknown",
            "sdg_contribution": "Unknown",
        }

    elapsed_ms = round((time.time() - start) * 1000)

    response = {
        "success": True,
        "class_name": result["class_name"],
        "label": result["label"],
        "confidence": result["confidence"],
        "confidence_pct": format_confidence(result["confidence"]),
        "icon": result["meta"]["icon"],
        "recyclable": result["meta"]["recyclable"],
        "bin_color": result["meta"]["bin_color"],
        "all_scores": result["all_scores"],
        "processing_time_ms": elapsed_ms,
        **explanation,
    }

    logger.info(
        "Prediction: %s (%.1f%%) in %dms",
        result["class_name"],
        result["confidence"] * 100,
        elapsed_ms,
    )
    return jsonify(response), 200
