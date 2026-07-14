import { useMemo } from "react";
import Dagre from "@dagrejs/dagre";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import type {
  Confidence,
  EntityStatus,
  LtpEntity,
  LtpModel,
  ModelIndex,
  TreeView,
} from "./model";

const NODE_WIDTH = 280;
const NODE_HEIGHT = 142;

type FlowNode = Node<LtpEntity, "ltp">;

function LtpNode({ data, selected }: NodeProps<FlowNode>) {
  return (
    <article
      className={`ltp-node ltp-node--${data.type} ${selected ? "is-selected" : ""}`}
      data-status={data.status}
    >
      <Handle type="target" position={Position.Top} className="ltp-handle" />
      <header>
        <span className="node-id">{data.id}</span>
        <span className="node-type">{data.type.replaceAll("_", " ")}</span>
      </header>
      <p>{data.statement}</p>
      <footer>
        <span className={`status-mark status-mark--${data.status}`} aria-hidden="true" />
        <span>{data.status}</span>
        <span className="node-confidence">{data.confidence}</span>
      </footer>
      <Handle type="source" position={Position.Bottom} className="ltp-handle" />
    </article>
  );
}

const nodeTypes = { ltp: LtpNode };

function layout(nodes: FlowNode[], edges: Edge[]): FlowNode[] {
  const graph = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  graph.setGraph({
    rankdir: "TB",
    ranksep: 86,
    nodesep: 42,
    marginx: 34,
    marginy: 34,
  });
  for (const node of nodes) {
    graph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const edge of edges) graph.setEdge(edge.source, edge.target);
  Dagre.layout(graph);
  return nodes.map((node) => {
    const position = graph.node(node.id);
    return {
      ...node,
      position: {
        x: position.x - NODE_WIDTH / 2,
        y: position.y - NODE_HEIGHT / 2,
      },
      style: { width: NODE_WIDTH, minHeight: NODE_HEIGHT },
    };
  });
}

interface TreeCanvasProps {
  model: LtpModel;
  index: ModelIndex;
  view: TreeView;
  statuses: Set<EntityStatus>;
  confidences: Set<Confidence>;
  onSelect: (entityId: string | null) => void;
}

export function TreeCanvas({
  model,
  index,
  view,
  statuses,
  confidences,
  onSelect,
}: TreeCanvasProps) {
  const flow = useMemo(() => {
    const viewDefinition = model.views[view];
    if (!viewDefinition) return { nodes: [], edges: [] };
    const entities = viewDefinition.entities
      .map((id) => index.entities.get(id))
      .filter((entity): entity is LtpEntity => Boolean(entity))
      .filter(
        (entity) => statuses.has(entity.status) && confidences.has(entity.confidence),
      );
    const visible = new Set(entities.map((entity) => entity.id));
    const edges: Edge[] = viewDefinition.links
      .map((id) => index.links.get(id))
      .filter((link) => Boolean(link))
      .filter((link) => visible.has(link!.from) && visible.has(link!.to))
      .map((link) => ({
        id: link!.id,
        source: link!.from,
        target: link!.to,
        type: link!.relation === "conflicts_with" ? "straight" : "smoothstep",
        label: link!.relation.replaceAll("_", " "),
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
        className: link!.relation === "conflicts_with" ? "edge-conflict" : "",
      }));
    const nodes: FlowNode[] = entities.map((entity) => ({
      id: entity.id,
      type: "ltp",
      data: entity,
      position: { x: 0, y: 0 },
    }));
    return { nodes: layout(nodes, edges), edges };
  }, [confidences, index, model.views, statuses, view]);

  if (!model.views[view]) {
    return (
      <div className="canvas-empty">
        <strong>This view has not been modelled yet.</strong>
        <span>Add it under <code>views.{view}</code> in ltp-model.yaml.</span>
      </div>
    );
  }
  if (!flow.nodes.length) {
    return (
      <div className="canvas-empty">
        <strong>No nodes match the current filters.</strong>
        <span>Broaden status or confidence under Refine.</span>
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={flow.nodes}
      edges={flow.edges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.22 }}
      minZoom={0.15}
      maxZoom={1.8}
      nodesConnectable={false}
      nodesDraggable
      elementsSelectable
      onNodeClick={(_, node) => onSelect(node.id)}
      onPaneClick={() => onSelect(null)}
      proOptions={{ hideAttribution: false }}
    >
      <Background gap={28} size={1} color="var(--grid-dot)" />
      <Controls showInteractive={false} />
      <MiniMap
        pannable
        zoomable
        nodeColor={(node) => {
          const entity = node.data as LtpEntity;
          return entity.status === "observed" || entity.status === "confirmed"
            ? "#3f7652"
            : entity.status === "disputed"
              ? "#a54b43"
              : "#8a7047";
        }}
      />
    </ReactFlow>
  );
}
