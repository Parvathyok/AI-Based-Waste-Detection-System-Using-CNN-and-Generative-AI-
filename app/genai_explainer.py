"""
genai_explainer.py — Generative AI Explanation Layer
Uses Google Gemini Flash to generate contextual explanations,
disposal recommendations, and environmental impact text.

This is the CORE NOVELTY of WasteWise AI:
  R = g(ŷ, C)
  where ŷ = predicted class, C = context, R = rich explanation
"""

import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── System prompt: grounds the model in waste-management expertise ─────────────
SYSTEM_PROMPT = """You are WasteWise, an expert AI assistant specializing in 
environmental sustainability, waste management, and circular economy principles.
You help citizens understand how to properly dispose of waste to support 
UN Sustainable Development Goals 11, 12, and 13.

Your responses must always be:
- Concise yet informative
- Actionable (tell users exactly what to do)
- Positive and encouraging toward sustainability
- Structured in JSON format as specified
"""


class GenAIExplainer:
    """
    Wraps Google Gemini Flash API to generate explanations for
    detected waste items. Falls back to rule-based explanations
    if API key is not configured (demo/offline mode).
    """

    FALLBACK_EXPLANATIONS = {
        "bio": {
            "explanation": "This is organic/biodegradable waste such as food scraps, garden waste, or natural materials.",
            "disposal_method": "Place in the green composting bin or home compost heap. Avoid mixing with plastics.",
            "recyclability": "Compostable — converts into nutrient-rich compost for soil.",
            "environmental_impact": "Composting organic waste reduces methane emissions from landfills by up to 50%.",
            "reuse_tips": "Create a home compost bin to turn kitchen scraps into garden fertilizer.",
            "sdg_contribution": "Supports SDG 12 (Responsible Consumption) and SDG 13 (Climate Action) by reducing landfill methane.",
        },
        "glass": {
            "explanation": "Glass is a highly recyclable material made from sand, soda ash, and limestone.",
            "disposal_method": "Rinse clean and place in the glass recycling bin. Remove lids and caps.",
            "recyclability": "100% recyclable — glass can be recycled indefinitely without quality loss.",
            "environmental_impact": "Recycling glass saves 315 kg of CO₂ per tonne and reduces energy use by 30%.",
            "reuse_tips": "Reuse glass jars for food storage, home decor, or as drinking glasses.",
            "sdg_contribution": "Supports SDG 12 by enabling circular economy loops for glass materials.",
        },
        "metals_plastics": {
            "explanation": "This item is made from metal or plastic — both valuable recyclable materials.",
            "disposal_method": "Rinse thoroughly. Separate metals (crush cans) from plastics and place in the yellow recycling bin.",
            "recyclability": "Metals: 100% recyclable. Plastics: depends on type (check resin code 1-7).",
            "environmental_impact": "Recycling aluminium saves 95% of the energy needed to produce new aluminium from ore.",
            "reuse_tips": "Plastic bottles can be repurposed as planters, storage containers, or craft materials.",
            "sdg_contribution": "Supports SDG 11 (Sustainable Cities) through proper urban waste stream management.",
        },
        "non_recyclable": {
            "explanation": "This item cannot currently be recycled through standard household recycling programs.",
            "disposal_method": "Place in the general waste (black/grey) bin. Check local hazardous waste facilities for special items.",
            "recyclability": "Not recyclable through standard streams — check specialist recycling programs.",
            "environmental_impact": "Minimizing non-recyclable waste generation is critical to reducing landfill pressure.",
            "reuse_tips": "Consider if this item can be repaired, donated, or upcycled before disposal.",
            "sdg_contribution": "Awareness of non-recyclable waste drives SDG 12 conscious consumption behaviors.",
        },
        "other": {
            "explanation": "This item's waste category requires further assessment for proper disposal.",
            "disposal_method": "When in doubt, check your local municipal waste guidelines or contact your waste management provider.",
            "recyclability": "Unknown — consult local guidelines.",
            "environmental_impact": "Correct sorting prevents contamination of recyclable waste streams.",
            "reuse_tips": "Before disposal, explore if the item has reuse or donation potential.",
            "sdg_contribution": "Proper sorting of mixed waste supports SDG 11 sustainable city waste management.",
        },
        "paper": {
            "explanation": "Paper and cardboard are among the most widely recycled materials globally.",
            "disposal_method": "Flatten cardboard, keep paper dry and clean. Place in the blue paper recycling bin.",
            "recyclability": "Highly recyclable — paper can be recycled 5-7 times before fibres degrade.",
            "environmental_impact": "Recycling 1 tonne of paper saves 17 trees, 26,500 litres of water, and 4,000 kWh energy.",
            "reuse_tips": "Use both sides of paper before recycling. Repurpose newspaper as packaging material.",
            "sdg_contribution": "Supports SDG 15 (Life on Land) by reducing deforestation pressure from paper demand.",
        },
        "unknown": {
            "explanation": "The system could not confidently identify this waste item. Please try a clearer image.",
            "disposal_method": "When uncertain, consult your local waste collection authority or use a waste identification app.",
            "recyclability": "Unknown — professional assessment recommended.",
            "environmental_impact": "Correct waste identification is the first step toward responsible disposal.",
            "reuse_tips": "Take a clearer, well-lit photo for better identification.",
            "sdg_contribution": "AI-assisted waste identification supports all waste-related SDGs.",
        },
    }

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        self.use_gemini = bool(api_key and api_key != "your_gemini_api_key_here")
        if self.use_gemini:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info("Gemini Flash API configured successfully.")
        else:
            logger.warning("GEMINI_API_KEY not set. Using rule-based fallback explanations.")

    def explain(self, class_name: str, label: str, confidence: float) -> dict:
        """
        Generate a structured explanation for the detected waste class.

        Parameters
        ----------
        class_name  : str   — Internal class key (e.g. 'glass')
        label       : str   — Human-readable label (e.g. 'Glass')
        confidence  : float — Model confidence (0–1)

        Returns
        -------
        dict with explanation fields
        """
        if self.use_gemini:
            return self._gemini_explain(class_name, label, confidence)
        return self.FALLBACK_EXPLANATIONS.get(
            class_name, self.FALLBACK_EXPLANATIONS["unknown"]
        )

    def _gemini_explain(self, class_name: str, label: str, confidence: float) -> dict:
        """Call Gemini Flash to generate the explanation JSON."""
        prompt = f"""
A waste detection AI has classified an image as: **{label}** (confidence: {confidence:.1%}).
Internal class key: {class_name}

Generate a comprehensive waste disposal guide in the following JSON format ONLY 
(no markdown fences, pure JSON):

{{
  "explanation": "What this waste type is (1-2 sentences)",
  "disposal_method": "Exact step-by-step disposal instructions",
  "recyclability": "Whether and how it can be recycled",
  "environmental_impact": "Quantified environmental benefit of proper disposal",
  "reuse_tips": "Creative reuse/upcycling ideas before disposal",
  "sdg_contribution": "Which UN SDGs this proper disposal supports and how"
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Strip any accidental markdown fences
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            import json
            return json.loads(text)
        except Exception as exc:
            logger.error(f"Gemini API error: {exc}. Falling back to rule-based.")
            return self.FALLBACK_EXPLANATIONS.get(
                class_name, self.FALLBACK_EXPLANATIONS["unknown"]
            )


# ── Module-level singleton ────────────────────────────────────────────────────
_explainer: GenAIExplainer | None = None


def get_explainer() -> GenAIExplainer:
    global _explainer
    if _explainer is None:
        _explainer = GenAIExplainer()
    return _explainer
