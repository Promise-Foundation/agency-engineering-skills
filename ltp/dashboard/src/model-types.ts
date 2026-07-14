// Generated from ltp.models by ltp.schema -- do not hand-edit.
// Regenerate with `python -m ltp.schema`.

export type AnalysisMode = "forward" | "reverse" | "reconciliation";
export type AssessmentStatus = "candidate" | "confirmed";
export type Basis = "observed" | "inferred" | "provisional";
export type CLRState = "not_applicable" | "untested" | "open" | "pass" | "fail";
export type CloudStatus = "candidate" | "validated_persistent_conflict" | "rejected";
export type Confidence = "high" | "medium" | "low";
export type ConflictAnalysisStatus = "no_validated_persistent_conflict" | "validated_persistent_conflict";
export type EmpiricalStatus = "not_tested" | "supported" | "falsified" | "inconclusive";
export type EntityKind = "goal" | "critical_success_factor" | "necessary_condition" | "undesirable_effect" | "cause" | "root_cause" | "constraint" | "cloud_objective" | "cloud_need" | "cloud_action" | "injection" | "desirable_effect" | "negative_branch" | "trimming_injection" | "obstacle" | "intermediate_objective" | "existing_reality" | "need" | "transition_action" | "immediate_effect" | "assumption" | "risk";
export type Expectation = "should_exist" | "should_not_exist";
export type FocusingStep = "identify" | "exploit" | "subordinate" | "elevate" | "inertia";
export type Influence = "control" | "influence" | "monitor" | "outside";
export type OperatingMode = "diagnose" | "resolve_conflict" | "plan_change" | "full" | "reconcile";
export type Operator = "single" | "all" | "any" | "exclusive_any" | "magnitudinal";
export type PlanStatus = "required" | "done" | "deferred" | "skipped";
export type PredictedResult = "untested" | "observed" | "absent" | "mixed";
export type ReviewStatus = "unreviewed" | "corroborated" | "user_confirmed" | "disputed" | "invalidated" | "superseded";
export type Satisfaction = "unknown" | "satisfied" | "partial" | "unsatisfied" | "not_applicable";
export type TransitionSize = "small" | "medium" | "large";
export type VerificationRole = "entity_existence" | "mechanism" | "causal_outcome" | "scientific_outcome" | "negative_branch_guardrail" | "prerequisite_readiness" | "transition_acceptance";

export interface AlternativeConstraint {
  entity: string;
  rejected_because: string;
}

export interface Analysis {
  current_constraint?: string;
  recommended_next_action?: string;
  expected_effect?: string;
  updated_at?: string;
}

export interface AnalysisPlan {
  mode?: OperatingMode;
  goal_tree?: PlanItem;
  current_reality_tree?: PlanItem;
  evaporating_cloud?: PlanItem;
  future_reality_tree?: PlanItem;
  prerequisite_tree?: PlanItem;
  transition_tree?: PlanItem;
}

export interface CLR {
  clarity?: CLRCheck;
  entity_existence?: CLRCheck;
  causality_existence?: CLRCheck;
  cause_insufficiency?: CLRCheck;
  additional_cause?: CLRCheck;
  cause_effect_reversal?: CLRCheck;
  predicted_effect_existence?: CLRCheck;
  tautology?: CLRCheck;
}

export interface CLRCheck {
  result?: CLRState;
  evidence_refs?: string[];
  reservation?: string;
  proposed_additional_premise?: string;
}

export interface CausalClaim {
  id: string;
  conclusion: string;
  premises?: string[];
  operator?: Operator;
  mode?: string;
  assumption_refs?: string[];
  confidence?: Confidence;
  clr?: CLR;
  verification?: ClaimVerification;
}

export interface ClaimVerification {
  hypothesis_ref: string;
  role: VerificationRole;
  statement_hash?: string;
  empirical_status?: EmpiricalStatus;
}

