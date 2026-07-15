i am attempting to make an agentic coding skill with a very simple goal:

to be able to represent normative definitions within a repository.

for example,

a Class OUGHT to be defined with pydantic.

that's a norm.

a doctor OUGHT to follow their hippocratic oath.

that's another norm.

the primitives are promise and assessment.


Your idea becomes much clearer if a norm is not itself a primitive, but a relationship between:

a promise describing what is expected, and

an assessment determining whether reality conforms to that promise.

A useful formulation is:

A norm is an assessable promise.

Core model
Promise
A promise establishes an expectation.

Promise:
    promisor
    promisee
    scope
    condition
    expected_state
    source
Examples:

The repository promises its maintainers that every domain model
will be defined using Pydantic.
A doctor promises their patients that they will act according
to the Hippocratic oath.
The promisor does not always need to be a person. A repository, organization, team, package, or role can be treated as a normative actor.

Assessment
An assessment evaluates a subject against a promise.

Assessment:
    promise
    subject
    assessor
    evidence
    verdict
    explanation
The verdict should probably support more than Boolean results:

satisfied
violated
unknown
not_applicable
unknown is especially important. An agent should not interpret “I could not determine compliance” as “compliant.”

Derived norm
A norm can then be represented as:

Norm = Promise + Assessment procedure
Or more formally:

Norm(P, A)

where:

P describes the expected state
A determines whether a subject satisfies P
For your Pydantic example:

Promise:
    bearer: repository
    scope: Python classes representing domain entities
    expected_state: class inherits from pydantic.BaseModel
Assessment:
    subject: a Python class
    evidence: AST and import resolution
    criterion: inherits directly or indirectly from BaseModel
    verdict: satisfied | violated | unknown | not_applicable
Repository representation
A human-readable declaration might look like this:

id: python.domain-models.use-pydantic

promise:
  promisor: repository
  promisee:
    - maintainers
    - consumers

  scope:
    language: python
    paths:
      - src/domain/**/*.py

  condition:
    subject_is: domain_model

  expected:
    subject_ought_to:
      inherit_from: pydantic.BaseModel

  source:
    kind: repository_policy
    reference: docs/architecture.md

assessment:
  implementation: assessments.python.pydantic_model
  outcomes:
    - satisfied
    - violated
    - unknown
    - not_applicable

  evidence:
    - class_definition
    - resolved_base_classes
This keeps the normative declaration separate from the executable checker.

Minimal Python ontology
Since the system itself concerns normative definitions, Pydantic is a natural representation:

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class Promise(BaseModel):
    id: str
    promisor: str
    promisee: list[str] = Field(default_factory=list)

    scope: dict[str, Any] = Field(default_factory=dict)
    condition: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any]

    source: dict[str, Any] | None = None


class Evidence(BaseModel):
    kind: str
    location: str | None = None
    value: Any = None


class Assessment(BaseModel):
    promise_id: str
    subject: str
    assessor: str

    verdict: Verdict
    evidence: list[Evidence] = Field(default_factory=list)
    explanation: str


class Norm(BaseModel):
    promise: Promise
    assessment_implementation: str
I would avoid storing an assessment result inside the normative definition. The definition should identify the assessment procedure; individual assessment results are observations produced at a particular revision.

Important distinction: promise versus obligation
“Promise” and “ought” are closely related, but they are not identical.

A promise can generate an obligation:

The repository promises to use Pydantic.
Therefore, the repository ought to use Pydantic.
But some obligations are not created by the bearer’s own promise:

A library ought not expose user passwords.
This may come from law, organizational policy, professional duties, or another authority.

You can preserve promise as the primitive by allowing the promisor to be the norm-setting institution:

The organization promises users that repositories under its control
will not expose passwords.
Another option is to interpret promise more broadly as a normative commitment, rather than only a voluntary speech act.

That broader meaning will make the model work better for software repositories.

Bearer, authority, and beneficiary
The most important roles to distinguish are:

bearer       Who must conform?
authority    Who establishes the expectation?
beneficiary  Who is protected or served?
assessor     Who determines conformity?
For example:

bearer:      repository maintainers
authority:   architecture team
beneficiary: library consumers
assessor:    static-analysis agent
For a doctor:

