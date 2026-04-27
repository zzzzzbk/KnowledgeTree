"""
Knowledge Tree - LLM-powered knowledge graph visualization using Google Gemini.
"""

import json
import re

import streamlit as st
import google.genai as genai
import streamlit.components.v1 as components
from pyvis.network import Network

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NODE_COLORS = {
    "root": "#4ECDC4",       # teal – broadest domain (e.g. "Computer Science")
    "domain": "#45B7D1",     # blue – major field (e.g. "Robotics")
    "subdomain": "#96CEB4",  # mint – sub-field (e.g. "State Estimation")
    "concept": "#FFEAA7",    # yellow – specific concept
    "input": "#FF6B6B",      # coral – user-provided concept
}

NODE_SIZES = {
    "root": 35,
    "domain": 28,
    "subdomain": 22,
    "concept": 18,
    "input": 30,
}

GRAPH_HEIGHT = 650  # px

PROMPT_TEMPLATE = """\
You are a knowledge graph expert. Analyse the following technical concepts and \
build a comprehensive hierarchical knowledge tree.

Concepts to analyse: {concepts}

Instructions:
1. For every concept, trace a path from a broad root domain all the way down to \
the concept itself (root -> domain -> subdomain -> ... -> concept).
2. Assign type "input" to nodes that exactly match one of the given concepts.
3. Assign type "root"      for the broadest categories (e.g. "Computer Science", \
"Engineering", "Design", "Mathematics").
4. Assign type "domain"    for major fields within a root (e.g. "Robotics", \
"Machine Learning", "3D Rendering").
5. Assign type "subdomain" for more specific areas (e.g. "State Estimation", \
"Path Planning", "3D Modeling").
6. Assign type "concept"   for specific concepts that are NOT themselves input \
nodes but sit between input nodes and their parents.
7. Re-use the same node when multiple input concepts share a parent \
(e.g. SLAM and Kalman Filter both fall under "State Estimation").
8. Node IDs must be lowercase with underscores (e.g. "computer_science").
9. Edges point FROM parent TO child.
10. Support any domain: technology, software tools (e.g. Blender -> 3D Modelling \
-> 3D Rendering -> Computer Graphics), skills, sciences, arts, etc.

Return ONLY a valid JSON object — no markdown, no code fences, nothing else — \
using exactly this schema:
{{
  "nodes": [
    {{
      "id": "<snake_case_id>",
      "label": "<Display Name>",
      "type": "root|domain|subdomain|concept|input",
      "description": "<one-sentence description>"
    }}
  ],
  "edges": [
    {{
      "from": "<parent_id>",
      "to": "<child_id>",
      "label": ""
    }}
  ]
}}
"""


# ---------------------------------------------------------------------------
# Gemini helpers
# ---------------------------------------------------------------------------


def call_gemini(api_key: str, concepts: list[str]) -> dict:
    """Call Google Gemini and return the parsed knowledge-graph JSON."""
    client = genai.Client(api_key=api_key)

    prompt = PROMPT_TEMPLATE.format(concepts=", ".join(concepts))
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    raw = response.text.strip()

    # Strip optional markdown code fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_pyvis_network(graph_data: dict) -> Network:
    """Convert the LLM JSON into a styled, directed pyvis Network."""
    net = Network(
        height=f"{GRAPH_HEIGHT}px",
        width="100%",
        directed=True,
        bgcolor="#1a1a2e",
        font_color="#ffffff",
    )

    # Physics: hierarchical repulsion gives a nice tree layout
    net.set_options(
        """
        {
          "layout": {
            "hierarchical": {
              "enabled": false
            }
          },
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 150,
              "springConstant": 0.04
            },
            "stabilization": {
              "iterations": 200
            }
          },
          "edges": {
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.7 } },
            "color": { "color": "#888888", "highlight": "#ffffff" },
            "smooth": { "type": "dynamic" }
          },
          "nodes": {
            "font": { "size": 13 },
            "borderWidth": 2,
            "shadow": { "enabled": true }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """
    )

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # Index nodes by id for quick lookup
    node_index = {n["id"]: n for n in nodes}

    for node in nodes:
        node_id = node["id"]
        label = node.get("label", node_id)
        ntype = node.get("type", "concept")
        desc = node.get("description", "")

        color = NODE_COLORS.get(ntype, NODE_COLORS["concept"])
        size = NODE_SIZES.get(ntype, 18)

        net.add_node(
            node_id,
            label=label,
            title=f"<b>{label}</b><br>{desc}<br><i>Type: {ntype}</i>",
            color=color,
            size=size,
            borderWidth=3 if ntype == "input" else 2,
            borderWidthSelected=5,
        )

    for edge in edges:
        src = edge.get("from", "")
        dst = edge.get("to", "")
        elabel = edge.get("label", "")
        if src in node_index and dst in node_index:
            net.add_edge(src, dst, title=elabel, label=elabel)

    return net


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------


