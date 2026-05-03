# WasteWise AI 🌍♻️
> AI-Based Waste Detection System with Generative AI and Cloud Deployment

[![SDG 11](https://img.shields.io/badge/SDG-11%20Sustainable%20Cities-yellow)](https://sdgs.un.org/goals/goal11)
[![SDG 12](https://img.shields.io/badge/SDG-12%20Responsible%20Consumption-green)](https://sdgs.un.org/goals/goal12)
[![SDG 13](https://img.shields.io/badge/SDG-13%20Climate%20Action-blue)](https://sdgs.un.org/goals/goal13)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)](https://hub.docker.com)
[![Flask](https://img.shields.io/badge/Flask-REST%20API-lightgrey?logo=flask)](https://flask.palletsprojects.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)

---

## 🎯 Overview

WasteWise AI is an **end-to-end Hybrid AI system** that:

1. **Classifies** waste images into 7 categories using **EfficientNet-B2** (based on the [detect-waste](https://github.com/wimlds-trojmiasto/detect-waste) research project)
2. **Explains** the result using **Google Gemini GenAI** — generating disposal instructions, recyclability status, environmental impact, and SDG contributions
3. Serves results via a **Flask REST API** with a premium dark-mode web UI
4. Is fully **containerized with Docker** for cloud deployment

### Novelty Formula
```
R = g(ŷ, C)
```
Where `ŷ` = predicted waste class, `C` = context, `R` = rich AI-generated explanation

---

## 🗑️ Waste Categories

| Class | Label | Recyclable | Bin |
|-------|-------|-----------|-----|
| `bio` | Biological/Organic | ✅ | 🟢 Green |
| `glass` | Glass | ✅ | 🔵 Blue |
| `metals_plastics` | Metals & Plastics | ✅ | 🟡 Yellow |
| `non_recyclable` | Non-Recyclable | ❌ | ⚫ Black |
| `paper` | Paper & Cardboard | ✅ | 🔵 Blue |
| `other` | Other | ❌ | ⚫ Grey |
| `unknown` | Unknown | ❓ | ⚫ Grey |

---

## 🚀 Quick Start

### 1. Local Development (Python)
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/wastewise-ai.git
cd wastewise-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the app
python main.py
# Open: http://localhost:5000
```

### 2. Docker (Recommended)
```bash
# Build and run with Docker Compose
cp .env.example .env
# Edit .env: add GEMINI_API_KEY

docker-compose up --build -d

# Open: http://localhost:5000
```

### 3. DockerHub (Pre-built)
```bash
docker pull YOUR_DOCKERHUB_USERNAME/wastewise-ai:latest
docker run -p 5000:5000 -e GEMINI_API_KEY=your_key YOUR_DOCKERHUB_USERNAME/wastewise-ai:latest
```

---

## 🔌 REST API

### `POST /predict`
Upload a waste image for classification + GenAI explanation.

**Request:**
```
Content-Type: multipart/form-data
Field: image (file)
```

**Response:**
```json
{
  "success": true,
  "class_name": "glass",
  "label": "Glass",
  "confidence": 0.923,
  "confidence_pct": "92.3%",
  "icon": "🫙",
  "recyclable": true,
  "bin_color": "Blue",
  "explanation": "Glass is a highly recyclable material...",
  "disposal_method": "Rinse clean and place in blue bin...",
  "recyclability": "100% recyclable — glass can be recycled indefinitely...",
  "environmental_impact": "Recycling glass saves 315 kg of CO₂ per tonne...",
  "reuse_tips": "Reuse glass jars for food storage...",
  "sdg_contribution": "Supports SDG 12 by enabling circular economy...",
  "all_scores": { "glass": 0.923, "paper": 0.031, ... },
  "processing_time_ms": 342
}
```

### `GET /health`
Returns `{"status": "healthy"}` — used by Docker health checks.

---

## 🏗️ Architecture

```
User → Upload Image
         ↓
    Flask REST API  (/predict)
         ↓
  EfficientNet-B2  (7-class waste classification)
         ↓
  Gemini Flash GenAI  (contextual explanation + disposal guide)
         ↓
    JSON Response → Web UI
```

---

## 🐳 Build & Deploy

```bash
# Run the full deployment script
chmod +x setup.sh
./setup.sh YOUR_DOCKERHUB_USERNAME v1.0.0
```

This script:
- Commits and tags the code with git
- Builds the multi-stage Docker image
- Pushes to DockerHub (`:latest` + `:v1.0.0`)
- Pushes to GitHub with version tag

---

## 📁 Project Structure

```
wastewise-ai/
├── app/
│   ├── model.py           # EfficientNet-B2 inference engine
│   ├── genai_explainer.py # Gemini GenAI explanation layer
│   ├── routes.py          # Flask REST API routes
│   └── utils.py           # Image utilities
├── templates/index.html   # Premium dark-mode web UI
├── static/
│   ├── css/style.css      # Glassmorphism UI styles
│   └── js/app.js          # Frontend logic
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.yml     # Local orchestration
├── setup.sh               # Build + push automation
├── requirements.txt
└── main.py                # Application entry point
```

---

## 🌍 SDG Alignment

| Goal | How |
|------|-----|
| **SDG 11** Sustainable Cities | Promotes urban waste sorting and smart waste management |
| **SDG 12** Responsible Consumption | Educates users on recyclability and circular economy |
| **SDG 13** Climate Action | Quantifies CO₂ savings from proper waste disposal |

---

## 📚 References

- Original detect-waste repo: https://github.com/wimlds-trojmiasto/detect-waste
- EfficientNet-B2: Tan & Le, 2019 — EfficientNet: Rethinking Model Scaling
- Google Gemini: https://deepmind.google/technologies/gemini/
- UN SDGs: https://sdgs.un.org/goals

---

## 📝 License
MIT License — see [LICENSE](LICENSE)