export interface Cloud {
  id: string;
  objective: string;
  need_b: string;
  need_c: string;
  action_d: string;
  action_d_prime: string;
  necessity_claims: CloudNecessity;
  status?: CloudStatus;
  conflict_claim?: string;
  persistence_evidence?: string[];
  injection_refs?: string[];
}

export interface CloudNecessity {
  a_requires_b: string;
  a_requires_c: string;
  b_requires_d: string;
  c_requires_d_prime: string;
}

export interface ConflictAnalysis {
  status: ConflictAnalysisStatus;
  candidates_rejected?: RejectedCloud[];
}

export interface ConflictClaim {
  id: string;
  statement: string;
  assumption_refs?: string[];
  evidence_refs?: string[];
}

export interface ConstraintAssessment {
  entity: string;
  limiting_mechanism: string;
  goal_measure?: Measure;
  status?: AssessmentStatus;
  evidence_refs?: string[];
  alternative_candidates?: AlternativeConstraint[];
  focusing_step?: FocusingStepState;
  exploit_direction?: string;
  subordinate_direction?: string;
  elevation_direction?: string;
}

export interface Entity {
  id: string;
  kind: EntityKind;
  statement: string;
  basis?: Basis;
  review_status?: ReviewStatus;
  confidence?: Confidence;
  satisfaction?: Satisfaction;
  influence?: Influence;
  evidence_refs?: string[];
  assumption_refs?: string[];
  reasoning?: string;
  atomic?: boolean;
  atomic_justification?: string;
  satisfaction_criterion?: string;
  measure?: Measure;
}

export interface Evidence {
  id: string;
  source: string;
  observation: string;
  lines?: string;
  interpretation?: string;
  kind?: string;
}

export interface FocusingStepState {
  current: FocusingStep;
}

export interface LtpModel {
  project: Project;
  schema_version?: number;
  analysis?: Analysis;
  analysis_plan?: AnalysisPlan;
  entities?: Entity[];
  evidence?: Evidence[];
  necessity_claims?: NecessityClaim[];
  causal_claims?: CausalClaim[];
  clouds?: Cloud[];
  conflict_claims?: ConflictClaim[];
  conflict_analysis?: ConflictAnalysis;
  predicted_effects?: PredictedEffect[];
  obstacle_resolutions?: ObstacleResolution[];
  transitions?: Transition[];
  constraint_assessment?: ConstraintAssessment;
  views?: Record<string, View>;
  open_questions?: string[];
  contradictions?: string[];
  coverage_gaps?: string[];
}

export interface Measure {
  name: string;
  unit: string;
  period?: string;
}

export interface NecessityClaim {
  id: string;
  prerequisite: string;
  objective: string;
  assumption_refs?: string[];
  confidence?: Confidence;
}

export interface ObstacleResolution {
  id: string;
  obstacle: string;
  intermediate_objective: string;
}

export interface PlanItem {
  status?: PlanStatus;
  reason?: string;
}

export interface PredictedEffect {
  id: string;
  source_claim: string;
  statement: string;
  expectation?: Expectation;
  result?: PredictedResult;
  evidence_refs?: string[];
  waived?: boolean;
  waiver_reason?: string;
}

export interface Project {
  name: string;
  analyzed_path?: string;
  analysis_mode?: AnalysisMode;
  provisional_goal?: string;
  goal?: string;
}

export interface RejectedCloud {
  candidate: string;
  reason: string;
}

export interface Transition {
  id: string;
  action: string;
  advances: string;
  existing_reality?: string;
  need?: string;
  immediate_effect?: string;
  precondition_refs?: string[];
  verification?: TransitionVerification;
  likely_scope?: string[];
  owner?: string;
  estimated_size?: TransitionSize;
  risk_refs?: string[];
  rollback?: string;
}

export interface TransitionVerification {
  kind: string;
  command?: string;
  acceptance?: string;
}

export interface View {
  title?: string;
  purpose?: string;
  entities?: string[];
  claims?: string[];
  clouds?: string[];
  transitions?: string[];
  obstacle_resolutions?: string[];
}
