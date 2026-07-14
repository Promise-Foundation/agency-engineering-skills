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
import {
  entityPasses,
  humanize,
  operatorLabel,
  reviewTone,
  viewLabels,
  type DashboardModel,
  type DashboardRelation,
  type Entity,
  type Filters,
  type Gate,
  type ModelIndex,
  type TreeView,
} from "./model";

const NODE_WIDTH = 280;
const NODE_HEIGHT = 142;
const GATE_WIDTH = 132;
const GATE_HEIGHT = 88;

interface EntityNodeData {
  entity: Entity;
  [key: string]: unknown;
}
interface GateNodeData {
  gate: Gate;
  [key: string]: unknown;
}
type EntityFlowNode = Node<EntityNodeData, "entity">;
type GateFlowNode = Node<GateNodeData, "gate">;
type FlowNode = EntityFlowNode | GateFlowNode;

function EntityNode({ data, selected }: NodeProps<EntityFlowNode>) {
  const { entity } = data;
  const tone = reviewTone(entity.review_status);
  const showSatisfaction =
    entity.satisfaction &&
    entity.satisfaction !== "unknown" &&
    entity.satisfaction !== "not_applicable";
  return (
    <article
      className={`ltp-node ltp-node--${entity.kind} ${selected ? "is-selected" : ""}`}
      data-tone={tone}
    >
      <Handle type="target" position={Position.Top} className="ltp-handle" />
      <header>
        <span className="node-id">{entity.id}</span>
        <span className="node-type">{humanize(entity.kind)}</span>
      </header>
      <p>{entity.statement}</p>
      <footer className="node-marks">
        <span className={`status-mark status-mark--${tone}`} aria-hidden="true" />
        {entity.review_status && <span className="node-mark">{humanize(entity.review_status)}</span>}
        {entity.basis && <span className="node-mark">{entity.basis}</span>}
        {entity.confidence && <span className="node-mark node-confidence">{entity.confidence}</span>}
        {showSatisfaction && (
          <span className="node-mark node-mark--sat">{humanize(entity.satisfaction!)}</span>
        )}
      </footer>
      <Handle type="source" position={Position.Bottom} className="ltp-handle" />
    </article>
  );
}

function GateNode({ data, selected }: NodeProps<GateFlowNode>) {
  const { gate } = data;
  return (
    <div
      className={`gate-node ${selected ? "is-selected" : ""}`}
      data-logic={gate.logic_status ?? "candidate"}
    >
      <Handle type="target" position={Position.Top} className="ltp-handle" />
      <span className="gate-op">{operatorLabel(gate.operator)}</span>
      <span className="gate-claim">{gate.claim}</span>
      <Handle type="source" position={Position.Bottom} className="ltp-handle" />
    </div>
  );
}

const nodeTypes = { entity: EntityNode, gate: GateNode };

function edgeMeta(relation: DashboardRelation): {
  type: string;
  label?: string;
  className: string;
} {
  switch (relation) {
    case "necessary_for":
      return { type: "smoothstep", label: "necessary for", className: "edge-necessary" };
    case "conflict":
      return { type: "straight", label: "conflict", className: "edge-conflict" };
    case "overcome_by":
      return { type: "smoothstep", label: "overcome by", className: "edge-overcome" };
    case "then":
      return { type: "smoothstep", label: "then", className: "edge-then" };
    case "premise":
    case "causes":
    default:
      return { type: "smoothstep", className: "edge-solid" };
  }
}

function dimsFor(node: FlowNode): { width: number; height: number } {
  return node.type === "gate"
    ? { width: GATE_WIDTH, height: GATE_HEIGHT }
    : { width: NODE_WIDTH, height: NODE_HEIGHT };
}

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
    const { width, height } = dimsFor(node);
    graph.setNode(node.id, { width, height });
  }
  for (const edge of edges) graph.setEdge(edge.source, edge.target);
  Dagre.layout(graph);
  return nodes.map((node): FlowNode => {
    const position = graph.node(node.id);
    const { width, height } = dimsFor(node);
    const placed = {
      position: { x: position.x - width / 2, y: position.y - height / 2 },
      style: { width, minHeight: height },
    };
    // Narrow on the discriminant so the placed node stays in the union.
    return node.type === "gate" ? { ...node, ...placed } : { ...node, ...placed };
  });
}