bearer:      doctor
authority:   professional institution and personal oath
beneficiary: patients
assessor:    medical board, court, peers, or the doctor
Without these distinctions, “the repository promises” may become ambiguous.

Agent behavior
An agentic coding skill built around this model could follow a tight loop:

1. Discover applicable promises.
2. Identify subjects within each promise's scope.
3. Run the associated assessments.
4. Record evidence and verdicts.
5. Explain violations in terms of the promise.
6. Propose or apply a repair.
7. Reassess the modified repository.
A finding might be represented as:

promise: python.domain-models.use-pydantic
subject: src/domain/customer.py::Customer
verdict: violated

evidence:
  - kind: base_classes
    location: src/domain/customer.py:12
    value:
      - object

explanation: >
  Customer is classified as a domain model but does not inherit from
  pydantic.BaseModel.

suggested_repair:
  operation: replace_base_class
  value: pydantic.BaseModel
A strong foundational rule
The system should distinguish:

declaration: what ought to be true
assessment: what appears to be true
repair: how reality might be changed
Do not collapse these into one operation. In particular, an agent should not silently redefine a norm because satisfying it is inconvenient.

The simplest conceptual foundation is therefore:

Promise:
    a declared normative commitment

Assessment:
    an evidence-backed judgment about fulfillment

Norm:
    a promise for which an assessment procedure exists

Violation:
    an assessment that concludes the promise is not fulfilled
That is small enough to remain coherent, while still supporting lint rules, architectural constraints, security policies, professional obligations, and eventually norms that require human judgment.


That gives a promise a stable normative address:

/biology/botany/_relates_to_plants
where:

/biology/botany       domain
_relates_to_plants    local promise name
The fully qualified promise identifier is:

{domain}/{name}
Domain tree
Domains form a rooted tree:

/
└── biology
    ├── botany
    │   ├── bryology
    │   └── dendrology
    └── zoology
A promise declared in a domain applies to that domain and every descendant domain.

For example:

/biology/_studies_living_systems
is effective in:

/biology
/biology/botany
/biology/botany/bryology
/biology/zoology
But not in:

/chemistry
/software
Similarly:

/biology/botany/_relates_to_plants
is effective in:

/biology/botany
/biology/botany/bryology
/biology/botany/dendrology
but not in:

/biology/zoology
Declared versus effective promises
It helps to distinguish two views.

A declared promise is physically defined at a domain:

declared("/biology/botany")
    = { _relates_to_plants }
An effective promise is available after inheritance:

effective("/biology/botany/bryology")
    =
    declared("/")
    ∪ declared("/biology")
    ∪ declared("/biology/botany")
    ∪ declared("/biology/botany/bryology")
Formally, for domain 
d
d:

effective(d) = ⋃ declared(a)
               for every ancestor a of d, including d
This means inheritance is a property of the namespace, not something copied into each child domain.

Promise identity
There are two potentially useful identities.

Declaration identity
This identifies the original promise:

/biology/botany/_relates_to_plants
That identity remains unchanged when inherited.

At /biology/botany/bryology, the effective promise is still:

/biology/botany/_relates_to_plants
It does not become:

/biology/botany/bryology/_relates_to_plants
unless a new promise is explicitly declared there.

Effective binding
The inherited application can separately record the domain in which it is being evaluated:

promise: /biology/botany/_relates_to_plants
declared_at: /biology/botany
effective_at: /biology/botany/bryology
This distinction makes provenance clear.

Suggested model
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Domain(BaseModel):
    path: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("A domain must begin with '/'")

        if value != "/" and value.endswith("/"):
            raise ValueError("A domain must not end with '/'")

        if "//" in value:
            raise ValueError("A domain must not contain empty segments")

        return value

    def ancestors(self) -> list[str]:
        if self.path == "/":
            return ["/"]

        segments = self.path.strip("/").split("/")
        return [
            "/" + "/".join(segments[:index])
            for index in range(1, len(segments) + 1)
        ]


