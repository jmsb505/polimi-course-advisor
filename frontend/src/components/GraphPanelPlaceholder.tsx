import React from "react";
import type { GraphView } from "../types/chat";

interface GraphPanelPlaceholderProps {
    graphView: GraphView | null;
}

export const GraphPanelPlaceholder: React.FC<GraphPanelPlaceholderProps> = ({ graphView }) => {
    if (!graphView || graphView.nodes.length === 0) {
        return (
            <div className="panel-content empty-state" style={{ color: "#aaa", padding: "1rem" }}>
                <p>The graph will appear here once recommendations are available.</p>
            </div>
        );
    }

    return (
        <div className="panel-content" style={{ padding: "1rem" }}>
            <div style={{ marginBottom: "0.5rem", fontWeight: "bold", color: "#ddd" }}>
                Graph Preview (Placeholder)
            </div>
            <div style={{ fontSize: "0.9rem", color: "#bbb" }}>
                <p><strong>Nodes:</strong> {graphView.nodes.length}</p>
                <p><strong>Edges:</strong> {graphView.edges.length}</p>
                <p style={{ marginTop: "0.5rem", fontStyle: "italic" }}>
                    Full interactive visualization coming in the next step.
                </p>
            </div>
        </div>
    );
};