interface TreeCanvasProps {
  model: DashboardModel;
  index: ModelIndex;
  view: TreeView;
  filters: Filters;
  onSelect: (id: string | null) => void;
}

export function TreeCanvas({ model, index, view, filters, onSelect }: TreeCanvasProps) {
  const viewDefinition = model.views[view];

  const flow = useMemo(() => {
    if (!viewDefinition || viewDefinition.empty) return { nodes: [] as FlowNode[], edges: [] as Edge[] };

    const entityRefs: Entity[] = [];
    const gateRefs: Gate[] = [];
    for (const id of viewDefinition.node_ids) {
      const entity = index.entities.get(id);
      if (entity) {
        entityRefs.push(entity);
        continue;
      }
      const gate = index.gates.get(id);
      if (gate) gateRefs.push(gate);
    }

    // Entity nodes are filtered by the four active status dimensions.
    const visibleEntityIds = new Set(
      entityRefs.filter((entity) => entityPasses(entity, filters)).map((entity) => entity.id),
    );

    // Collect each gate's neighbouring node ids from the view edges.
    const gateNeighbors = new Map<string, Set<string>>();
    const addNeighbor = (gateId: string, other: string) => {
      const set = gateNeighbors.get(gateId) ?? new Set<string>();
      set.add(other);
      gateNeighbors.set(gateId, set);
    };
    for (const edge of viewDefinition.edges) {
      if (index.gates.has(edge.source)) addNeighbor(edge.source, edge.target);
      if (index.gates.has(edge.target)) addNeighbor(edge.target, edge.source);
    }

    // A gate is shown iff every entity it connects to is visible.
    const visibleGateIds = new Set(
      gateRefs
        .filter((gate) => {
          const neighbors = gateNeighbors.get(gate.id);
          if (!neighbors || neighbors.size === 0) return false;
          return [...neighbors].every((neighbor) =>
            index.entities.has(neighbor) ? visibleEntityIds.has(neighbor) : true,
          );
        })
        .map((gate) => gate.id),
    );

    const visibleNodeIds = new Set<string>([...visibleEntityIds, ...visibleGateIds]);

    const entityNodes = entityRefs
      .filter((entity) => visibleEntityIds.has(entity.id))
      .map(
        (entity): EntityFlowNode => ({
          id: entity.id,
          type: "entity",
          data: { entity },
          position: { x: 0, y: 0 },
        }),
      );
    const gateNodes = gateRefs
      .filter((gate) => visibleGateIds.has(gate.id))
      .map(
        (gate): GateFlowNode => ({
          id: gate.id,
          type: "gate",
          data: { gate },
          position: { x: 0, y: 0 },
        }),
      );
    const nodes: FlowNode[] = [...entityNodes, ...gateNodes];

    const edges: Edge[] = viewDefinition.edges
      .filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
      .map((edge, i) => {
        const meta = edgeMeta(edge.relation);
        return {
          id: `${edge.source}--${edge.relation}--${edge.target}--${i}`,
          source: edge.source,
          target: edge.target,
          type: meta.type,
          label: meta.label,
          markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
          className: meta.className,
        };
      });

    return { nodes: layout(nodes, edges), edges };
  }, [filters, index, viewDefinition]);

  if (!viewDefinition || viewDefinition.empty) {
    return (
      <div className="canvas-empty">
        <strong>Not modelled in this analysis.</strong>
        <span>
          The {viewLabels[view].purpose} was not produced for <code>{model.project.name}</code>.
        </span>
      </div>
    );
  }
  if (!flow.nodes.length) {
    return (
      <div className="canvas-empty">
        <strong>No nodes match the current filters.</strong>
        <span>Broaden basis, review, confidence, or satisfaction under Refine.</span>
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
          if (node.type === "gate") return "#486c7a";
          const data = node.data as EntityNodeData;
          const tone = reviewTone(data.entity.review_status);
          return tone === "positive" ? "#3f7652" : tone === "negative" ? "#a54b43" : "#8a7047";
        }}
      />
    </ReactFlow>
  );
}