def render_legend():
    st.markdown(
        """
        <style>
        .legend-item {
            display: inline-flex; align-items: center;
            margin-right: 18px; font-size: 0.85rem;
        }
        .legend-dot {
            width: 14px; height: 14px; border-radius: 50%;
            display: inline-block; margin-right: 6px;
        }
        </style>
        <div style="margin-bottom:10px">
        <span class="legend-item"><span class="legend-dot" style="background:#FF6B6B"></span>Your concept</span>
        <span class="legend-item"><span class="legend-dot" style="background:#4ECDC4"></span>Root domain</span>
        <span class="legend-item"><span class="legend-dot" style="background:#45B7D1"></span>Domain</span>
        <span class="legend-item"><span class="legend-dot" style="background:#96CEB4"></span>Sub-domain</span>
        <span class="legend-item"><span class="legend-dot" style="background:#FFEAA7"></span>Concept</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="🌳 Knowledge Tree",
        page_icon="🌳",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🌳 Knowledge Tree")
        st.markdown(
            "Automatically build a personal knowledge graph from your concepts "
            "using **Google Gemini**."
        )
        st.divider()

        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help=(
                "Get a free key at https://aistudio.google.com/app/apikey. "
                "The key is only used client-side and never stored."
            ),
        )

        st.divider()
        st.markdown("### Examples")
        examples = {
            "Robotics concepts": "SLAM\nKalman Filter\nA-star",
            "3D & Design": "Blender\nSubstance Painter\nUnreal Engine",
            "ML stack": "Neural Networks\nBackpropagation\nPyTorch",
            "Mixed bag": "SLAM\nTransformers\nBlender\nDocker",
        }
        for name, value in examples.items():
            if st.button(name, use_container_width=True):
                st.session_state["concepts_input"] = value

        st.divider()
        st.caption("Powered by [Google Gemini](https://ai.google.dev/) · Built with Streamlit & pyvis")

    # ── Main area ─────────────────────────────────────────────────────────────
    st.markdown("## Enter your knowledge concepts")
    st.markdown(
        "Type one concept per line. The AI will discover their parent domains, "
        "shared connections, and build an interactive knowledge tree."
    )

    concepts_input = st.text_area(
        "Concepts (one per line)",
        value=st.session_state.get("concepts_input", ""),
        height=150,
        placeholder="SLAM\nKalman Filter\nA-star",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run = st.button("🌱 Build Tree", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear", use_container_width=False):
            st.session_state.pop("concepts_input", None)
            st.session_state.pop("graph_data", None)
            st.rerun()

    # ── Handle build ──────────────────────────────────────────────────────────
    if run:
        if not api_key:
            st.error("⚠️  Please enter your Gemini API key in the sidebar.")
        elif not concepts_input.strip():
            st.warning("Please enter at least one concept.")
        else:
            concepts = [
                c.strip()
                for c in concepts_input.strip().splitlines()
                if c.strip()
            ]
            with st.spinner(f"Asking Gemini to analyse {len(concepts)} concept(s)…"):
                try:
                    graph_data = call_gemini(api_key, concepts)
                    st.session_state["graph_data"] = graph_data
                    st.session_state["concepts_input"] = concepts_input
                except json.JSONDecodeError as exc:
                    st.error(f"Could not parse Gemini response as JSON: {exc}")
                    st.stop()
                except Exception as exc:
                    st.error(f"Gemini API error: {exc}")
                    st.stop()

    # ── Render graph ──────────────────────────────────────────────────────────
    if "graph_data" in st.session_state:
        graph_data = st.session_state["graph_data"]
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        if not nodes:
            st.warning("Gemini returned an empty graph. Try different concepts.")
        else:
            st.divider()
            st.markdown(
                f"### Knowledge Tree  "
                f"<small style='color:grey'>{len(nodes)} nodes · {len(edges)} edges</small>",
                unsafe_allow_html=True,
            )
            render_legend()

            net = build_pyvis_network(graph_data)
            html_content = net.generate_html()

            # Render in an iframe-style component
            components.html(html_content, height=GRAPH_HEIGHT + 20, scrolling=False)

            # ── Node detail table ─────────────────────────────────────────
            st.divider()
            st.markdown("### Concept Details")
            input_nodes = [n for n in nodes if n.get("type") == "input"]
            other_nodes = [n for n in nodes if n.get("type") != "input"]

            if input_nodes:
                st.markdown("**Your concepts**")
                for n in input_nodes:
                    with st.expander(f"🔴 {n['label']}"):
                        st.write(n.get("description", "No description available."))

            if other_nodes:
                st.markdown("**Discovered nodes**")
                for n in sorted(other_nodes, key=lambda x: x.get("type", "")):
                    type_emoji = {
                        "root": "🌐",
                        "domain": "📂",
                        "subdomain": "📁",
                        "concept": "💡",
                    }.get(n.get("type", ""), "•")
                    with st.expander(f"{type_emoji} {n['label']}  — *{n.get('type', '')}*"):
                        st.write(n.get("description", "No description available."))


if __name__ == "__main__":
    main()
