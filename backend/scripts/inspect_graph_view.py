# backend/scripts/inspect_graph_view.py

import sys
import os
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).parent.parent.parent
sys.path.append(str(root))

from backend.app.deps import init_data, get_courses_raw, get_graph
from backend.core.models import Course
from backend.core.ranking import build_graph_view_for_recommendations

def main():
    print("Initializing data...")
    init_data()
    
    courses_raw = get_courses_raw()
    graph = get_graph()
    
    # Reconstruct Course objects
    courses = []
    for item in courses_raw:
        ssd_raw = item.get("ssd", []) or []
        ssd_list = [str(s).strip() for s in ssd_raw if s] if isinstance(ssd_raw, list) else [str(ssd_raw).strip()]
        courses.append(Course(
            code=item["code"],
            name=item["name"],
            cfu=item.get("cfu", 0.0),
            semester=item.get("semester", 1),
            language=item.get("language", "EN"),
            group=item.get("group", ""),
            ssd=ssd_list,
            description=item.get("description", ""),
            raw=item
        ))
    
    # Pick some "recommendations" (e.g., first 3)
    rec_codes = [c.code for c in courses[:3]]
    print(f"Recommended codes: {rec_codes}")
    
    # Generate graph view
    gv = build_graph_view_for_recommendations(
        recommended_codes=rec_codes,
        graph=graph,
        courses=courses,
        max_neighbors_per_node=3
    )
    
    print(f"\nGraph View Stats:")
    print(f"Nodes: {len(gv['nodes'])}")
    print(f"Edges: {len(gv['edges'])}")
    
    # Inspect first few edges
    print("\nSample Edges:")
    for edge in gv['edges'][:5]:
        print(f"Edge: {edge['source']} -> {edge['target']} (w={edge['weight']:.2f})")
        print(f"  Concepts: {edge['concepts']}")
        print(f"  Reasons: {edge['reasons']}")

if __name__ == "__main__":
    main()
