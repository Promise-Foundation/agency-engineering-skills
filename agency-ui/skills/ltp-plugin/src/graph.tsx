import { useMemo } from "react";
import Dagre from "@dagrejs/dagre";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./ltp.css";
import type { LtpModel } from "./mapping";

const NODE_WIDTH = 214;
const NODE_HEIGHT = 66;

interface NodeData extends Record<string, unknown> {
  label: string;
  kind: string;
}
type FlowNode = Node<NodeData>;

function short(text: string): string {
  return text.length > 54 ? `${text.slice(0, 53)}…` : text;
}

function EntityNode({ data }: NodeProps<FlowNode>) {
  return (
    <div className={`ltp-node ltp-node--${data.kind}`}>
      <Handle type="target" position={Position.Bottom} className="ltp-handle" />
      <div className="ltp-node__kind">{data.kind.replace(/_/g, " ")}</div>
      <div className="ltp-node__label">{data.label}</div>
      <Handle type="source" position={Position.Top} className="ltp-handle" />
    </div>
  );
}

function GateNode({ data }: NodeProps<FlowNode>) {
  return (
    <div className="ltp-gate" title="all premises jointly cause the effect">
      <Handle type="target" position={Position.Bottom} className="ltp-handle" />
      <span>{data.label}</span>
      <Handle type="source" position={Position.Top} className="ltp-handle" />
    </div>
  );
}

const nodeTypes = { entity: EntityNode, gate: GateNode };

function layout(nodes: FlowNode[], edges: Edge[]): FlowNode[] {
  const graph = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "BT", ranksep: 66, nodesep: 34, marginx: 20, marginy: 20 });
  for (const node of nodes) graph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  for (const edge of edges) graph.setEdge(edge.source, edge.target);
  Dagre.layout(graph);
  return nodes.map((node) => {
    const position = graph.node(node.id);
    return { ...node, position: { x: position.x - NODE_WIDTH / 2, y: position.y - NODE_HEIGHT / 2 } };
  });
}

export function LtpGraph({
  model,
  viewKey,
  onSelect,
}: {
  model: LtpModel;
  viewKey: string;
  onSelect?: (nodeId: string) => void;
}) {
  const flow = useMemo(() => {
    const view = model.views?.[viewKey];
    if (!view || view.empty) return null;
    const entityById = new Map(model.entities.map((entity) => [entity.id, entity]));
    const gateById = new Map((model.gates ?? []).map((gate) => [gate.id, gate]));
    const present = new Set(view.node_ids);

    const nodes: FlowNode[] = view.node_ids.map((id) => {
      const gate = gateById.get(id);
      if (gate) {
        return { id, type: "gate", position: { x: 0, y: 0 }, data: { label: (gate.operator ?? "all").toUpperCase(), kind: "gate" } };
      }
      const entity = entityById.get(id);
      return {
        id,
        type: "entity",
        position: { x: 0, y: 0 },
        data: { label: entity ? short(entity.statement) : id, kind: entity ? entity.kind : "unknown" },
      };
    });

    const edges: Edge[] = view.edges
      .filter((edge) => present.has(edge.source) && present.has(edge.target))
      .map((edge, index) => ({
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
        label:
          edge.relation === "necessary_for"
            ? "necessary for"
            : edge.relation === "conflict"
              ? "conflict"
              : edge.relation === "overcome_by"
                ? "overcome by"
                : edge.relation === "then"
                  ? "then"
                  : "",
        markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14 },
        style:
          edge.relation === "necessary_for"
            ? { strokeDasharray: "5 4" }
            : edge.relation === "conflict"
              ? { stroke: "#e0645a", strokeDasharray: "2 3" }
              : {},
      }));

    return { nodes: layout(nodes, edges), edges };
  }, [model, viewKey]);

  if (!flow) {
    return <div className="ltp-graph-empty">This view is not modelled in this analysis.</div>;
  }
  return (
    <div className="ltp-graph">
      <ReactFlow
        nodes={flow.nodes}
        edges={flow.edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={1.6}
        nodesDraggable={false}
        onNodeClick={(_, node) => onSelect?.(node.id)}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={22} size={1} color="#2a323c" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
