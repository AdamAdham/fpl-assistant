# modules/graph_visualizer.py

import streamlit as st
from pyvis.network import Network
import tempfile
import os


def visualize_subgraph(context):
    nodes = context.get("nodes", [])
    rels = context.get("relationships", [])

    if not nodes:
        st.info("No graph data available.")
        return

    # Create PyVis graph
    net = Network(
        height="600px",
        width="100%",
        directed=True,
        bgcolor="#0e1117",      
        font_color="white"
    )


    net.barnes_hut(
        gravity=-20000,
        central_gravity=0.3,
        spring_length=150,
        spring_strength=0.01,
        damping=0.09
    )

  
    for n in nodes:
        label = n.get("label", "")
        nid = n["id"]

        if label == "Player":
            color = "#00c3ff"
            size = 25
        elif label == "Team":
            color = "#ffaa00"
            size = 20
        elif label == "Fixture":
            color = "#7fff00"
            size = 18
        else:
            color = "#cccccc"
            size = 15

        net.add_node(
            nid,
            label=str(nid),
            title=label,
            color=color,
            size=size
        )

    
    for r in rels:
        net.add_edge(
            r["start"],
            r["end"],
            label=r["type"],
            color="#ffffff",
            arrowStrikethrough=False
        )

    net.set_options("""
    const options = {
      "nodes": {
        "shadow": true,
        "shape": "dot"
      },
      "edges": {
        "smooth": true,
        "arrows": {
          "to": { "enabled": true }
        },
        "font": { "color": "white" }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -20000,
          "springLength": 150,
          "springConstant": 0.001
        },
        "stabilization": { "iterations": 250 }
      }
    }
    """)

    # Save graph to a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        html_path = tmp.name

    # Load HTML into Streamlit
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        st.components.v1.html(html, height=650, scrolling=True)

    os.remove(html_path)
