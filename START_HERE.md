# Start Here

For your first session, follow [Getting Started](docs/GETTING_STARTED.md) from installing Python through saving your first Study note. Use [Installation and Requirements](docs/INSTALLATION.md) to add optional tools later. The [Chinese handbook](DOCUMENTATION.zh-CN.md#beginner-start) provides the same beginner route in Chinese.

OpenSci **1.0.0** provides Research Workspace, Literature Workspace and supporting review, execution and maintenance modules. Start with the [Feature Catalog](FEATURES.md), then open the [English handbook](OpenSci-Manual.html) or [Chinese handbook](OpenSci-Manual.zh-CN.html).

1. Complete the three settings files in [Getting Started](docs/GETTING_STARTED.md), then open `Start-OpenSci.cmd` on Windows. Select **1 Browse Studies** for read-only use; **0 Exit** closes the menu.
2. Keep software and Study records in their separate folders. Create a discussion Study first; Git and execution-node setup can wait until you need them.
3. Select **2 Create Study** only after setup. An empty list is expected on a new installation. Use menu 10/11 for overview and discussion progress.
4. Select **Literature Workspace** to check capabilities before configuring a protected Zotero connection. Follow the [Literature guide](docs/LITERATURE.md).
5. Add [Assistant Access and Run Monitor](INTEGRATION.md), the [Claude Development Launcher](CLAUDE_LAUNCHER.md), or execution services only when needed and after their own configuration checks.

To keep working while traveling, use [Research from Your Phone](docs/MOBILE_RESEARCH.md).

Package Verification belongs to installation maintenance: use `verify_delivery.py` on a fresh unconfigured extraction. Existing local configuration and study data must be preserved.

The supplied experiment runner supports the public Estimator Comparison, one CPU thread and no GPU. [Feature limits](FEATURES.md#availability-and-operating-limits) distinguish available implementation from integrations that still require live acceptance. Installing files alone does not start services or approve experiments.
