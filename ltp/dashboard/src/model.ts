// The dashboard consumes the normalized, already-validated dashboard-model.json
// served at /api/dashboard. It does NOT parse or validate YAML. The canonical
// field types are imported from ./model-types (generated from Python).
import type {
  Analysis,
  AnalysisPlan,
  Basis,
  CausalClaim,
  CLR,
  Cloud,
  Confidence,
  ConflictClaim,
  ConstraintAssessment,
  Entity,
  Evidence,
  Influence,
  NecessityClaim,
  ObstacleResolution,
  Operator,
  PredictedEffect,
  Project,
  ReviewStatus,
  Satisfaction,
  Transition,
} from "./model-types";

export type {
  Analysis,
  AnalysisPlan,
  Basis,
  CausalClaim,
  ClaimVerification,
  CLR,
  CLRCheck,
  CLRState,
  Cloud,
  Confidence,
  ConflictClaim,
  ConstraintAssessment,
  EmpiricalStatus,
  Entity,
  EntityKind,
  Evidence,
  Influence,
  Measure,
  NecessityClaim,
  ObstacleResolution,
  Operator,
  PlanItem,
  PlanStatus,
  PredictedEffect,
  Project,
  ReviewStatus,
  Satisfaction,
  Transition,
} from "./model-types";

export const viewOrder = [
  "goal-tree",
  "current-reality",
  "evaporating-cloud",
  "future-reality",
  "prerequisite-tree",
  "transition-tree",
] as const;

export type TreeView = (typeof viewOrder)[number];

// logic_status lives on gates and causal claims in the JSON contract but is not
// yet on the generated CausalClaim type, so it is declared here.
export type LogicStatus = "candidate" | "scrutinized" | "contradicted";
export type Severity = "error" | "warning" | "info";
export type DashboardRelation =
  | "causes"
  | "premise"
  | "necessary_for"
  | "conflict"
  | "overcome_by"
  | "then";

export interface DashboardCausalClaim extends CausalClaim {
  logic_status?: LogicStatus;
}

export interface Gate {
  id: string;
  is_gate: true;
  operator: Operator;
  claim: string;
  logic_status?: LogicStatus;
}

export interface Diagnostic {
  code: string;
  severity: Severity;
  title: string;
  message: string;
  target?: string;
  hint?: string;
}

export interface HealthCounts {
  error: number;
  warning: number;
  info: number;
}

export interface Health {
  counts: HealthCounts;
  publishable: boolean;
  diagnostics: Diagnostic[];
}

export interface BuildInfo {
  source_hash: string;
  generator: string;
}

export interface DashboardEdge {
  source: string;
  target: string;
  relation: DashboardRelation;
  claim?: string;
}

export interface DashboardView {
  title: string;
  empty: boolean;
  node_ids: string[];
  edges: DashboardEdge[];
}

export interface DashboardModel {
  schema_version: number;
  project: Project;
  analysis: Analysis;
  analysis_plan: AnalysisPlan;
  entities: Entity[];
  gates: Gate[];
  evidence: Evidence[];
  necessity_claims: NecessityClaim[];
  causal_claims: DashboardCausalClaim[];
  clouds: Cloud[];
  conflict_claims: ConflictClaim[];
  predicted_effects: PredictedEffect[];
  obstacle_resolutions: ObstacleResolution[];
  transitions: Transition[];
  constraint_assessment: ConstraintAssessment | null;
  views: Partial<Record<TreeView, DashboardView>>;
  health: Health;
  open_questions: string[];
  contradictions: string[];
  coverage_gaps: string[];
  build: BuildInfo;
}

export interface FileMeta {
  exists: boolean;
  name: string;
  modified_ns?: number;
  size?: number;
}

export interface DashboardMeta {
  model: FileMeta;
}

export interface ModelIndex {
  entities: Map<string, Entity>;
  gates: Map<string, Gate>;
  claims: Map<string, DashboardCausalClaim>;
  evidence: Map<string, Evidence>;
}

export function indexModel(model: DashboardModel): ModelIndex {
  return {
    entities: new Map(model.entities.map((entity) => [entity.id, entity])),
    gates: new Map(model.gates.map((gate) => [gate.id, gate])),
    claims: new Map(model.causal_claims.map((claim) => [claim.id, claim])),
    evidence: new Map(model.evidence.map((item) => [item.id, item])),
  };
}

