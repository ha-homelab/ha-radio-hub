# Continuous integration and automated approval

The required `check` job compiles both Ethernet ESPHome configurations, tests the
RF C++ contracts with sanitizers, exercises migration with synthetic inputs,
validates printable geometry and builds the serial-service container. Thread RCP
changes additionally run the existing independent RCP build.

Security scanning calls `victron-venus/venus-os-ci-toolkit` at the immutable commit
`5d827f345c66fdb493efba9c24cf79575b681fdb`: Trivy scans dependencies and secrets;
dependency review checks pull requests. The separate CodeQL matrix covers C++,
Python and GitHub Actions using build mode `none`, because embedded firmware is
built by its dedicated ESPHome job. Dependabot proposes reviewed workflow and
Python dependency updates. Scanner failures must be investigated before merging.

## Approval and review

`Auto Approve PRs` follows the labeled, trusted-author workflow used by the other
HA Homelab integrations. The `auto-approve` label opts an eligible non-draft PR in
to the pinned toolkit's metadata-only automated approval. It checks the actual
reviewer identity and current PR/base commits; it does not perform code review or
replace validation. The branch rules continue requiring a successful `check`, an
independent current approval and resolved review conversations. New commits dismiss
stale approvals. There is no protection bypass or automatic merge workflow here.

After modifying a PR, wait for its new checks, then rerun its **Auto Approve PRs**
workflow (or add the label if it has not been opted in). Once this workflow exists
on `main`, manual recovery also accepts a same-repository PR number and the exact
40-character expected head SHA. A mismatched or moved head is rejected by the
shared workflow. Do not rerun an older commit's CI as evidence for a newer commit.

`CodeRabbit Review Requests` uses the toolkit's deduplicated review-request flow
for newly opened PRs in active public repositories with fewer than ten stars,
plus manual dispatch for an existing PR. The shared workflow skips repositories
outside that eligibility policy. CodeRabbit must be installed for it to deliver
a review. The opening trigger becomes available after this workflow reaches
`main`; it does not run retroactively on the installation PR. Automated approval
and a CodeRabbit review are separate mechanisms.

`BOT_PAT` is an encrypted repository Actions **secret**, never an Actions variable
or Terraform value. Its account is the existing `californiantiramisu` reviewer,
with repository write access managed by the infrastructure repository. The token
is passed explicitly only to the shared metadata workflows; build and security
jobs do not receive it. The optional `APPROVAL_PAT` secret is needed only when the
primary bot cannot act as an independent reviewer. Privileged review workflows
must never execute source from the pull request.
