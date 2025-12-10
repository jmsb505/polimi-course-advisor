import React, { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import type { GraphView } from "../types/chat";

interface GraphPanelProps {
    graphView: GraphView | null;
    selectedCourseCode?: string | null;
    onSelectCourse?: (code: string) => void;
}

export const GraphPanel: React.FC<GraphPanelProps> = ({
    graphView,
    selectedCourseCode,
    onSelectCourse,
}) => {
    const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    useEffect(() => {
        if (!containerRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                if (width > 0 && height > 0) {
                    setDimensions({ width, height });
                }
            }
        });

        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, [graphView]);

    // Force configuration effect
    useEffect(() => {
        if (fgRef.current) {
            // Apply strong repulsion
            fgRef.current.d3Force('charge')?.strength(-200);
            // Apply longer link distance
            fgRef.current.d3Force('link')?.distance(100);
            // Re-heat simulation
            fgRef.current.d3ReheatSimulation();
        }
    }, [graphView, dimensions]);

    const graphData = useMemo(() => {
        if (!graphView) {
            return { nodes: [], links: [] };
        }

        const scores = graphView.nodes.map((n) => n.score);
        const minScore = scores.length ? Math.min(...scores) : 0;
        const maxScore = scores.length ? Math.max(...scores) : 1;

        const scaleScore = (score: number) => {
            if (maxScore === minScore) return 3;
            const t = (score - minScore) / (maxScore - minScore);
            return 3 + t * 7;
        };

        const nodes = graphView.nodes.map((n) => {
            const isSelected = selectedCourseCode && n.code === selectedCourseCode;
            const color = isSelected
                ? "#f97316"
                : n.is_recommended
                    ? "#eab308"
                    : "#38bdf8";

            return {
                id: n.code,
                code: n.code,
                label: n.label,
                group: n.group,
                score: n.score,
                isRecommended: n.is_recommended,
                val: scaleScore(n.score),
                color,
            };
        });

        const links = graphView.edges.map((e) => ({
            source: e.source,
            target: e.target,
            weight: e.weight,
            concepts: e.concepts,
            reasons: e.reasons,
        }));

        return { nodes, links };
    }, [graphView, selectedCourseCode]);

    if (!graphView || graphData.nodes.length === 0) {
        return (
            <div className="panel-content empty-state" style={{ color: "#aaa", padding: "1rem" }}>
                The course graph will appear here once recommendations are available.
            </div>
        );
    }

    return (
        <div className="panel-content graph-panel-container" style={{
            position: "relative",
            flex: 1,
            minHeight: 0,
            width: "100%",
            overflow: "hidden",
            borderRadius: "0.5rem",
            backgroundColor: "rgba(17, 24, 39, 0.6)", // bg-gray-900/60
            border: "1px solid rgba(55, 65, 81, 1)", // border-gray-700
            display: "flex",
            flexDirection: "column"
        }}>
            <div style={{
                padding: "0.5rem 0.75rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderBottom: "1px solid rgba(55, 65, 81, 1)",
                background: "rgba(0,0,0,0.2)",
                zIndex: 10
            }}>
                <span style={{ fontWeight: 600, color: "#f3f4f6", fontSize: "0.85rem" }}>
                    Course Graph
                </span>
                <span style={{ fontSize: "0.7rem", color: "#9ca3af" }}>
                    Nodes: {graphData.nodes.length} · Edges: {graphData.links.length}
                </span>
            </div>

            <div
                ref={containerRef}
                style={{
                    flex: 1,
                    width: "100%",
                    position: "relative",
                    minHeight: 0
                }}
            >
                <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0 }}>
                    {dimensions.width > 0 && dimensions.height > 0 ? (
                        <ForceGraph2D
                            ref={fgRef}
                            width={dimensions.width}
                            height={dimensions.height}
                            graphData={graphData}
                            nodeId="id"
                            linkSource="source"
                            linkTarget="target"
                            nodeVal="val"
                            nodeLabel={(node: any) =>
                                `[${node.code}] ${node.label}`
                            }
                            linkLabel={(link: any) => {
                                const concepts = link.concepts || [];
                                const reasons = link.reasons || [];
                                const parts = [];
                                if (concepts.length > 0) parts.push(`Concepts: ${concepts.join(", ")}`);
                                if (reasons.length > 0) parts.push(`Reasons: ${reasons.join(", ")}`);
                                return parts.length > 0 ? parts.join("\n") : "Related";
                            }}
                            linkHoverPrecision={20}
                            nodeRelSize={8}
                            backgroundColor="rgba(0,0,0,0)" // transparent
                            linkColor={() => "rgba(148, 163, 184, 0.6)"}
                            linkWidth={(link: any) => 0.5 + (link.weight || 0) * 2}
                            linkDirectionalParticles={(link: any) =>
                                link.weight && link.weight > 0.3 ? 2 : 0
                            }
                            linkDirectionalParticleSpeed={0.01}
                            linkDirectionalParticleWidth={2}

                            // Basic physics props
                            d3AlphaDecay={0.02}
                            d3VelocityDecay={0.3}
                            cooldownTicks={100}

                            onEngineStop={() => {
                                if (fgRef.current) {
                                    fgRef.current.zoomToFit(400);
                                }
                            }}
                            onNodeClick={(node: any) => {
                                if (onSelectCourse) {
                                    onSelectCourse(node.code);
                                }
                            }}
                        />
                    ) : (
                        <div className="flex h-full w-full items-center justify-center text-xs text-gray-500">
                            Loading graph...
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
