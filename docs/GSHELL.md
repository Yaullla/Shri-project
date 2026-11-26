# GShell / Cloud Shell development

Optional alternative to local Linux or WSL for the Radar project. GShell is
a third-party client, not a dependency of Radar. Cloud Shell is a temporary
development environment, not a production host or an always-on collector.

## One-time Windows preparation

1. Use a dedicated Google account with minimal permissions and enable Cloud Shell:
   https://shell.cloud.google.com/
2. Review https://github.com/Spectra010s/gshell and choose a specific release
   from https://github.com/Spectra010s/gshell/releases. Verify the archive against
   its published checksums.txt before extracting and adding the binary to PATH.
   A publisher checksum is not an independent security audit.
3. In PowerShell, run:

       gshell auth login
       gshell status
       gshell run "uname -s && git --version && python3 --version"

   Complete OAuth in your own browser. Never paste tokens, credentials.json,
   SSH private keys or API keys into Git, chats or logs.

4. Open an interactive Cloud Shell session using `gshell`. Check `uv --version`.
   If missing, install a reviewed uv release using the official instructions:
   https://docs.astral.sh/uv/getting-started/installation/
   Ensure uv is available on PATH in noninteractive shells too.

## First checkout and test

From Windows PowerShell (one-time checkout into a dedicated directory):

    gshell run "git clone --branch feat/gshell-cloudshell --single-branch https://github.com/Yaullla/Shri-project.git ~/shri-gshell"
    gshell run "cd ~/shri-gshell && bash scripts/cloudshell_check.sh"

After this integration is merged, use main for a new checkout instead.
For subsequent development sessions, review local changes before updating:

    gshell run "cd ~/shri-gshell && git status --short"
    gshell run "cd ~/shri-gshell && git pull --ff-only"
    gshell run "cd ~/shri-gshell && bash scripts/cloudshell_check.sh"

The check verifies GitHub HTTPS, syncs Python dependencies (locked when a
uv.lock exists), runs unit tests, the actual FastMCP stdio smoke test and Ruff.
It does not start a persistent server, collect live prices, spend model tokens,
set up a public tunnel, activate a billed Google Cloud project or alter Codex
configuration. Dependency resolution without a lockfile is development-only.
Review and commit a lockfile separately before production use.

## Optional Codex and optimizer setup

The existing scripts/install_dev.sh and scripts/register_codex.sh can be run
inside Cloud Shell after the base tests pass, subject to their Linux x86-64,
uv and Node prerequisites. Follow docs/INSTALL.md; keep automatic optimizer
hooks disabled until measured independently. Registration affects the Codex
client running INSIDE Cloud Shell, not Codex running on Windows.

For Windows Codex, use the GShell CLI as an explicit remote test command.
Do not expose arbitrary remote shell execution as an unauthenticated MCP
tool. The existing Radar stdio MCP remains separate from GShell.

## Limits and data

Keep only development data in the remote checkout. Do not copy .env files,
private customer data or live credentials. For private repositories, authenticate
Git separately with least-privilege credentials; do not put tokens in URLs.
Cloud Shell has idle, session, storage and weekly usage quotas:
https://cloud.google.com/shell/docs/quotas-limits
Use normal CI or an authorized persistent host for unattended collection.
GShell cannot bypass the limits. To revoke its access: `gshell auth logout`.

## Acceptance

Real end-to-end acceptance requires the account owner to authenticate and run
the check in their Cloud Shell. A successful GitHub commit is not evidence
that GShell is installed or the cloud tests have passed.
