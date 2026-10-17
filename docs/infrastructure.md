# Terraform ownership

This repository is provisioned by the existing
[HA Homelab infrastructure project](https://github.com/4alvit/terraform-github-ha-homelab).
Its canonical state stays in HCP Terraform:
`victron-venus/github-ha-homelab-infrastructure`.

Managed addresses are:

- `github_repository.repositories["ha-radio-hub"]`
- `github_branch_default.main["ha-radio-hub"]`
- `github_repository_vulnerability_alerts.repositories["ha-radio-hub"]`
- `github_repository_dependabot_security_updates.repositories["ha-radio-hub"]`
- `github_repository_ruleset.radio_hub`

Visibility is explicitly public, destruction is blocked, and secret scanning and
push protection are enabled. Only original/sanitized design material belongs here.
HA deployment, radio migration and device flashing are separate operator actions.

The initial bootstrap targets only the new repository and its settings. The
main-branch ruleset is applied after the initial source push; it then requires a
pull request, approval and successful `check`. Subsequent updates follow that
policy. Targeted bootstrap is not proof that unrelated organization state has no
drift: inspect a subsequent full plan separately before any wider apply.

Never add a second Terraform backend for the same GitHub repository. Keep HCP
and GitHub credentials in their existing secret stores, not in this project.
