# Remote Acceptance

## Remote and unattended acceptance record

Status: to be completed by the actual operator. This template is not evidence of a pass and does not grant approval.

Operator/date/study/coordinator: ____
Source Development Workspace / destination Development Workspace / source commit and repository identity check: ____
Compute node/submission account/data and environment version: ____

Remote interaction:

- [ ] Check the actual SSH alias, account, directory, trusted fingerprint and development CLI login shell.
- [ ] Open the remote desktop project and access only authorized files; confirm the directories do not automatically synchronize.
- [ ] Separately record versions, eligibility, authentication and service acceptance for Codex, Python, tests, Claude and Vertex/other models.
- [ ] Keep formal submission credentials out of the agent account; accept real paths/accounts/ACLs separately for colocated roles.
- [ ] If a local WSL fallback is explicitly configured and accepted, check its continuation behavior; Development Workspace changes must not change the Execution Node.
- [ ] Dirty/mismatched commits, wrong repository/account/path all prevent switching.
- [ ] A simulated disconnect reports unavailable while preserving records/run IDs; reconcile remote jobs before recovery.

Evidence/digests/failures/actions: ____

Unattended operation and recovery:

- [ ] In an isolated synthetic test, close Windows access and inspect whether the actual remote process continues; retain timestamps and process/job IDs.
- [ ] Reconnect to the original run ID; reopening the launcher creates no experiment and duplicate submission is rejected.
- [ ] Test network loss, process exit and host-restart diagnostics/recovery, beyond basic SSH connectivity.
- [ ] Wait for human decisions, data permission, budget and approval; never manufacture authorization.
- [ ] Host production jobs in an accepted persistent session/scheduler and record retry/exit policy.
- [ ] Restore coordinator state/snapshots from a verified backup only after stopping the old writer.

Evidence/digests/failures/actions: ____
Separate conclusions: remote interaction ____; unattended operation ____; formal compute node ____.
