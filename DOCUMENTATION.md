# OpenSci User and Maintainer Handbook

Use this handbook to install OpenSci, create a Study and choose the tools you want to connect. A **Study** is the saved record of one research question: its goal, evidence, decisions and next steps. You can begin without writing code or configuring a server.

This handbook covers OpenSci **1.0.1**, revised **2026-10-15**. For an introduction to the project's benefits and integrations, read the [project README](README.md#english).

Open [OpenSci-Manual.html](OpenSci-Manual.html) in the project root to read and search the English documentation offline. The files below are the maintained sources; the HTML is generated from them and should not be edited separately.

## Your first successful session

1. Follow [Getting Started](docs/GETTING_STARTED.md) to install the basic software and create three small settings files. It explains where to click, what to enter and what you should see.
2. Create one Study, read its Overview and save one progress note. At this point you have a working research record; no model subscription, Git repository or server is required.
3. Add [an AI assistant](docs/PLUGINS.md) to work in natural language, or [Zotero](docs/LITERATURE.md) to work with your papers. Configure one integration at a time.
4. To continue while away, follow [Research from Your Phone](docs/MOBILE_RESEARCH.md).
5. Use the later maintenance and technical references when you need backups, source-based research, experiments or extensions. You do not need to read them all before starting.

The OpenSci menu accepts numbered choices and short text. A ChatGPT or Codex conversation provides the AI assistant; the menu itself does not contain a language model. Each guide states its prerequisites, the actions to take and the expected result. Keep any error message and consult [Troubleshooting](docs/TROUBLESHOOTING.md) before changing unrelated settings.

## Find your task

| Task | Guide |
| --- | --- |
| Understand modules and available features | [Feature Catalog](FEATURES.md) |
| Install dependencies and prepare required settings | [Installation and Requirements](docs/INSTALLATION.md) |
| Install the plugin or MCP server | [Plugins and MCP](docs/PLUGINS.md) |
| Continue work through the ChatGPT phone app | [Research from Your Phone](docs/MOBILE_RESEARCH.md) |
| Understand the installation and first setup | [Getting started](docs/GETTING_STARTED.md) |
| List, create and resume studies | [Daily use](docs/DAILY_USE.md) |
| Search, collect, read and cite Zotero literature | [Literature work](docs/LITERATURE.md) |
| Understand local and remote configuration | [Configuration](docs/CONFIGURATION.md) |
| Inspect, back up, restore and hand over | [Maintenance](docs/MAINTENANCE.md) |
| Extend the implementation | [Development](docs/DEVELOPMENT.md) |
| Upgrade source, records or roll back | [Upgrade guide](docs/UPGRADE_GUIDE.md) |
| Diagnose errors and uncertain state | [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Understand the vocabulary | [Glossary](docs/GLOSSARY.md) |

## Reading paths

- **New users:** getting started → save your first progress note → add the one integration you need. Follow configuration and source-control references when those features become relevant.
- **New maintainers:** getting started → maintenance → troubleshooting → upgrade guide. Identify the sole writer, backup locations and original run IDs first.
- **Developers:** development → the relevant contract → targeted tests → separate English and Chinese handbooks → review according to the applicable workspace rules and a response to findings.

## Detailed reference

| Reference | Scope |
| --- | --- |
| [LITERATURE.md](LITERATURE.md) | Literature protocol, grants, sources, jobs, recovery and citations |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Modules and data flow |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Full deployment and synthetic execution |
| [LAUNCHER.md](LAUNCHER.md) | Research Workspace and remote continuation |
| [INTEGRATION.md](INTEGRATION.md) | Commands, receipts, MCP and observation |
| [RECORDS.md](RECORDS.md) | Record contracts and historical reads |
| [HISTORY.md](HISTORY.md) | Study history and plan recovery |
| [UPDATING.md](UPDATING.md) | Software update procedure |
| [BACKUP_AND_MIGRATION.md](BACKUP_AND_MIGRATION.md) | Backup and migration contract |
| [SIMULATION_ADAPTERS.md](SIMULATION_ADAPTERS.md) | Offline simulation interface |
| [CLAUDE_LAUNCHER.md](CLAUDE_LAUNCHER.md) | Windows development launcher |
| [environments/README.md](environments/README.md) | Interpreter and environment binding |
| [AGENTS.md](AGENTS.md) | Single maintained collaboration rules source |

## Documentation maintenance

Implementation and contracts define behavior, while configuration defines the current bindings. Documentation does not grant execution authority. When adding parameters or changing errors, defaults or record formats, update both languages, examples, tests and release hashes together. A documentation revision is distinct from a code version, Git commit and record schema_version.

See the [documentation workflow](docs/DEVELOPMENT.md#documentation) for rebuilding and checking. Replace example placeholders with real values. Sections marked for later enablement describe prerequisites and procedures, not completed setup. Update deployment status only after accepting a newly enabled capability in the actual environment.

## Separate language editions

The [Chinese handbook](DOCUMENTATION.zh-CN.md) and [Chinese offline edition](OpenSci-Manual.zh-CN.html) are maintained separately. The English offline edition collects all English guides and references. No machine-specific account, SSH alias or private user path belongs in either edition. Configuration examples are placeholders; preserve actual bindings only in ignored local files.
