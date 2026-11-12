# Security Policy

## Reporting a Vulnerability

Do not publish API keys, account data, database files, or private Codex conversations in an issue. Report security concerns privately to the repository maintainer.

## Security Boundaries

The watchdog does not read credential values, mutate Provider configuration, or terminate Codex. Diagnostics are limited to Provider names/order, routing flags, executable version, and process names. Review any future integration that expands these boundaries before release.
