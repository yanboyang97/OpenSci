# OpenSci

[中文介绍](#chinese) · [English](#english)

<a id="chinese"></a>
## 中文介绍

**把 AI 助手、文献和自己的电脑，组织成一个能持续推进课题的科研工作台。**

一个想法可能始于聊天，相关论文保存在 Zotero，代码放在电脑或服务器上，实验结果又在另一处。OpenSci 把这些工作围绕同一个课题连接起来：研究什么、依据是什么、做过哪些决定、下一步做什么，都能留下记录。换一次对话、换一台设备，也能从已有进展继续。

### 基于你熟悉的工具，连接完整的研究过程

OpenSci 以 Python 为基础，通过 MCP（让 AI 助手调用外部工具的连接协议）接入研究工具。你可以按需使用以下集成，无需一次装齐。

| 工具与资源 | 在 OpenSci 中能做什么 |
| --- | --- |
| ChatGPT、Codex 与支持 MCP 的助手 | 读取课题概览、讨论研究问题、保存结论，让下一次对话接着工作 |
| Zotero 与文献检索来源 | 查找和筛选论文，整理阅读笔记，把证据关联到研究问题 |
| Codex、Claude、Gemini 与兼容接口的模型服务 | 在各自完成配置后，辅助开发，或对同一组材料开展证据评审并保留分歧 |
| Word，以及 LaTeX / BibTeX、Quarto 等论文写作工具 | 整理论文引用和参考文献，让读者找到依据；Word 使用本机 Zotero 插件 |
| Git（代码修改记录工具）、本地电脑和远程工作区 | 保存代码修改记录，知道每一步研究用了哪个版本，方便继续或回查 |
| MLflow（实验记录工具）、Prefect（任务安排工具） | 在完成配置后集中查看实验结果，按预先设定并获批准的步骤执行任务 |

### 从一个问题开始，逐步形成可追溯的成果

- **让课题有连续的记忆。** 保存目标、已知事实、假设、证据、未解决的问题和下一步，减少反复向助手交代背景。
- **让阅读留下依据。** 将检索、筛选、阅读和引用连接起来，区分论文原文、你的批注与 AI 的推断。
- **让方案经得起追问。** 让已配置的模型审阅同一组材料，记录不同意见，帮助你判断还缺少什么证据。
- **让工作过程可回看。** 将代码、任务、批准和结果关联起来；保存课题历史，并按需备份和恢复。

例如，你可以先建立“可重复使用包装”课题，逐步整理相关文献、记录争议、比较研究方案，最后把选定证据带入文稿。每一步都可以单独开始，再逐渐接入更多工具。

### 出差在外，也能用手机推进科研

通过**手机上的 ChatGPT 应用连接自己的电脑**，你可以在外出时继续已有任务：请助手整理材料、处理获准的研究工作、汇报进展，再把结论保存回同一个 OpenSci 课题。计算和文件处理在连接的电脑上进行，你在手机上安排工作、查看结果并处理必要的确认。

这为远程科研自动化提供了入口。电脑需要保持在线，所用文献、模型和执行工具需要事先配置。OpenSci 的实验批准规则仍然有效；内置实验执行器目前提供一个公开估计量比较示例，接入专业科学软件或 GPU 任务需要进一步开发。手机使用步骤见[中文手册](DOCUMENTATION.zh-CN.md#mobile-research)，宿主能力见 [OpenAI 手机使用指南](https://learn.chatgpt.com/docs/mobile)。

### 按自己的资源继续扩展

你可以先只用一台电脑保存课题，再接入已有的 Zotero 文献库、模型账户、研究代码和服务器。模型服务、计算设备与存储位置由你选择；需要额外安装或账户权限的部分，在手册中分别说明。

对于现有接口支持的资源，完成配置即可使用；新的科学软件、数据来源或执行方式，可以由开发者通过适配器扩展。适配器就是连接新工具的一小层程序。专业软件仍需要各自的安装、许可和结果核验。

课题记录由你自己的协调端保存，也就是负责保存正式记录的那台电脑及其数据目录。调用外部 AI 或服务时，所选服务会处理相应任务内容；具体数据流见[隐私说明](PRIVACY.md)。

### 从这里开始

**第一次使用**：打开[中文使用手册](DOCUMENTATION.zh-CN.md#beginner-start)，先完成“建立一个课题并保存一次进展”，再选择需要的功能。安装要求、配置文件、操作步骤和常见问题都在手册中。

[中文离线手册](OpenSci-Manual.zh-CN.html) · [完整功能目录](DOCUMENTATION.zh-CN.md#feature-catalog) · [扩展开发指南（英文）](docs/DEVELOPMENT.md) · [MIT 开源许可证](LICENSE)

---

<a id="english"></a>
## English

**Bring your AI assistants, literature and computers together in a research workspace that keeps a study moving forward.**

A research idea may begin in a conversation, its papers live in Zotero, its code runs on a computer or server, and its results end up somewhere else. OpenSci connects that work around a shared Study: the question, evidence, decisions and next steps remain available when you return in another conversation or on another device.

### Built around tools you already use

OpenSci runs on Python and uses MCP—the Model Context Protocol—to let assistants work with connected research tools. Add the integrations you need as your work grows.

| Tools and resources | What they bring to your workflow |
| --- | --- |
| ChatGPT, Codex and MCP-compatible assistants | Read a Study Overview, discuss questions and save conclusions for the next conversation |
| Zotero and literature sources | Find and screen papers, organize reading notes and connect evidence to a research question |
| Codex, Claude, Gemini and compatible model services | Support development or review the same supplied evidence, retaining disagreements; each service needs its own setup |
| Word and paper-writing tools such as LaTeX / BibTeX and Quarto | Organize citations and reference lists so readers can find the evidence; Word uses the local Zotero plugin |
| Git (code change history), local computers and remote workspaces | Save code changes and connect each research step to the version used, making work easier to resume or check |
| MLflow (experiment records) and Prefect (task scheduling) | Once configured, view experiment results in one place and carry out steps that were set up and approved in advance |

### Turn a question into a traceable body of work

- **Keep a study's working memory.** Save goals, facts, hypotheses, evidence, open questions and next steps, so you spend less time rebuilding context.
- **Keep the evidence behind your reading.** Connect discovery, screening, reading and citation while distinguishing source text, your annotations and AI inferences.
- **Give research plans a closer review.** Ask configured models to examine the same materials, retain their disagreements and identify missing evidence.
- **Keep a history you can revisit.** Link code, tasks, approvals and results; preserve Study history and use backup and recovery when needed.

For example, start a Study on reusable packaging, gather relevant papers, record disagreements, compare proposed methods and carry the selected evidence into a manuscript. Begin with one step and add tools as you need them.

### Continue research from your phone

Connect the **ChatGPT mobile app to your own computer** to continue tasks while traveling. Ask the assistant to organize materials, carry out authorized research work, report progress and save conclusions to the same OpenSci Study. Your computer handles files and computation; your phone lets you direct the work and review results or approval requests.

This provides an entry point for remote research automation. Keep the computer online and configure the tools you intend to use. OpenSci's experiment approval rules still apply. Its supplied runner executes a public estimator comparison; professional scientific software and GPU tasks require further integration. See [Research from Your Phone](docs/MOBILE_RESEARCH.md) and the [OpenAI mobile guide](https://learn.chatgpt.com/docs/mobile).

### Grow it around your own resources

Start with one computer and a Study, then connect your existing Zotero library, model accounts, research code and servers. Choose the services, hardware and storage that suit your work. The handbook explains the installation and account requirements for each integration.

Resources supported by an existing interface can be configured directly. Developers can add adapters—small programs connecting another tool—for new scientific software, data sources or execution methods. Those tools still need their own installation, licenses and result validation.

Your coordinator, the computer and data folder responsible for the official records, stores your Study history. External AI and service calls let the selected services process the task content. See [Privacy](PRIVACY.md) for the data flows.

### Get started

**First time here?** Follow [Getting Started](docs/GETTING_STARTED.md) to create a Study and save your first progress note, then add the features you need. The [handbook](DOCUMENTATION.md) covers requirements, configuration, operations and troubleshooting.

[English offline handbook](OpenSci-Manual.html) · [Full feature catalog](FEATURES.md) · [Extension guide](docs/DEVELOPMENT.md) · [MIT license](LICENSE)