class PromiseDefinition(BaseModel):
    name: str
    domain: Domain
    statement: str
    assessment: str

    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.startswith("_"):
            raise ValueError("Promise names must begin with '_'")

        if "/" in value:
            raise ValueError("Promise names cannot contain '/'")

        return value

    @property
    def address(self) -> str:
        if self.domain.path == "/":
            return f"/{self.name}"

        return f"{self.domain.path}/{self.name}"


class EffectivePromise(BaseModel):
    promise: PromiseDefinition
    effective_domain: Domain

    @property
    def inherited(self) -> bool:
        return self.promise.domain.path != self.effective_domain.path
Example:

promise = PromiseDefinition(
    name="_relates_to_plants",
    domain=Domain(path="/biology/botany"),
    statement="Subjects in this domain ought to relate to plants.",
    assessment="assessments.botany.relates_to_plants",
)

effective = EffectivePromise(
    promise=promise,
    effective_domain=Domain(path="/biology/botany/bryology"),
)

assert promise.address == "/biology/botany/_relates_to_plants"
assert effective.inherited is True
Repository representation
A filesystem representation maps naturally onto the domain hierarchy:

.norms/
├── promises.yaml
└── biology/
    ├── promises.yaml
    └── botany/
        ├── promises.yaml
        └── bryology/
            └── promises.yaml
For example:

# .norms/biology/botany/promises.yaml

domain: /biology/botany

promises:
  _relates_to_plants:
    statement: >
      A subject in this domain ought to relate to plants.

    assessment:
      implementation: assessments.botany.relates_to_plants
Or each promise could be its own file:

.norms/biology/botany/_relates_to_plants.yaml
The file path then directly encodes the normative address.

Resolution algorithm
Given a target domain:

/biology/botany/bryology
the resolver walks from root to leaf:

/
/biology
/biology/botany
/biology/botany/bryology
At each level it loads locally declared promises.

def resolve_promises(
    target: Domain,
    declarations: list[PromiseDefinition],
) -> list[EffectivePromise]:
    ancestors = set(target.ancestors())

    applicable = [
        promise
        for promise in declarations
        if promise.domain.path in ancestors
    ]

    return [
        EffectivePromise(
            promise=promise,
            effective_domain=target,
        )
        for promise in applicable
    ]
The traversal order should generally be root-to-leaf so that more specific declarations can be processed after general ones.

Shadowing versus accumulation
You will need to decide what happens when the same local name occurs at multiple levels:

/biology/_preserves_life
/biology/botany/_preserves_life
There are two possible models.

Accumulation
Both promises remain effective because their full addresses differ.

/biology/_preserves_life
/biology/botany/_preserves_life
This is the safest default. Promise identity is based on the full address, not merely the local name.

Shadowing
The child declaration replaces the inherited promise having the same local name.

This is familiar from programming languages, but it hides normative obligations and weakens provenance. I would avoid implicit shadowing.

A better rule is:

Promises accumulate by default. Replacing, refining, or suppressing an inherited promise must be explicit.

Explicit refinement
A child promise can explicitly refine an inherited promise:

domain: /biology/botany

promises:
  _preserves_life:
    refines: /biology/_preserves_life
    statement: >
      Botanical research ought to preserve plant life and ecosystem
      diversity.
This creates a relationship without erasing the parent promise:

/biology/_preserves_life
          ↑ refined by
/biology/botany/_preserves_life
The child domain remains subject to both unless the refinement semantics explicitly state that satisfying the refinement entails satisfying the parent.

Explicit exceptions
Inheritance will eventually require exceptions. These should be first-class declarations rather than silent configuration flags.

For example:

domain: /biology/botany/paleobotany

exceptions:
  - promise: /biology/botany/_studies_living_plants
    reason: >
      Paleobotany primarily studies fossilized and extinct plant life.
An exception should itself be assessable and attributable:

exception:
  promise: /biology/botany/_studies_living_plants
  effective_at: /biology/botany/paleobotany
  authority: /biology/botany/_defines_subdisciplines
  justification: fossilized specimens are within scope
This prevents a child namespace from casually opting out of inherited norms.

Assessment resolution
An assessment is performed against both a promise and a target domain:

promise: /biology/botany/_relates_to_plants
subject: specimen-123
subject_domain: /biology/botany/bryology
effective_because:
  relationship: descendant
  declared_at: /biology/botany
