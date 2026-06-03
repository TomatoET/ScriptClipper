# Security Policy

## Supported Versions

ScriptClipper is currently in initial preview. Security fixes are considered for the latest release only.

| Version | Supported |
| ------- | --------- |
| v0.1.x  | Yes       |

## Reporting a Vulnerability

Please do not publish vulnerability details in a public issue before the issue is reviewed.

Report security concerns through one of these paths:

- Open a private GitHub security advisory for this repository, if available.
- Contact the repository owner through GitHub if private advisories are not available.

Include:

- A clear description of the issue.
- Steps to reproduce it.
- Affected files or features.
- Any relevant environment details.

## Scope

Relevant security concerns include:

- Accidental exposure of credentials or private data.
- Unsafe file handling.
- Path traversal or unintended filesystem access.
- Packaging issues that include unexpected files.
- Vulnerabilities in project dependencies.

## Out of Scope

- Issues that require already-compromised local administrator access.
- General feature requests.
- Reports without enough information to reproduce or evaluate.

## Handling Secrets

Do not commit:

- API keys or tokens.
- Cookies or account credentials.
- `.env` files.
- Private keys or certificates.
- Machine-specific absolute paths that reveal private local information.
