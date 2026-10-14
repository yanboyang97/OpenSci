# Glossary

The [Feature Catalog](../FEATURES.md) defines module and feature names. This glossary explains the objects used by those modules.

| Term | Meaning |
| --- | --- |
| Study | A continuing research question with its goal, evidence, decisions, source bindings and runs |
| Coordinator | The only deployment allowed to write a study's authoritative records |
| Development Workspace | The selected source workspace for research preparation, implementation and checks; stored as `active_agent` |
| Execution Node | The separately selected host/account where a human submits approved experiments |
| Study Record | The current structured study state plus links to immutable history |
| Revision | A monotonically increasing study update number, used to reject stale writes |
| Source Baseline | A clean Git commit and recorded origin identity shared by the intended workspaces |
| Planning Phase | A human workflow label, such as evidence gathering or analysis; not proof of scientific acceptance |
| Progress Note | A recorded conclusion, unresolved question or next step |
| Evidence Snapshot | Preserved original bytes and metadata used to support a traceable claim |
| Review Plan | Frozen review inputs, models, destinations, rounds, cost limits and shared rules |
| Review Record | The completed review's prompts, responses, reports and integrity manifest |
| Task Specification | A draft describing exact source, evidence, environment, node and resource limits |
| Human Approval | A separate human's authorization of a fixed task for a limited time |
| Run | One execution attempt with an original run ID, status and artifacts |
| Observation | A verified reading of a configured run source, including age and conflicts |
| Request | A structured operation with a unique ID and expected study revision |
| Receipt | Durable evidence of an operation's recorded outcome; not experiment approval |
| Unknown outcome | An interrupted operation whose commit result is not yet established; recover by its original request ID |
| Maintenance Plan | A reviewed, expiring preflight result for a deliberate study maintenance action |
| Resource Catalog | Stable external resource identities and file digests |
| Device Mapping | Local paths that bind catalog resources to one machine |
| Format marker | A machine-readable `schema_version` used by validators; OpenSci manages it, and it is not a module or product edition |
| MCP | Model Context Protocol, the local tool interface used by Assistant Access |
| Protected Grant | Local configuration defining permitted library, writing, remote or paid actions |
| Literature Candidate | A search result that has not yet been explicitly collected into the library |
| Coverage | What a search, extraction or analysis actually inspected, including missing or inaccessible material |
| Reconciliation | Checking original IDs and recorded effects against the actual system after uncertainty or external change |

A checksum establishes byte consistency against a trusted reference. It does not by itself establish publisher identity, execution authority or scientific truth.

## Stable field names in commands and configuration

These identifiers are kept so saved records and integrations remain readable. They do not name separate products or modules.

| Identifier | User-facing meaning |
| --- | --- |
| `hub.py`, `hub.local.json` | Research Workspace entry and its local configuration |
| `agent`, `active_agent`, `select_agent` in node configuration and study records | Development Workspace and its selection; the `agent` caller role in Assistant Access separately means a restricted assistant |
| `compute`, `compute_target`, `select_compute` | Execution Node and its selection |
| `checkpoint` | Record Progress, including a source consistency check |
| `anchor` | The source commit and repository identity bound to the study |
| `revision` | Study record update number; distinct from the OpenSci release number |
