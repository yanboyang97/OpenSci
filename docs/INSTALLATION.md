# Installation and Requirements

[Handbook](../DOCUMENTATION.md)

Install only the software needed for the features you will use. OpenSci itself does not install software, start services, create accounts or copy credentials. The basic Study workspace runs on the Python standard library. A GPU, Node.js, Docker, a database server and a model subscription are not baseline requirements.

## Supported environment and minimum versions

The numbers below are dependency floors for this release, not a claim that every operating-system and dependency combination has been exercised. Keep security updates installed. Where a vendor does not publish a numerical minimum for a required client capability, the capability is the requirement; do not interpret an unspecified minimum as support for every version.

| Component | Minimum or required capability | Needed for | Installation and readiness |
| --- | --- | --- | --- |
| Operating system | Windows 10 with Windows PowerShell 5.1; or a maintained Linux distribution providing Python 3.10 | Core workspace | Windows launchers require Windows. Ubuntu 22.04 is a Linux baseline that supplies Python 3.10. Approved experiment submission requires Linux or WSL 2. macOS is not a validated target of this release. |
| Python | **3.10** | All commands and MCP | Install from [python.org](https://www.python.org/downloads/) or the OS package manager. Include the standard-library SQLite module. Check `python --version`; select the full interpreter path when multiple installations exist. |
| Git | **2.28** | Research source provenance, repository installation and source-based backup | Install from [git-scm.com](https://git-scm.com/downloads). The documented `git init -b` requires [Git 2.28](https://git-scm.com/docs/git-init/2.28.0). Discussion-only Studies do not need Git. |
| Windows PowerShell | **5.1** | Windows menu and Study Chat launchers | Included with supported Windows installations. Check `$PSVersionTable.PSVersion`. |
| PowerShell | **7.0** | Claude Development Launcher | Install [PowerShell](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows) separately; configure its executable path. |
| OpenSSH client | Supports fixed commands, host-key checking and `ExitOnForwardFailure`; no OpenSci numeric floor established | Remote Development Workspace or remote MCP | Install the [Windows OpenSSH client](https://learn.microsoft.com/windows-server/administration/openssh/openssh_install_firstuse) or distribution package. Record `ssh -V` and validate the required restricted transport. An SSH server is needed only on the receiving host. |
| WSL | **WSL 2**, only if selected | Linux work or experiment execution on Windows | Install through [Microsoft's WSL instructions](https://learn.microsoft.com/windows/wsl/install). Install Python and Git inside the selected distribution. Native Windows discussion and local MCP do not need WSL. |
| Zotero | **10.0**, Local API **3**, with `Zotero-Server-ID` | Literature library operations | Install [Zotero](https://www.zotero.org/download/), sign in to the intended personal library, and enable local communication. The [Local API](https://www.zotero.org/support/dev/web_api/v3/local_api) provides the instance identity and local write authorization required by OpenSci. |
| Edge or Chrome and Zotero Connector | Current Stable or Extended Stable browser; compatible current Connector | Browser-assisted collection | Install the Connector from [Zotero](https://www.zotero.org/download/connectors). These are the vendor's [supported browser channels](https://www.zotero.org/support/system_requirements); no fixed version is promised. OpenSci's browser setting accepts `edge` or `chrome`. |
| Word desktop and Zotero Word plugin | Windows Word **2010** or later, excluding Starter; active compatible Zotero plugin | Native Word citations | Follow [Zotero's Word integration](https://www.zotero.org/support/word_processor_integration). This is the vendor compatibility floor. OpenSci additionally requires an observed local editing session and native citation fields; Word web alone does not provide this workflow. |
| PyMuPDF | **1.24**, below **2** | PDF text extraction | Install `PyMuPDF>=1.24,<2` in the chosen environment. Text extraction does not provide OCR or verify figures. |
| MLflow | **3.0**, below **4** | Experiment Tracking | Install `mlflow>=3,<4`; separately configure the tracking service, access and storage. No tracking server starts automatically. |
| Prefect | **3.0**, below **4** | Workflow Scheduling | Install `prefect>=3,<4`; provision a work pool and authorized worker. Local discussion and MCP do not depend on it. |
| Google Gen AI SDK | **1.40**, below **2** | Gemini Evidence Review | Install `google-genai>=1.40,<2`. This release uses the [SDK's context-managed Client API](https://github.com/googleapis/python-genai/blob/v1.40.0/google/genai/client.py). Configure an eligible Google Cloud project, region, model and Application Default Credentials. |
| Codex CLI | **0.162.1** release support floor; build providing `exec`, `--ephemeral`, `--ignore-user-config`, JSON events and `--output-last-message` | Optional Codex Evidence Review | Install a current supported CLI and check `codex exec --help` against these options before enabling it. For plugins, the host must support the portable plugin manifest or direct stdio MCP configuration. |
| Claude Code | Native CLI with `--bare`, `--tools`, `--disallowedTools`, `--no-session-persistence`, `--max-turns`, `--max-budget-usd`, JSON output; numeric minimum not established | Optional Claude development/review | Follow [Claude Code installation](https://code.claude.com/docs/en/setup). The Windows development launcher requires native `claude.exe`. Verify options locally; CLI model access and credentials are separate from a desktop subscription. |
| Secure MCP Tunnel client | **0.0.16** launcher compatibility baseline, or a newer compatible release | Ordinary Chat access to a private coordinator | Download from the [official release page](https://github.com/openai/tunnel-client/releases/latest). Verify the downloaded checksum and confirm launcher options in `help`. The binary is not redistributed. Account access and tunnel permissions are separate prerequisites. |
| ChatGPT / Codex host | Local stdio MCP for desktop; custom private MCP connection and tunnel access for ordinary Chat | Assistant Access | No vendor numeric minimum is established here. Confirm the required feature exists in the actual account and client; use [plugin setup](PLUGINS.md). |
| ChatGPT mobile and desktop apps | Supported builds with remote computer access; numeric minimum not established | Research from a phone | Use the same account/workspace and link your computer through its connection settings. See [Research from Your Phone](MOBILE_RESEARCH.md) for setup and the current official client requirements. |
| LaTeX / Quarto | A working LaTeX engine plus BibTeX, or a Quarto installation able to render the selected `.qmd`; numeric minimum not established | Compiling exported manuscripts | Install a supported [TeX distribution](https://www.latex-project.org/get/) or [Quarto](https://quarto.org/docs/get-started/). Exporting bibliography data needs neither. Record `pdflatex --version`, `bibtex --version` or `quarto --version` and compile the actual manuscript. |
| markdown-it-py | Exactly **4.0.0** | Rebuilding the offline handbooks only | Install from `requirements-docs.txt`. Reading the supplied HTML needs only a browser. |

The optional Python dependencies are recorded in [requirements-optional.txt](../requirements-optional.txt). Install selected packages in a dedicated environment with `python -m venv .venv`; invoke its interpreter explicitly. Installing the whole optional requirements file is convenient only if all those integrations are wanted. Record installed versions with `python -m pip freeze` outside the public source tree. DVC is not called by OpenSci; add it separately only when the research project uses it, with a backend chosen for that project's storage.

## Install the software

Download the runtime ZIP from [OpenSci releases](https://github.com/yanboyang97/OpenSci/releases), or clone the repository. Extract into a new directory and verify the archive SHA-256 against the release checksum. On a fresh extraction, run:

```text
python -B verify_delivery.py
```

For a Git checkout, use `python -B verify_delivery.py --installed`; Git metadata is outside the distributed file manifest. Hashes verify bytes against the manifest, not publisher identity. Do not delete an installed user's local files to satisfy the strict fresh-package check.

<a id="complete-setup-before-real-use"></a>
## Complete setup before real use

1. Choose a writable installation folder and a **separate coordinator folder** on a reliable local filesystem. Only one coordinator writes a Study. Keep raw research data, credentials and backups outside the public repository.
2. Follow [Getting Started](GETTING_STARTED.md) to create the coordinator configuration and bind the launcher to it. On Windows, set actual executable paths in `config/runtime.local.json`.
3. Set filesystem permissions. The operator owns coordinator records and connection policies. A dedicated assistant/service account must not be able to rewrite grants or human approvals. Same-account access is a single-user trust boundary.
4. Create a Study with your own ID and goal. Confirm that its Overview is readable and retain the creation receipt. No Git repository or model account is needed for discussion progress.
5. For assistants, configure one protected Study scope and follow [Plugins and MCP](PLUGINS.md). Start read-only, then explicitly allow the required writes. A connection file contains paths, never secret values.
6. For Zotero, complete [Literature setup](LITERATURE.md): local communication, personal-library identity, explicit write grants, selected sources, institutional/API access, browser choice, finite analysis limits and separate Zotero backups. Research directions start empty.
7. For source-dependent work, choose a separate research Git repository, a public-safe commit identity and a clean source commit. Configure intended Development Workspaces and Execution Nodes. Synchronize a common history before switching workspaces.
8. Before model review or execution, configure eligible providers, credentials, budgets, the actual interpreter/environment, and independent human approval. An installed model client or example provider entry is not authorization to spend money or submit work.
9. Set backup destinations, retention and recovery ownership. Check an isolated restore before relying on the backup. Configure Run Monitor, MLflow and Prefect only when used.

Setup is complete for a feature when its documented prerequisite checks succeed in your environment. A missing optional integration does not prevent independent Study discussion.