verdict: satisfied
Applicability can therefore be determined mechanically:

A promise P applies to domain D when:

D = P.domain

or

D is a descendant of P.domain
This produces a compact foundation:

Domain
    A hierarchical namespace.

Promise
    A named normative declaration located in a domain.

Inheritance
    A promise applies to its declaring domain and all descendants.

Assessment
    A judgment about whether a subject fulfills an applicable promise.

Effective promise
    A declared promise viewed in the context of a descendant domain.
The important invariant is:

Inheritance changes where a promise is effective, but never changes the promise’s canonical address or origin.


there's one more important addition: a trust score can be calculated for any domain based on the proprotion of kept vs broken promises as determined by the assessments of the promise.  the status of the promise (broken, kept, ...) is not represented by the promise object itself.  truth is in the eye of the beholder.

Exactly. That establishes a crucial separation:

A promise declares what ought to be true.
An assessment claims whether it is true.
A trust score summarizes a chosen set of those claims.

A promise is never intrinsically “kept” or “broken.”

Assessor-relative status
Instead of:

promise.status = "broken"
the model should express:

Assessor A judges promise P to be broken
in domain D
at time T
based on evidence E.
Another assessor can legitimately produce a conflicting assessment:

- promise: /software/python/_classes_use_pydantic
  domain: /software/python/models
  assessor: static-analysis-agent
  verdict: kept

- promise: /software/python/_classes_use_pydantic
  domain: /software/python/models
  assessor: architecture-reviewer
  verdict: broken
Neither verdict mutates the promise.

Assessment model
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    KEPT = "kept"
    BROKEN = "broken"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class Assessment(BaseModel):
    promise: str
    effective_domain: str

    assessor: str
    subject: str | None = None

    verdict: Verdict
    confidence: float | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str | None = None

    observed_at: datetime
    repository_revision: str | None = None
The important identity is not merely:

promise + verdict
but something closer to:

promise
+ effective domain
+ subject
+ assessor
+ repository revision
+ observation time
That makes assessments historical claims rather than mutable global facts.

Trust is also observer-relative
A domain does not have one absolute trust score.

Instead:

trust(domain, observer, assessment-policy, snapshot)
For example:

trust(
    domain="/software/python",
    observer="alice",
    assessment_policy="assessments Alice accepts",
    snapshot="git:abc123"
)
Alice and Bob may assign different trust scores because they:

trust different assessors;

use different evidence;

select different time windows;

weight promises differently;

resolve conflicting assessments differently.

“Truth is in the eye of the beholder” therefore applies at two levels:

Assessment:
    What does this assessor believe?

Trust view:
    Which assessments does this observer accept?
The assessor and observer may be the same actor, but they do not have to be.

Basic trust calculation
For a domain 
D
D, first resolve its effective inherited promises:

effective(D)
Then select one usable verdict for each promise under the observer’s assessment policy.

A simple score is:

trust(D) = kept / (kept + broken)
unknown and not_applicable should normally be excluded from the denominator.

Example:

kept:           7
broken:         2
unknown:        3
not applicable: 1
Then:

trust = 7 / (7 + 2) = 0.777...
The result should retain its coverage:

domain: /software/python
trust: 0.778

counts:
  kept: 7
  broken: 2
  unknown: 3
  not_applicable: 1

coverage: 0.75
Here coverage is:

(kept + broken) / (kept + broken + unknown)
A trust score of 1.0 based on one assessed promise should not look equivalent to 1.0 based on one thousand assessments.

Trust report, not just trust number
A computed result should therefore contain more than a scalar:

class TrustScore(BaseModel):
    domain: str
    observer: str
    snapshot: str | None = None

    score: float | None
    kept: int
    broken: int
    unknown: int
    not_applicable: int

    coverage: float
    assessment_policy: str
When there are no kept or broken assessments:

score = null
not:

score = 0
No evidence is different from total failure.

The aggregation unit must be explicit
There is an important ambiguity in “proportion of kept versus broken promises.”

Suppose this promise exists:

/software/python/_classes_use_pydantic
and the domain contains 100 classes:

99 conform
1 violates
Possible interpretations include:

Promise-level scoring
The promise is considered broken because at least one applicable subject violates it:

kept promises:   0
broken promises: 1
trust:           0
Subject-level scoring
Each application of the promise is counted:

kept obligations:   99
broken obligations: 1
trust:              0.99
Fractional promise scoring
The promise receives a fulfillment ratio:

promise fulfillment: 0.99
Then domain trust averages promise fulfillment values.

These answer different questions. I would preserve all three concepts but make promise application the fundamental scoring unit:

Promise definition
    /software/python/_classes_use_pydantic

Promise applications
    Promise applied to ClassA
    Promise applied to ClassB
    Promise applied to ClassC
An assessment evaluates a particular application whenever a concrete subject exists.

Promise application
class PromiseApplication(BaseModel):
    promise: str
    effective_domain: str
    subject: str
For example:

promise: /software/python/_classes_use_pydantic
effective_domain: /software/python/models
subject: src/models/customer.py::Customer
The assessment then refers to this application:

application:
  promise: /software/python/_classes_use_pydantic
  effective_domain: /software/python/models
  subject: src/models/customer.py::Customer

assessor: pydantic-static-checker
verdict: broken
This avoids declaring the entire promise universally broken merely because one subject violates it.

A higher-level evaluator may still derive:

The promise is not universally fulfilled in this domain.
But that is another computed assessment, not a mutation of the promise.

Inherited promises and domain trust
Trust for a domain should ordinarily include all promises effective in that domain:

effective(D)
    =
    promises declared at D
    +
    promises inherited from every ancestor
Therefore /biology/botany/bryology can be evaluated against:

/biology/_concerns_living_systems
/biology/botany/_relates_to_plants
/biology/botany/bryology/_studies_bryophytes
The trust report should preserve provenance:

results:
  - promise: /biology/_concerns_living_systems
    declared_at: /biology
    inherited: true
    verdict: kept

  - promise: /biology/botany/_relates_to_plants
    declared_at: /biology/botany
    inherited: true
    verdict: kept

  - promise: /biology/botany/bryology/_studies_bryophytes
    declared_at: /biology/botany/bryology
    inherited: false
    verdict: broken
Resolving multiple assessments
Because assessments can conflict, the trust computation needs an explicit resolution policy.

Possible policies include:

latest_by_assessor
latest_accepted
majority
most_confident
most_conservative
all_assessments
A useful default is:

Filter to assessors trusted by the observer.

Filter to the repository revision being evaluated.

Select the latest assessment per promise application and assessor.

Resolve conflicts using the observer’s declared policy.

Calculate trust from the resolved verdicts.

Do not silently average contradictory claims.

A conflict is meaningful information:

resolution: unresolved_conflict

assessments:
  - assessor: static-checker
    verdict: kept
  - assessor: human-reviewer
    verdict: broken
Such a case may become unknown for scoring purposes until the observer chooses a conflict policy.

Weighted trust
Not all promises necessarily have equal normative importance.

/security/_does_not_expose_credentials
probably matters more than:

/style/_uses_trailing_commas
Weights should not live on the promise as objective truth unless they are part of the normative declaration. An observer can instead provide a weighting policy:

weights:
  /security/_does_not_expose_credentials: 10
  /style/_uses_trailing_commas: 1
Then:

weighted trust
    =
    weight of kept applications
    /
    weight of kept and broken applications
Again, the resulting score belongs to a view:

Alice’s weighted trust in /software
not:

The objective trust of /software
Refined ontology
The model now has five distinct concepts:

Domain
    A hierarchical namespace.

Promise
    A normative declaration with a canonical domain address.

Promise application
    A promise as applied to a domain or concrete subject.

Assessment
    An assessor’s evidence-backed verdict about a promise application.

Trust view
    An observer-relative aggregation of selected assessments.
The key invariants become:

Promises do not contain verdicts.

Assessments do not modify promises.

Different assessments may disagree.

Trust scores are derived, reproducible views.

Every trust score identifies whose view it represents,
which assessments it used, and what snapshot it describes.
A compact expression of the architecture is:

Promise = ought

Assessment = appears to be

Trust = how often the observer believes ought and is coincide

give me all documents i need in order to turn this into an agentic coding skill usable by claude or codex.



