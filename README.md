# 🌳 KnowledgeTree

An interactive web app that **automatically builds a personal knowledge tree** from your input concepts using the **Google Gemini** large-language model and renders it as a beautiful, explorable graph.

---

## Features

- **LLM-powered hierarchy discovery** — paste any concept (SLAM, Kalman Filter, Blender, Docker, …) and Gemini traces the full path from a root domain all the way down to your concept.
- **Cross-concept connection detection** — input multiple concepts and the AI finds shared parent nodes and inter-connections automatically.
- **Broad domain support** — works for technologies, software tools, skills, sciences, arts, and more.
- **Interactive graph** — pan, zoom, hover for descriptions, drag nodes to reorganise.
- **One-click examples** — try pre-built concept sets from the sidebar.

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/zzzzzbk/KnowledgeTree.git
cd KnowledgeTree
pip install -r requirements.txt
```

### 2. Get a Gemini API key

Visit <https://aistudio.google.com/app/apikey> and create a free key.

### 3. Run the app

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually <http://localhost:8501>).

### 4. Use it

1. Paste your Gemini API key in the sidebar.
2. Type one concept per line in the text area (e.g. `SLAM`, `Kalman Filter`, `A-star`).
3. Click **🌱 Build Tree**.
4. Explore the interactive knowledge graph!

---

## Node colour legend

| Colour | Meaning |
|--------|---------|
| 🔴 Coral | Your input concept |
| 🟦 Teal | Root domain (broadest, e.g. "Computer Science") |
| 🔵 Blue | Domain (e.g. "Robotics") |
| 🟢 Mint | Sub-domain (e.g. "State Estimation") |
| 🟡 Yellow | Intermediate concept node |

---

## Example inputs

| Input | Discovered tree |
|-------|----------------|
| `SLAM` | Computer Science → Robotics → State Estimation → SLAM |
| `SLAM`, `Kalman Filter`, `A-star` | Shared robotics/math parents with cross-links |
| `Blender`, `Substance Painter` | Computer Graphics → 3D Rendering → 3D Modelling → Blender/Substance Painter |
| `Neural Networks`, `Backpropagation`, `PyTorch` | AI → ML → Deep Learning sub-tree |

---

## Tech stack

| Component | Library |
|-----------|---------|
| UI | [Streamlit](https://streamlit.io/) |
| LLM | [Google Gemini](https://ai.google.dev/) via `google-genai` |
| Graph data | [networkx](https://networkx.org/) (future extensions) |
| Visualisation | [pyvis](https://pyvis.readthedocs.io/) |

---

## Project structure

```
KnowledgeTree/
├── app.py            # Streamlit application (UI + Gemini + graph rendering)
├── requirements.txt  # Python dependencies
└── README.md
```