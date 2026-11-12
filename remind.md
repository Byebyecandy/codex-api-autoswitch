# Maintenance Reminders

## Before changing CC Switch integration

- Re-check the installed CC Switch version and database schema. Treat database fields as version-specific and fail closed on unknown schemas.
- Keep CC Switch as the only live failover controller when native Routing + Failover is enabled.
- Never write Provider tokens, `auth.json`, `config.toml`, the CC Switch database, or failover queue settings from this watchdog.
- Keep the active Provider as P1 and the second sorted Codex Provider as P2. Verify actual queue IDs, not just queue length.
- Do not infer account quota exhaustion from HTTP 429 alone. Require explicit provider error evidence for quota-related classification.
- Do not restart or terminate Codex while user work may be active.

## Before release

- Run tests on the oldest supported Python version (3.10) and the newest supported version.
- Test paths with spaces, non-ASCII usernames, and non-ASCII Provider names on Windows.
- Confirm logs and diagnostics never contain tokens, auth file contents, raw request bodies, or full database rows.
- Keep `config.json` as the sole runtime config source; update `config.yaml` only as a clearly marked reference copy or remove it.
- Update README compatibility claims and limitations when actual behavior changes.
- Verify install scripts do not change global Python packages or install startup tasks without the user's choice.
