import React, { useEffect, useRef, useState } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import type { GraphView } from "../types/chat";

interface GraphPanelProps {
    graphView: GraphView | null;
    selectedCourseCode?: string | null;
    onSelectCourse?: (code: string) => void;
}

interface ExtendedGraphNode {
    id: string;
    x?: number;
    y?: number;
    code: string;
    label: string;
    group: string | null;
    score: number;
    isRecommended: boolean;
    val: number;
    color: string;
}

interface ExtendedGraphLink {
    source: string | ExtendedGraphNode;
    target: string | ExtendedGraphNode;
    weight: number;
    concepts: string[];
    reasons: { type: string; value: string; contribution: number }[];
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

    const [graphData, setGraphData] = useState<{ nodes: ExtendedGraphNode[]; links: ExtendedGraphLink[] }>({
        nodes: [],
        links: []
    });
    const [prevViewProps, setPrevViewProps] = useState<{ view: GraphView | null; selected: string | null | undefined }>({
        view: null,
        selected: undefined
    });

    // Official React pattern for derived state that needs to preserve previous values
    if (graphView !== prevViewProps.view || selectedCourseCode !== prevViewProps.selected) {
        setPrevViewProps({ view: graphView, selected: selectedCourseCode });

        if (!graphView) {
            setGraphData({ nodes: [], links: [] });
        } else {
            const scores = graphView.nodes.map((n) => n.score);
            const minScore = scores.length ? Math.min(...scores) : 0;
            const maxScore = scores.length ? Math.max(...scores) : 1;

            const scaleScore = (score: number) => {
                if (maxScore === minScore) return 3;
                const t = (score - minScore) / (maxScore - minScore);
                return 3 + t * 7;
            };

            const oldNodesMap = new Map(graphData.nodes.map(n => [n.id, n]));

            const nodes: ExtendedGraphNode[] = graphView.nodes.map((n) => {
                const isSelected = selectedCourseCode && n.code === selectedCourseCode;
                const color = isSelected
                    ? "#f97316"
                    : n.is_recommended
                        ? "#eab308"
                        : "#38bdf8";

                const existingNode = oldNodesMap.get(n.code);
                return {
                    ...(existingNode || {}),
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

            const links: ExtendedGraphLink[] = graphView.edges.map((e) => ({
                source: e.source,
                target: e.target,
                weight: e.weight,
                concepts: e.concepts,
                reasons: e.reasons.map(r => ({
                    type: String(r.type),
                    value: String(r.value),
                    contribution: Number(r.contribution)
                })),
            }));

            setGraphData({ nodes, links });
        }
    }

    // Force configuration effect
    useEffect(() => {
        if (fgRef.current) {
            fgRef.current.d3Force('charge')?.strength(-200);
            fgRef.current.d3Force('link')?.distance(100);
            fgRef.current.d3ReheatSimulation();
        }
    }, [graphData, dimensions]);


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
                            nodeLabel={(nodeObj) => {
                                const node = nodeObj as ExtendedGraphNode;
                                return `
                <div style="padding: 4px; font-size: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 4px;">
                  <div style="font-weight: bold; color: #f9fafb;">[${node.code}] ${node.label}</div>
                  <div style="color: #9ca3af; font-size: 11px;">Group: ${node.group || "N/A"}</div>
                  <div style="color: #fbbf24; font-size: 11px;">Score: ${node.score.toFixed(4)} ${node.isRecommended ? " (Recommended)" : ""}</div>
                </div>
              `;
                            }}
                            linkLabel={(linkObj) => {
                                const l = linkObj as ExtendedGraphLink;
                                const concepts = l.concepts || [];
                                const reasons = l.reasons || [];
                                const topReasons = reasons.slice(0, 2).map((r) => `${r.type}: ${r.value}`).join("<br/>");

                                return `
                  <div style="padding: 4px; font-size: 11px; background: #0f172a; border: 1px solid #334155; border-radius: 4px;">
                    <div style="font-weight: bold; color: #e5e7eb; border-bottom: 1px solid #1f2937; margin-bottom: 2px;">Edge Analysis</div>
                    <div style="color: #38bdf8;">${concepts.join(" &bull; ")}</div>
                    ${topReasons ? `<div style="color: #9ca3af; margin-top: 2px;">${topReasons}</div>` : ""}
                  </div>
                `;
                            }}
                            linkHoverPrecision={20}
                            nodeRelSize={8}
                            backgroundColor="rgba(0,0,0,0)" // transparent
                            linkColor={() => "rgba(148, 163, 184, 0.6)"}
                            linkWidth={(linkObj) => 0.5 + ((linkObj as ExtendedGraphLink).weight || 0) * 2}
                            linkDirectionalParticles={(linkObj) =>
                                (linkObj as ExtendedGraphLink).weight && (linkObj as ExtendedGraphLink).weight > 0.3 ? 2 : 0
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
                            onNodeClick={(nodeObj) => {
                                if (onSelectCourse) {
                                    onSelectCourse((nodeObj as ExtendedGraphNode).code);
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
