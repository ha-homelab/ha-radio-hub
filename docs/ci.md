# Continuous integration and automated approval

The required `check` job gates five independent jobs in
[Prototype validation](../.github/workflows/check.yml). The `module-carrier` job
validates the current MC1; the other jobs retain shared implementation and
historical hardware regressions. The modular job compiles
both existing Ethernet ESPHome configurations, tests the RF/UART C++ contracts
with sanitizers, exercises migration with synthetic inputs, validates printable
geometry and builds the serial-service container. The single-host job checks the
new wiring/energy model, compiles all services into one S3 image plus its matching
H2 radio firmware, exercises the actual REST handlers with the pinned HA client,
and validates the separate concept enclosure. The MG24 job downloads hash-verified
tools and SDK, generates the exact module/UART configuration, builds the Zigbee
NCP and bootloader, and checks merged/update images. The PCB job checks the
carrier, MG24 adapter and integrated board with circuit-contract tests and
native KiCad ERC/DRC/connectivity checks in the official KiCad
10.0.6 container, pinned by digest. Network access is disabled during those
checks. The wiring atlas and physical contact drawings must reproduce from their
committed sources; their checks run in the single-host job. Failure, cancellation or
skipping of any job prevents the required gate from passing. Thread RCP changes additionally run
the existing independent Nordic RCP build.

The MC1 job checks generated diagrams and native-render provenance, the
independent carrier audit, GPIO/connector contracts and XIAO build recipes. It
then exercises the WK2132, Thread recovery and update helpers under host
sanitizers. It installs pinned mechanical dependencies, runs the rail and
enclosure geometry tests, and checks regenerated outputs against the committed
files with each `build.py --check`. The twelve rail/export checks cover fit
geometry and portable export comparison: STL solids and source-derived text must
agree; PNG integrity and dimensions are checked without requiring identical
cross-platform pixels. Use `--check --exact` for local byte reproduction.
The suite also includes the eleven enclosure checks
for native board alignment, printable meshes, antenna end-wall setback and
spacing-frame/floor-fastener clearance. It also compiles the complete S3-Nano
image and builds/verifies the matching
H2 RX23/TX24 RCP. The MG24 job separately builds the board-specific XIAO NCP and
UART bootloader. The PCB job runs the MC1 native CAD tests, ERC and classified
DRC in addition to the historical boards. Its 41 explicit opposing-face
pad/body projections remain in the raw DRC report; additional or changed
findings fail. These automated checks do not establish physical stack height,
radio range or successful operation of an assembled hub.

The modular job also checks that README board renders match their native PCB
source hashes and that the illustrated parts catalog covers every canonical
BOM row. Catalog checks run offline: manufacturer-photo availability and
AliExpress search results are not treated as build dependencies or verified
offers. Local identification illustrations keep the catalog usable when a
remote image is unavailable.

The DIY carrier also has native PCB checks and an independent connectivity
check that joins actual bottom-copper islands through the specified insulated
wire links. The modular job checks its print-package source/output hashes,
metric PDF dimensions and orientation regressions. These checks do not certify
a printer, toner-transfer process or hand-assembled board.

Security scanning calls `victron-venus/venus-os-ci-toolkit` at the immutable commit
`5d827f345c66fdb493efba9c24cf79575b681fdb`: Trivy scans dependencies and secrets;
dependency review checks pull requests. The separate CodeQL matrix covers C++,
Python and GitHub Actions using build mode `none`, because embedded firmware is
built by its dedicated ESPHome job. It runs for every pull request, including
stacked PRs whose base is another feature branch. Dependabot proposes reviewed workflow and
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