// A minimal shape guard: the JSON is validated server-side, so this only guards
// against a truncated or wrong payload rather than re-validating the contract.
export function parseDashboard(value: unknown): DashboardModel {
  if (!value || typeof value !== "object") {
    throw new Error("The dashboard payload was not an object.");
  }
  const model = value as Partial<DashboardModel>;
  if (!model.project?.name) throw new Error("The dashboard payload is missing project.name.");
  if (!Array.isArray(model.entities)) throw new Error("The dashboard payload is missing entities.");
  if (!model.views || typeof model.views !== "object") {
    throw new Error("The dashboard payload is missing views.");
  }
  return value as DashboardModel;
}

export type NodeRef =
  | { kind: "entity"; entity: Entity }
  | { kind: "gate"; gate: Gate };

// Resolve a view node id (which may reference an entity OR a gate) to its record.
export function resolveNode(index: ModelIndex, id: string): NodeRef | null {
  const entity = index.entities.get(id);
  if (entity) return { kind: "entity", entity };
  const gate = index.gates.get(id);
  if (gate) return { kind: "gate", gate };
  return null;
}

export function humanize(value: string): string {
  return value.replaceAll("_", " ").replaceAll("-", " ");
}

const operatorLabels: Record<Operator, string> = {
  single: "SINGLE",
  all: "AND",
  any: "OR",
  exclusive_any: "XOR",
  magnitudinal: "MAG",
};

export function operatorLabel(operator?: Operator): string {
  return operator ? operatorLabels[operator] : "GATE";
}

export type Tone = "positive" | "negative" | "neutral";

// A single visual tone for an entity, derived from its review status.
export function reviewTone(status?: ReviewStatus): Tone {
  switch (status) {
    case "corroborated":
    case "user_confirmed":
      return "positive";
    case "disputed":
    case "invalidated":
    case "superseded":
      return "negative";
    default:
      return "neutral";
  }
}

// The four independent status dimensions the Refine panel filters on.
export const basisValues: Basis[] = ["observed", "inferred", "provisional"];
export const reviewStatusValues: ReviewStatus[] = [
  "unreviewed",
  "corroborated",
  "user_confirmed",
  "disputed",
  "invalidated",
  "superseded",
];
export const confidenceValues: Confidence[] = ["high", "medium", "low"];
export const satisfactionValues: Satisfaction[] = [
  "unknown",
  "satisfied",
  "partial",
  "unsatisfied",
  "not_applicable",
];

export interface Filters {
  basis: Set<Basis>;
  review_status: Set<ReviewStatus>;
  confidence: Set<Confidence>;
  satisfaction: Set<Satisfaction>;
}

export function defaultFilters(): Filters {
  return {
    basis: new Set(basisValues),
    review_status: new Set(reviewStatusValues),
    confidence: new Set(confidenceValues),
    satisfaction: new Set(satisfactionValues),
  };
}

function passes<T>(value: T | undefined, active: Set<T>): boolean {
  // An entity with a missing dimension is never hidden by that dimension.
  return value === undefined || active.has(value);
}

export function entityPasses(entity: Entity, filters: Filters): boolean {
  return (
    passes(entity.basis, filters.basis) &&
    passes(entity.review_status, filters.review_status) &&
    passes(entity.confidence, filters.confidence) &&
    passes(entity.satisfaction, filters.satisfaction)
  );
}

// Maps a view key to its analysis_plan field.
export const viewToPlanKey: Record<TreeView, keyof AnalysisPlan> = {
  "goal-tree": "goal_tree",
  "current-reality": "current_reality_tree",
  "evaporating-cloud": "evaporating_cloud",
  "future-reality": "future_reality_tree",
  "prerequisite-tree": "prerequisite_tree",
  "transition-tree": "transition_tree",
};

export const viewLabels: Record<
  TreeView,
  { short: string; title: string; purpose: string; question: string }
> = {
  "goal-tree": {
    short: "Goal",
    title: "What must be true",
    purpose: "Goal Tree",
    question: "What conditions make success possible?",
  },
  "current-reality": {
    short: "Reality",
    title: "Why it is stuck",
    purpose: "Current Reality Tree",
    question: "Which causes explain the effects we see?",
  },
  "evaporating-cloud": {
    short: "Conflict",
    title: "What is in tension",
    purpose: "Evaporating Cloud",
    question: "Which assumptions make both sides seem necessary?",
  },
  "future-reality": {
    short: "Future",
    title: "What resolves it",
    purpose: "Future Reality Tree",
    question: "How should the proposed change produce success?",
  },
  "prerequisite-tree": {
    short: "Sequence",
    title: "What comes first",
    purpose: "Prerequisite Tree",
    question: "Which obstacles must be overcome, and in what order?",
  },
  "transition-tree": {
    short: "Action",
    title: "What to do now",
    purpose: "Transition Tree",
    question: "Which action should create which observable effect?",
  },
};
