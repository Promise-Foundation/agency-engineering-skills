# Diagnostic codes

Generated from `ltp.diagnostics` by `ltp.schema` -- do not hand-edit.

`ltp validate` emits these. **error** blocks publication; **warning** is the
scrutiny backlog; **info** is a note.

| Code | Severity | Meaning |
|---|---|---|
| `CLR-001` | warning | sufficiency claim has no CLR review (candidate claim) |
| `CLR-003` | error | CLR concluded no causality exists |
| `CLR-006` | error | CLR concluded the cause and effect are reversed |
| `CLR-007` | error | CLR concluded the claim is a tautology |
| `CLR-008` | warning | claim has open CLR checks (not yet scrutinized) |
| `CLR-009` | warning | claimed entity existence is unverified |
| `CON-001` | error | current constraint is not a constraint-kind entity |
| `CON-002` | error | current constraint has no limiting-mechanism argument |
| `CON-003` | warning | constraint assessment has no goal measure |
| `CON-004` | warning | constraint assessment considered no alternatives |
| `CON-005` | warning | constraint assessment has no Five Focusing Steps posture |
| `CON-006` | warning | root cause used as the constraint without demonstration |
| `CRT-001` | warning | UDE is written as a missing feature, not a harmful effect |
| `CRT-002` | error | UDE has no cause leading into it |
| `CRT-003` | warning | UDE is not observed / present-tense |
| `CRT-004` | error | causal cycle (not modelled as a feedback loop) |
| `CRT-005` | warning | root-cause candidate explains only one UDE |
| `CRT-006` | warning | causal claim may require an additional premise |
| `CRT-007` | error | compound premises without an explicit operator |
| `CRT-008` | warning | important causal claim has no assumptions and no CLR |
| `EC-002` | error | cloud lacks distinct A/B/C/D/D' roles |
| `EC-003` | error | cloud does not wire four necessity claims |
| `EC-004` | error | cloud has no explicit D-D' incompatibility |
| `EC-005` | warning | cloud necessity claim has no assumption |
| `EC-006` | warning | no evidence that both needs are legitimate |
| `EC-007` | warning | no assumption is targeted by an injection |
| `EC-008` | error | conflict has no evidence of persistence |
| `EC-009` | warning | conflict rests only on generic resource finitude |
| `FRT-001` | error | injection enters no causal claim |
| `FRT-003` | error | injection has no explicit desirable-effect path |
| `FRT-004` | error | injection jumps directly to goal achieved |
| `FRT-005` | warning | desirable effect supports no NC, CSF, or goal |
| `FRT-006` | error | negative branch is not dispositioned |
| `GT-001` | error | no goal is selected |
| `GT-002` | error | the selected goal is not a goal-kind entity |
| `GT-003` | error | CSF has no necessity path to the goal |
| `GT-004` | warning | CSF has no NC and is not justified as atomic |
| `GT-005` | error | NC has no necessity path to a CSF or the goal |
| `GT-006` | warning | goal-tree leaf has no observable satisfaction criterion |
| `GT-007` | warning | more than five top-level CSFs without justification |
| `GT-008` | warning | CSF appears necessary for another CSF, not the goal |
| `GT-010` | warning | necessary condition's necessity is unjustified |
| `ID-001` | info | entity id prefix does not match its kind |
| `INT-UNVERIFIED` | error | completed intervention has no outcome observation |
| `OBS-STALE` | error | prediction observation is stale |
| `PLAN-001` | info | analysis-plan status disagrees with model content |
| `PLAN-002` | warning | a required tree has no content |
| `PRED-001` | warning | root-cause candidate has no predicted effect |
| `PRED-002` | warning | a predicted effect that should exist was not observed |
| `PRED-003` | error | prediction waiver has no reason |
| `PRED-OVERDUE` | error | prediction is overdue and unevaluated |
| `PRT-001` | error | obstacle has no intermediate objective |
| `PRT-002` | warning | IO overcomes no named obstacle |
| `PRT-003` | warning | IO is written as an imperative action, not a condition |
| `PRT-004` | warning | disconnected prerequisite row |
| `PRT-006` | error | IO has no dependency path to the target injection |
| `REF-001` | error | reference to an unknown id |
| `REF-002` | error | reference to an id of the wrong kind for its role |
| `REL-001` | error | prevention or neutralisation encoded as causation |
| `REL-002` | error | forward causation encoded outside a sufficiency claim |
| `TIME-001` | error | temporal field is not a valid ISO date or datetime |
| `TT-002` | error | transition advances no intermediate objective |
| `TT-003` | warning | action contains multiple independently verifiable changes |
| `TT-004` | warning | action directly implements the whole injection |
| `TT-005` | warning | transition has no verification |
| `TT-006` | info | transition has no likely scope |
| `TT-007` | error | transition has no immediate observable effect |
| `XTR-003` | warning | injection resolves no root cause or conflict assumption |
| `XTR-004` | error | recommended action has no complete path to the goal |
| `XTR-005` | warning | entity is disconnected from every structure |

_70 codes: 34 error, 33 warning, 3 info._
