<!-- handbook-ui
{
  "guides": "完整手册",
  "references": "技术参考",
  "source": "维护源文档",
  "contents": "章节目录",
  "back": "返回顶部",
  "title": "OpenSci 使用维护与开发手册",
  "navigation": "文档导航",
  "icon": "OpenSci 图标",
  "brand": "使用 · 维护 · 扩展 · 升级",
  "menu": "目录",
  "search": "搜索",
  "placeholder": "关键词 · Ctrl K",
  "clear": "清空",
  "print": "打印",
  "hero": "离线中文手册",
  "description": "从第一次使用到日常维护、扩展开发和版本升级。",
  "code": "代码",
  "docs": "文档",
  "sources": "份维护源文档",
  "results": "搜索结果",
  "footer": "由 Markdown 生成，更新时请编辑维护源文档。",
  "fingerprint": "构建源摘要 SHA-256",
  "all": "全部 {count} 份文档",
  "matches": "匹配 {hits} 个小节，来自 {count} 份文档",
  "no_matches": "没有找到匹配项，请尝试更短的词或文件名。",
  "limit": "显示前 80 个结果，请增加关键词缩小范围。"
}
-->

# OpenSci 用户与维护手册

适用版本：**OpenSci 1.1.0**。文档日期：**2026-10-15**。

这本手册从第一次安装开始，说明在哪里操作、需要填写什么、完成后会看到什么。先做完下面的入门流程，再选择需要的文献、助手或手机功能。项目的整体介绍见 [README](README.md#chinese)。打开 `OpenSci-Manual.zh-CN.html` 可离线阅读和搜索，英文版为 `OpenSci-Manual.html`。

<a id="beginner-start"></a>
## 零基础开始：建立课题并保存一次进展

第一次只完成一件事：**建立一个课题，保存一条进展，再把它读出来。** 此时只需一台 Windows 电脑、Python 和 OpenSci 文件。模型账户、Git、Zotero 和服务器可以以后按需添加。若已经有人替你配置好，确认记录保存位置后，从第 4 步开始。

“课题（Study）”就是一个研究问题的记录本，用来保存目标、证据、决定和下一步。OpenSci 菜单负责保存记录；需要自然语言对话时，再接入 ChatGPT、Codex 等助手。

### 第 1 步：分开存放软件和研究记录

打开 [OpenSci 下载页](https://github.com/yanboyang97/OpenSci/releases)，展开 1.1.0 版本下的 **Assets（下载文件）**，选择完整运行包 **OpenSci-1.1.0.zip**。带 Plugin 或 MCP 名称的包用于后续助手接入。把运行包解压到一个新文件夹。本手册用 `C:\OpenSci` 举例；打开后应能看到 `Start-OpenSci.cmd`、`config` 和 `scripts`。如果它们还在下一层文件夹内，以那一层作为安装目录。

另建 `C:\OpenSci-Data` 保存研究记录，再在其中新建 `config` 文件夹。没有 C 盘写入权限时，可以选其他可写位置，并把后文的路径一致替换。已有课题目录应继续保留，不要覆盖。

| 示例文件夹 | 用途 |
| --- | --- |
| `C:\OpenSci` | 软件、配置样例和手册 |
| `C:\OpenSci-Data` | 你自己的正式课题记录和本地设置 |

负责保存正式记录的电脑称为“协调端”。第一次使用时，它就是当前这台电脑。同一课题只使用一份正式记录目录。

### 第 2 步：安装或找到 Python

Python 是运行 OpenSci 的程序。若未安装，从 [Python 官方网站](https://www.python.org/downloads/windows/)安装 **3.10 或更新版本**；安装器提供“添加到 PATH”选项时将其勾选，这样命令窗口可以找到 Python。

点击 Windows 开始菜单，搜索并打开 **PowerShell**。它是输入命令的窗口。分别粘贴下面两行，每行按一次 Enter：

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

第一行应显示 Python 3.10 或更高版本。第二行会显示 `python.exe` 的完整位置，复制这个位置，下一步要用。如果打开了商店或提示找不到命令，把 `python` 换成 `py -3` 再执行；两个命令都找不到时，先完成安装并重新打开 PowerShell。

在添加本地设置之前，核对刚解压的软件包：

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
python -B verify_delivery.py
```

如果前面使用的是 `py -3`，这里改用 `py -3 -B verify_delivery.py`。成功时显示 `Verified exact delivery file set`。Git 工作副本加上 `--installed`，允许存在 Git 自身的文件。若文件不匹配，先重新取得完整包或核对差异，不要删除自己的数据来消除报错。

### 第 3 步：准备三个设置文件

在 Windows 11 的文件资源管理器中，依次点击 **查看 → 显示 → 文件扩展名**；Windows 10 则在 **查看** 选项卡勾选 **文件扩展名**。确认复制后的设置文件以 `.json` 结尾，没有多出的 `.txt`；界面不同时可参照 [微软扩展名说明](https://support.microsoft.com/en-us/windows/experience/storage-filemanagement/common-file-name-extensions-in-windows)。复制后用记事本编辑，保存为 UTF-8。JSON 是一种文本设置格式，请保留示例中的括号、逗号和英文双引号。

**记录设置。** 把 `C:\OpenSci\config\hub.study.example.json` 复制到 `C:\OpenSci-Data\config\hub.local.json`，内容不变。这份样例支持从空白讨论课题开始。

**记录位置。** 把 `C:\OpenSci\config\studies.example.json` 复制为同目录的 `studies.local.json`，内容改为：

```json
{
  "schema_version": 1,
  "coordinator_root": "C:/OpenSci-Data"
}
```

**Python 位置。** 把 `C:\OpenSci\config\runtime.example.json` 复制为同目录的 `runtime.local.json`。使用下面的内容，把 `python` 的值换成第 2 步显示的真实位置。这里用正斜杠 `/`，不必处理反斜杠转义。

```json
{
  "schema_version": 1,
  "python": "C:/Tools/Python/python.exe",
  "git": "",
  "powershell": ""
}
```

`C:/Tools/Python/python.exe` 只是示例，必须替换成自己电脑上的实际位置。第一次使用时，后两项保持空字符串即可。`.local.json` 文件属于本机配置，里面的个人路径和凭据不要提交到公开仓库。

### 第 4 步：新建自己的课题

双击 `C:\OpenSci\Start-OpenSci.cmd`。菜单使用英文名称，输入数字后按 Enter。

1. 输入 `1`（Browse Studies，浏览课题）。新安装时没有课题是正常的。
2. 输入 `2`（Create Study，新建课题）。
3. 出现 `Study ID` 时，输入一个新编号，例如 `STUDY-001`。编号为 3–48 个大写字母、数字或连字符，并以字母开头。
4. 出现 `Research goal` 时，写下自己的研究问题，例如“梳理可重复使用包装的研究证据”。

成功后会显示课题编号、目标和包含 `committed: true` 的保存回执。回执中的 `request_id` 是这次操作的编号，请保留。若课题编号已存在，打开原课题继续使用，不要重复创建。

### 第 5 步：保存第一条进展

输入 `11`（Save Discussion Progress，保存讨论进展），再输入同一个课题编号。按提示填写：

每次保存都会**替换当前进展摘要和全部五个列表**。以后再次保存前，先用菜单 `10` 读取现有进展，把仍需保留的内容一并写入。列表留空表示清空当前列表，不是保留旧值。较早版本仍在历史中，读取方法见[进展与历史](#saved-progress)。

| 屏幕提示 | 含义 | 示例 |
| --- | --- | --- |
| Saved summary | 当前进展概括，包括仍需保留的早期要点，必填 | 已确定第一阶段的研究问题 |
| Decisions | 已经做出的决定 | 先做文献整理 |
| Hypotheses | 尚需证据支持的假设 | 没有则直接按 Enter |
| Evidence refs | 真实来源或文献条目的引用 | 没有则直接按 Enter |
| Open questions | 还没有解决的问题 | 应选择什么比较方法？ |
| Next steps | 下一步做什么 | 选出第一批阅读文献 |

看到保存回执后，输入 `10`（Study Overview，课题概览）和课题编号。概览中出现刚才保存的内容，就完成了基础使用。输入 `0` 退出菜单，记录会继续保存在数据目录中。

### 第 6 步：只添加现在需要的功能

先选择一个备份位置，再把课题用于持续研究。想用 AI 对话，接着看[助手接入](#assistant-setup)；想使用自己的论文，看[文献工作台](#literature-workspace)；想出门后继续工作，看[手机科研](#mobile-research)。全部软件要求集中在[依赖说明](#requirements)，可以按需安装。

如果以后需要把实验与源码版本关联，请按[登记研究源码的新课题示例](#source-study)操作。现有讨论课题仍可继续使用；当前没有把它直接转换为源码课题的操作入口，不要手动改写记录。

### 第一次打开遇到问题

| 现象 | 处理方法 |
| --- | --- |
| 窗口一闪而过 | 在 PowerShell 先输入 `Set-Location -LiteralPath 'C:\OpenSci'`，再输入 `.\Start-OpenSci.cmd`，保留窗口中的错误信息 |
| 提示需要 Python 3.10+ | 重做第 2 步，核对 `runtime.local.json` 中的完整解释器位置 |
| 提示记录目录不存在 | 核对 `studies.local.json` 与实际创建的 `C:\OpenSci-Data` 是否一致 |
| 提示缺少工作区配置 | 核对文件是否确实叫 `C:\OpenSci-Data\config\hub.local.json` |
| 提示 JSON 无法读取 | 核对英文双引号、逗号、UTF-8 编码，以及文件没有多出 `.txt` 后缀 |
| 提示 Git 文件不存在 | 初次讨论课题可以将 `git` 保持为空，不要保留不存在的示例路径 |
| 不确定是否保存成功 | 保留原 `request_id`，按[保存失败后的恢复步骤](#save-recovery)查询原回执后再决定是否重试 |

Linux 用户使用 Python 3.10+，在自己的可写数据目录建立 `config/hub.local.json`，内容来自同一份 `hub.study.example.json`。在软件目录运行 `python3 -B scripts/hub.py --coordinator-root /home/researcher/OpenSci-Data menu`，把示例账户和目录替换为实际值，再使用相同菜单。Linux 不使用 Windows 的 `runtime.local.json`。

<a id="mobile-research"></a>
## 出差在外：通过手机 ChatGPT 连接电脑

手机负责发出要求、查看进展和处理必要确认；连接的电脑负责运行任务、读取已有材料并使用 OpenSci。可以接续既有任务、整理文献、处理获准的研究工作，再把成果保存到同一个课题。

### 在电脑上完成一次连接设置

先在电脑上完成前面的基础设置，建立自己的课题，并按[助手接入](#assistant-setup)配置 OpenSci Study，或让电脑上的任务使用已经配置好的 OpenSci 命令入口。所需的 Zotero、模型或研究软件也在电脑上配置。

在桌面应用设置中打开 **Connections → Control this Mac or PC**，选择 **Set up** 或 **Add**，按提示用手机扫码并确认设备连接。手机与电脑使用同一个 ChatGPT 账户和工作区。随后在手机 ChatGPT 的 **Codex** 入口中选择电脑和对应项目；若应用仍显示 **Remote**，使用该入口。保持电脑开机、联网且不休眠。平台当前文档以 iOS 为例，客户端范围以 [OpenAI 手机使用指南](https://learn.chatgpt.com/docs/mobile)及[远程连接说明](https://learn.chatgpt.com/docs/remote-connections)为准。

这项设备连接由宿主应用提供，OpenSci 负责课题记录和科研工具。OpenSci 本发行物的入门操作以 Windows 为例；宿主支持连接 Mac 不等于 OpenSci 已完成 macOS 适配。

### 日常使用：打开任务，然后说清楚要做什么

在手机上打开电脑中的已有任务，或在对应项目中开始任务。例如：

> 继续 OpenSci 中的 STUDY-001 课题。先读取最新目标和进展，整理还没解决的问题，并建议下一步。

已经配置文献库后，可以继续说：

> 比较这个课题已关联 Zotero 集合中我选定论文的摘要，列出一致和分歧之处，附上条目引用。没有读到的材料明确标注。

需要保留成果时，说：

> 把刚才的结论、未解决的问题和下一步保存到这个 OpenSci 课题，返回保存回执和更新后的修订号。

把 `STUDY-001` 替换成自己的编号。完整聊天仍保存在 ChatGPT；正式科研进展保存在 OpenSci，之后在其他已授权会话里也能继续。

### 自动化工作的范围

助手可以在已有权限与配置范围内处理任务，你在手机上安排工作和查看结果。长任务保留原任务或作业编号，断线后继续查看同一个任务。手机断网不表示电脑任务已经停止，聊天中出现文字也不等于课题已经保存。

手机连接不会自动创建计划任务或批准实验。OpenSci 的实验仍需要独立人工批准；内置执行器目前提供公开估计量比较示例，使用一个 CPU 线程，不使用 GPU。专业科学软件需要相应适配与资源设置。

若只想在普通 Chat 中调用课题工具，可以配置[私有 MCP 连接](#assistant-setup)。这条连接提供有范围限制的课题操作，不会单独赋予整个电脑的文件、桌面或命令访问权；它与手机接续电脑任务分别设置。

<a id="requirements"></a>
## 软件安装与最低要求

基础课题讨论、概览、进展保存和 MCP 只需要 **Python 3.10+** 及其标准库 SQLite，不要求 GPU、Node.js、Docker、模型账户或数据库服务。Windows 菜单要求 Windows PowerShell **5.1+**；Claude 开发启动器另需 PowerShell **7.0+**。Windows 10 或提供 Python 3.10 的受维护 Linux 可运行基础功能；Ubuntu 22.04 是 Linux 基线。实验提交使用 Linux 或 WSL 2，macOS 未纳入本发行物的验收范围。

| 软件或依赖 | 本发行物要求的最低版本或能力 | 使用范围 |
| --- | --- | --- |
| Git | **2.28**，支持文档中的 `git init -b` | 研究源码依据、仓库安装、源码备份；普通讨论不要求 |
| OpenSSH | 支持固定命令、主机密钥校验、`ExitOnForwardFailure`；未确立数字最低版本 | 远程工作区或 MCP，按实际环境验证 |
| WSL | **WSL 2** | 需要在 Windows 上使用 Linux 时选装 |
| Zotero | **10.0**，Local API **3** 和 `Zotero-Server-ID` | 文献库读取、写入和实例绑定 |
| Edge / Chrome、Zotero Connector | 浏览器当前 Stable 或 Extended Stable，匹配的当前 Connector | 浏览器辅助采集；厂商采用更新渠道要求 |
| Word 桌面版、Zotero Word 插件 | Windows Word **2010+**，不含 Starter，兼容的原生插件 | 此为 Zotero 的兼容下限；还需可观察的本机编辑会话，不能用 Word 网页版代替 |
| PyMuPDF | **1.24 ≤ 版本 < 2** | PDF 文本提取，不包含 OCR |
| MLflow | **3.0 ≤ 版本 < 4** | 实验追踪，可选 |
| Prefect | **3.0 ≤ 版本 < 4** | 工作流调度，可选 |
| Google Gen AI SDK | **1.40 ≤ 版本 < 2** | Gemini 评审，使用 Client 上下文管理接口 |
| Codex CLI | **0.162.1** 为本发行物支持基线，支持 `exec`、`--ephemeral`、`--ignore-user-config`、JSON 事件和 `--output-last-message`；更早版本未纳入本发行物支持范围 | 可选证据评审 |
| Claude Code | 原生 CLI，支持 `--bare`、工具限制、会话持久化开关、轮数/预算限制及 JSON 输出；未确立数字最低版本 | 可选开发和评审 |
| Secure MCP Tunnel 客户端 | **0.0.16** 启动器兼容基线，或兼容的新版本 | 普通 Chat 访问私有协调端，另需账户资格与权限 |
| ChatGPT 手机与桌面应用 | 提供远程电脑访问的受支持版本，未确立数字最低版本 | 手机连接电脑接续任务，见[手机科研](#mobile-research) |
| ChatGPT / Codex 宿主 | 本机 stdio MCP；普通 Chat 需自定义私有连接与隧道能力；未确立数字最低版本 | 助手接入 |
| LaTeX / Quarto | 可编译目标文稿的 LaTeX 引擎与 BibTeX，或 Quarto；未确立数字最低版本 | 仅编译导出文稿需要；书目导出本身不需要 |
| markdown-it-py | 固定 **4.0.0** | 重建离线手册；阅读 HTML 不需要安装 |

这些数值是本发行物的依赖下限，不表示所有组合均已实测；客户端没有明确最低版本时，按必需能力核对 `--help`，不要猜版本号。完整官方下载入口和依据见 [Installation and Requirements](docs/INSTALLATION.md)。Python 从 python.org 或系统包管理器安装；可选包在独立虚拟环境中按 `requirements-optional.txt` 选择安装。文档构建依赖单独列在 `requirements-docs.txt`。DVC 仅由使用它的研究项目自行选择，并非 OpenSci 运行依赖。

### 按使用范围继续配置

基础设置见[零基础开始](#beginner-start)。接入助手、文献、模型和远程设备时，分别完成相应章节的账户、权限、预算与备份设置。安装某个软件不会自动批准费用或实验。

<a id="assistant-setup"></a>
## 助手接入：ChatGPT、Codex 与 Claude 系列

本章帮助你让助手读取课题概览，并在你要求时保存进展。覆盖 **ChatGPT、Codex、Claude Desktop 和 Claude Code**。MCP 是让助手连接工具的协议；OpenSci 的本机服务是 `scripts/hub_mcp.py`，**OpenSci Study** 插件为兼容的插件客户端打包了这个服务。安装连接不等于建立课题，也不提供账号、隧道或凭据。

### 选择适合自己的入口

| 使用位置 | Windows | macOS / Linux |
| --- | --- | --- |
| 浏览器中的 ChatGPT | 私有 Secure MCP Tunnel，使用随包的 Windows 启动器 | 在 OpenSci 所在电脑运行官方隧道客户端 |
| 电脑上的 Codex | 直接配置本机 MCP，或使用兼容的 OpenSci 插件 | 相同 MCP 配置，换成本机 Python 和路径 |
| Claude Desktop | 本机 MCP 配置 | macOS 本机 MCP；Linux 桌面当前为 beta，有 Developer 设置时按该入口配置 |
| Claude Code | 从 Windows 终端注册本机 stdio MCP | 相同命令，换成本机 Python 和路径 |

这是可采用的接入路线，不表示每个操作系统上的完整科研流程都已实测通过。Claude 当前桌面支持范围见[官方安装说明](https://support.claude.com/en/articles/10065433-install-claude-desktop)。连接必须运行在实际能访问记录的电脑/进程中；Windows 路径不能直接用在 WSL 或云端容器。Zotero 留在协调器所在电脑，不转发其本机端口。手机接续电脑任务另见[手机科研](#mobile-research)。

<a id="connection-prerequisites"></a>
### 第 1 步：准备并选择一个课题

先完成[零基础开始](#beginner-start)，建立课题并在本机确认能读到概览。准备 Python 3.10+ 和完整 OpenSci 软件目录；直接 MCP 不需要额外的 MCP SDK 或 Python 包。记下以下四个值：

| 要填写的值 | Windows 入门示例 | 去哪里取得自己的值 |
| --- | --- | --- |
| Python 程序 | `C:/Tools/Python/python.exe` | 软件 `config/runtime.local.json` 中的 `python`；macOS/Linux 用 `command -v python3` 查找并核对版本 |
| 软件目录 | `C:/OpenSci` | 包含 `scripts/hub_mcp.py` 的目录 |
| 记录目录 | `C:/OpenSci-Data` | 你选择的、包含 `config/hub.local.json` 和已保存课题的目录 |
| 课题编号 | `STUDY-001` | 创建或列出课题时显示的编号 |

macOS 可使用自己的 `/Users/yourname/OpenSci`、`/Users/yourname/OpenSci-Data`，Linux 可使用 `/home/yourname/OpenSci`、`/home/yourname/OpenSci-Data`。必须换掉 `yourname` 和所有示例路径，填写真实绝对路径。JSON/TOML 参数中不要使用 `~` 或命令行变量，它们不会自动展开。

把软件中的 `config/mcp.unselected.example.json` 复制到记录目录的 `config/mcp.policy.local.json`，用文本编辑器打开，将 `connection_id` 换成唯一名称，如 `opensci-codex-01`，暂时保留其他字段。它是连接身份名称，不是密码。接入第二个客户端时，使用**另一份策略和另一个连接名称**，如 `mcp.claude.local.json` / `opensci-claude-01`，后续命令也改用那个策略路径。各客户端指向同一份权威记录，不分别复制课题。

选择课题前先停止对应连接；第一次配置时尚未运行，可以直接操作。在 PowerShell 中执行：

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
$OpenSciPython = (Get-Content -LiteralPath '.\config\runtime.local.json' -Raw -Encoding UTF8 | ConvertFrom-Json).python
& $OpenSciPython -E -s -B scripts/select_study_connection.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json --study-id STUDY-001 --connection-stopped
```

macOS/Linux 从软件目录执行，替换成本机实际路径：

```bash
/usr/bin/python3 -E -s -B scripts/select_study_connection.py --coordinator-root /home/yourname/OpenSci-Data --policy /home/yourname/OpenSci-Data/config/mcp.policy.local.json --study-id STUDY-001 --connection-stopped
```

出现 `Study selected.` 表示选择已保存。这同时启用该连接获准的助手写入；只想阅读时，在启动前把策略中的 `allow_write` 改回 `false`。首次读取保持 `allow_remote_checks: false`。没有可信宿主绑定时，身份/项目上下文保持 unknown，不能用模型名称推断项目身份。

<a id="direct-mcp-installation"></a>
### 第 2A 步：Codex 直接连接本机服务

同一客户端在直接连接和下方插件方式中选择一种，避免重复工具使用不同连接身份。

Codex 默认在 `~/.codex/config.toml` 保存 MCP 设置，Windows 对应 `%USERPROFILE%\.codex\config.toml`；自定义过 Codex 主目录时使用实际生效文件。先备份，只合并下面这一段并保留其他设置。名称已存在时核对原条目，不重复添加。[官方 MCP 配置说明](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

```toml
[mcp_servers.opensci]
command = 'C:/Tools/Python/python.exe'
args = ['-E', '-s', '-B', 'C:/OpenSci/scripts/hub_mcp.py', '--coordinator-root', 'C:/OpenSci-Data', '--policy', 'C:/OpenSci-Data/config/mcp.policy.local.json']
cwd = 'C:/OpenSci'
startup_timeout_sec = 20
tool_timeout_sec = 60
enabled = true
```

把程序和路径换成第 1 步确认的值。macOS/Linux 要把所有路径（包括 `cwd`）换成本机绝对路径；可复用 [mcp.desktop.example.toml](config/mcp.desktop.example.toml)。

重启本机客户端/服务，开始新对话。Codex CLI 中执行 `codex mcp list`，进入 Codex 后用 `/mcp` 查看连接。桌面宿主如提供“Settings → MCP servers”，可在该处添加相同 STDIO 程序/参数并重启。然后完成下方统一验收；列表中有配置不等于已经读取成功，本机配置也不会自动接通云端对话。

#### 可选：安装 OpenSci Study 插件

仅用于支持 OpenAI 插件格式的客户端。仓库根目录包含 `plugin.json`、`mcp.json`、图标和服务源码，`.agents/plugins/marketplace.json` 指向该目录。宿主环境需能以 `python` 启动 Python；需要使用 Python 完整路径时，采用上面的直接 MCP。

Windows 按 Windows+R 输入 `%LOCALAPPDATA%`，在打开位置创建 `OpenSci` 文件夹，把软件的 `config/plugin.connection.example.json` 复制进去并命名为 `connection.json`。macOS/Linux 的 OpenSci 入口脚本读取 `~/.config/opensci/connection.json`；也可在宿主进程用 `OPENSCI_CONNECTION_FILE` 指定绝对路径。填写实际值：

```json
{"schema_version":1,"coordinator_root":"C:/OpenSci-Data","policy":"C:/OpenSci-Data/config/mcp.policy.local.json"}
```

保存 UTF-8，避免额外 `.txt` 后缀。由操作者维护，放在插件缓存之外；缺失或无效时插件停止启动。兼容的 Codex CLI 可执行 `codex plugin marketplace add yanboyang97/OpenSci`，再在所装版本支持时执行 `codex plugin add opensci-study@opensci`；兼容桌面市场也可从仓库选择并安装 **OpenSci Study**。没有对应命令/界面时用直接 MCP，并参考[当前插件指南](https://developers.openai.com/plugins/build/plugins)。安装后开启新对话。GitHub 下载不表示已经上架公共目录或配置了托管服务。

<a id="claude-desktop"></a>
### 第 2B 步：Claude Desktop 添加本机 MCP

1. 安装并登录对应系统的 Claude Desktop。进入应用的 **Settings → Developer → Edit Config**。Windows 文件为 `%APPDATA%\Claude\claude_desktop_config.json`，macOS 为 `~/Library/Application Support/Claude/claude_desktop_config.json`。Linux beta 使用应用实际打开的文件，不猜测其保存位置。受管理设置隐藏入口时，请管理员确认，或使用被允许安装的 Claude Code。[官方本机服务教程](https://modelcontextprotocol.io/docs/develop/connect-local-servers)
2. 备份文件，把下面的 `opensci-study` 合并到已有 `mcpServers` 中，保留其他条目。空文件可使用完整示例。策略路径使用为此客户端单独准备的那一份。

```json
{
  "mcpServers": {
    "opensci-study": {
      "command": "C:/Tools/Python/python.exe",
      "args": ["-E", "-s", "-B", "C:/OpenSci/scripts/hub_mcp.py", "--coordinator-root", "C:/OpenSci-Data", "--policy", "C:/OpenSci-Data/config/mcp.policy.local.json"]
    }
  }
}
```

3. 所有路径都换成第 1 步实际值；macOS/Linux 使用本机 Python、软件、记录和策略绝对路径。Windows 的 JSON 路径可使用正斜线，不加入注释或末尾多余逗号。完全退出并重开 Claude Desktop，在 **Connectors / Manage connectors** 和 Developer 状态中检查 `opensci-study`。
4. 开始对话，按需启用这个连接器，再做统一验收。OpenSci ZIP 不是 Claude 的 `.mcpb` 桌面扩展，不从扩展安装器导入；这份本机配置也不会单独连接 Claude 网页或手机端。

<a id="claude-code"></a>
### 第 2C 步：Claude Code 注册本机启动命令

在能够访问记录的环境安装并登录 Claude Code。Windows PowerShell 使用以下命令，路径换成自己的实际值：

```powershell
claude mcp add --transport stdio --scope user opensci-study -- C:/Tools/Python/python.exe -E -s -B C:/OpenSci/scripts/hub_mcp.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json
claude mcp get opensci-study
```

macOS/Linux 使用：

```bash
claude mcp add --transport stdio --scope user opensci-study -- /usr/bin/python3 -E -s -B /home/yourname/OpenSci/scripts/hub_mcp.py --coordinator-root /home/yourname/OpenSci-Data --policy /home/yourname/OpenSci-Data/config/mcp.policy.local.json
claude mcp get opensci-study
```

替换第 1 步的全部路径和此客户端专用策略；带空格的路径用引号包为一个参数。`--scope user` 表示只为本用户注册，不发布项目配置；`--` 将 Claude 的参数与 OpenSci 的参数隔开。启动 Claude Code，用 `/mcp` 检查，再完成统一验收。以后移除这项注册可用 `claude mcp remove opensci-study --scope user`，不会删除 OpenSci 记录。[Claude Code MCP 命令说明](https://code.claude.com/docs/en/mcp)

<a id="ordinary-chat"></a>
### 第 2D 步：ChatGPT 连接自己的私有隧道

浏览器里的 ChatGPT 不能直接启动本机 Python。需要在 OpenSci 所在电脑运行官方 Secure MCP Tunnel 客户端，并使用单独选好课题的策略。准备目标 Platform 组织与 ChatGPT 工作区的访问权限：创建隧道需要 **Tunnels Read + Manage**，运行密钥及连接操作者需要 **Read + Use**；隧道除所属组织外，还要关联目标 ChatGPT 工作区。[官方隧道设置](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

#### 生成隧道启动配置

打开 [Platform 隧道设置](https://platform.openai.com/settings/organization/tunnels)，创建或选择自己的私有隧道，记下 `tunnel_id` 和组织编号。从该页或其指向的官方发行页下载对应操作系统的客户端，保存在选定目录，核对官方来源及提供的校验信息，并查看 `help quickstart`。OpenSci 不附带分发该客户端。

Windows 示例将客户端放在 `C:\Tools\tunnel-client\tunnel-client.exe`：

```powershell
& 'C:\Tools\tunnel-client\tunnel-client.exe' help quickstart
& 'C:\Tools\tunnel-client\tunnel-client.exe' init --sample sample_mcp_stdio_local --profile opensci-chat --tunnel-id YOUR_TUNNEL_ID --mcp-command 'C:/Tools/Python/python.exe -E -s -B C:/OpenSci/scripts/hub_mcp.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json'
```

替换隧道编号和全部路径；路径有空格时按客户端帮助保留必要引号。记下生成结果中的 **profile 实际绝对文件路径**。profile 是告诉隧道如何启动 OpenSci 的本机配置，不要假定生成文件必定叫 `chat.local.yaml`。

macOS/Linux 用官方本机客户端的绝对路径执行同样的 `init` 参数，并换成本机 Python、服务、记录、策略路径；`--mcp-command` 的内容仍作为一整段带引号的命令。若初始化要求凭据，按下方临时进程环境方式在本机输入，不把密钥原文放进命令历史或 profile。

#### Windows 启动

把软件 `config/chat.example.json` 复制为软件 `config/chat.local.json`，填写：

| 字段 | 如何填写 |
| --- | --- |
| `client` | 下载的程序绝对路径 |
| `client_sha256` | 核对下载来源后，用 `Get-FileHash -Algorithm SHA256` 取得的程序摘要 |
| `profile` | 刚生成的实际 profile 路径 |
| `organization_id` | 目标 Platform 组织编号 |
| `pid_file`、`health_file`、`log_file` | 私有目录中的独立文件，如 `C:/OpenSci-Data/connection/`；先创建父目录 |

示例程序的完整摘要命令为 `(Get-FileHash -LiteralPath 'C:\Tools\tunnel-client\tunnel-client.exe' -Algorithm SHA256).Hash.ToLowerInvariant()`，把返回值复制到 `client_sha256`。

查看所装客户端的帮助，核对支持 `Start-Study-Chat.ps1` 使用的参数，尤其是 `--profile-file`、`--mcp.stdio-send-initialized-notification` 以及 PID/健康/日志参数。版本不兼容时不要绕过启动器检查。

先用 `doctor --profile opensci-chat --explain` 检查 profile。需要运行密钥时，以下 PowerShell 写法隐藏输入，并在退出时清除临时环境变量：

```powershell
if (Test-Path Env:CONTROL_PLANE_API_KEY) { throw 'Use a fresh terminal without an existing tunnel key.' }
$OpenSciSecret = Read-Host 'Tunnel runtime key' -AsSecureString
try {
    $env:CONTROL_PLANE_API_KEY = [System.Net.NetworkCredential]::new('', $OpenSciSecret).Password
    & 'C:\Tools\tunnel-client\tunnel-client.exe' doctor --profile opensci-chat --explain
} finally {
    Remove-Item Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
    $OpenSciSecret.Dispose()
}
```

若初始化也需要密钥，把审阅过的 `init` 命令放在同一 `try` 内、`doctor` 之前执行。单次使用时双击 `Start-Study-Chat.cmd`，在隐藏提示中输入受限运行密钥并保持窗口打开；若希望记住密钥并在后台连接，请按下面的可选配置操作。在 `health_file` 写出的本机健康地址查看就绪状态。

#### macOS/Linux 启动

打开交互式 **Bash** 终端，当前是其他 shell 时先输入 `bash`。下例假设本机客户端为 `/home/yourname/Tools/tunnel-client`，执行前替换路径和编号：

```bash
if [ -n "${CONTROL_PLANE_API_KEY+x}" ]; then
  printf '%s\n' 'Use a fresh terminal without an existing tunnel key.'
else
  read -r -s -p 'Tunnel runtime key: ' CONTROL_PLANE_API_KEY
  printf '\n'
  export CONTROL_PLANE_API_KEY
  trap 'unset CONTROL_PLANE_API_KEY' EXIT
  if /home/yourname/Tools/tunnel-client doctor --profile opensci-chat --explain; then
    /home/yourname/Tools/tunnel-client run --profile opensci-chat --control-plane.organization-id YOUR_ORGANIZATION_ID --mcp.stdio-send-initialized-notification
  fi
  unset CONTROL_PLANE_API_KEY
  trap - EXIT
fi
```

先核对所装客户端帮助，只有 `doctor` 成功才继续运行。若 `init` 需要密钥，在 `export` 之后、`doctor` 之前执行审阅过的初始化。一个隧道只运行一个客户端，保持终端和电脑不休眠，结束时 Ctrl+C 停止。中断后确认密钥变量已清除，或关闭这个专用终端。

#### 加入 ChatGPT，完成一次实际工具调用

在 ChatGPT **Plugins** 中选择 **+ → Add custom MCP server**，把 **Connection** 设为 **Tunnel**，选中或粘贴同一隧道编号，完成所需认证和风险确认，创建私有插件；工作区策略可能限制此入口。[自定义 MCP 设置说明](https://developers.openai.com/api/docs/guides/custom-mcp-server)

发现工具时保持隧道健康。在新对话中启用/选择插件，再完成下面验收。找不到隧道时核对工作区关联及 Read + Use 权限。电脑休眠或客户端停止会使实时调用不可用，但不会清除已保存课题。服务更新后刷新插件工具。当前连接用于私有单用户，不作为共享托管服务发布。

<a id="connection-acceptance"></a>
### 可选：加密记住密钥，登录后在后台连接（Windows）

OpenSci 1.1.0 新增此可选方式；原来的单次输入方式仍可使用。这里的 API Key（服务访问密钥）用于连接隧道，与调用模型的密钥分开。Windows DPAPI 是 Windows 为当前登录账户加密数据的功能。OpenSci 不在本机生成有效的 OpenAI 密钥，也不能延长平台设置的有效期。

1. 先完成上面的隧道和 `config/chat.local.json` 设置。旧连接窗口中按 **Ctrl+C** 停止连接，同一隧道只保留一个客户端。
2. 打开 [OpenAI 隧道设置](https://platform.openai.com/settings/organization/tunnels)，在隧道所属组织中，按[官方说明](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)创建一把专用的受限密钥，仅授予 **Tunnels Read + Use（读取和使用隧道）**。选择账户允许的较长有效期；只有平台确实提供时才能选择不过期。没有相应权限或选项时联系组织管理员，不要用权限更大的模型或管理员密钥替代。
3. 在文件资源管理器打开 OpenSci 安装目录，双击 **Manage-Study-Connection.cmd**，输入 **1**。把密钥粘贴到弹出窗口的密码输入框中，只需这一次。不要发到聊天、命令或 JSON 文件里。可在有效期栏填写平台显示的到期日，格式为 `2027-10-15`；不填并不代表密钥不会过期。
4. 如果希望登录 Windows 后自动连接，勾选 **Start automatically after I sign in to Windows**，再点 **Save encrypted and connect（加密保存并连接）**。密钥密文保存在 `%LOCALAPPDATA%\OpenSci\connections\<连接编号>\credential.dpapi`，文件夹仅授予当前账户和 Windows 系统账户权限。自启动条目仅包含程序路径，没有密钥。
5. 回到管理菜单，输入 **2 Status（状态）**。稍等后应看到 `stored_key`、`worker_running`、`client_running`、`ready` 都是 `true`；选择自动启动时 `start_at_sign_in` 也应为 `true`。随后请 ChatGPT 读取已选课题的概览，确认真实工具调用成功。仅显示连接健康还不等于整个 ChatGPT 接入已经通过。
6. 现在可以关闭设置和菜单窗口，连接仍在后台运行。以后登录 Windows 会按选项自动启动；未勾选时，双击 **Start-Study-Chat.cmd** 也无需再次输入密钥。电脑必须保持联网、唤醒且账户处于登录状态。锁屏不等于退出登录；关机、退出登录或休眠后不能继续提供实时服务。

管理菜单 **3** 启动、**4** 停止当前连接、**5** 取消登录自启动、**6** 停止并取消自启动且删除本地保存的密钥。**4** 不取消下次登录时启动的设置，**5** 不停止已经在运行的连接。密钥到期或被撤销时，在平台创建新的受限密钥，再通过 **1** 替换，验证成功后撤销旧密钥。

误关菜单窗口时先看 **2**，仍在运行就无需重开连接；已停止则用 **3**。不要因此重建隧道或课题。保存时断线且没有成功回执，应恢复同一连接并查询原请求回执，确认后再决定是否重试，不要直接换请求编号重复提交。

软件会核验客户端摘要，并把密钥绑定到当前配置路径、组织、客户端摘要和连接配置文件摘要。原位置升级 OpenSci 会保留这些设置；更换客户端、连接配置文件或安装位置后，需要核对并重新保存密钥。临时网络恢复由官方客户端处理；客户端退出后，后台程序最多尝试启动五次，之后标记 `attention_required`，请检查网络、权限、有效期和本机日志。不要启用原始 HTTP 日志或公开分享包含秘密的日志。

同一 Windows 账户下的其他程序以及被入侵的管理员账户仍可能取得密钥，系统加密不是账户内部的隔离边界。密文文件通常不能直接搬到另一台电脑或另一 Windows 账户使用，应通过密码管理器的安全恢复方式或重新签发密钥恢复连接。此功能不安装系统服务，也不会为 Linux 自动安装常驻服务。


### 第 3 步：在任何客户端完成读取、保存与恢复验收

1. 请助手：“先读取 OpenSci 连接能力，解析已选课题，再读概览，告诉我课题编号和目标，暂时不要保存。”对应工具为 `opensci_get_capabilities`、`opensci_resolve_study_link`、`opensci_get_study_brief`；助手按实际返回的工具参数调用。核对编号确实是你选的课题。
2. 想测试保存时，再说：“把连接检查完成、下一步检查已选论文记为进展，保留已有进展，并返回已提交回执。”提交前检查拟保存的完整进展快照；结构化进展会替换上一份快照，聊天答复本身不是保存。
3. 核对 `committed: true`，保留请求编号/修订号，再读概览确认。只读策略会按设计拒绝第 2 步。写入超时时，保持同一连接身份查询原请求，按[回执恢复](#save-recovery)处理，不因丢失响应另造替代写入。

| 情况 | 最小检查步骤 |
| --- | --- |
| 没有 OpenSci 工具 | 核对本机客户端/宿主、完整服务目录、程序和路径、JSON/TOML 格式并重启 |
| `selection_required` | 停止连接，在它实际使用的策略中选择课题，再启动 |
| 读到错误课题 | 立即停止并纠正策略选择，先不要保存 |
| 能读但不能保存 | 核对 `allow_write`、课题和该操作授权，不扩大其他权限 |
| 不允许远程分析 | 确实需要时才核对 `allow_remote_checks` 和现有执行端设置 |
| 隧道健康但 ChatGPT 找不到 | 核对组织/工作区关联、连接权限及隧道编号 |
| Word 或浏览器工作不可用 | MCP 不附带这些软件或桌面控制，分别完成对应设置 |

切换课题时先停止该客户端/服务和隧道，按第 1 步选择新课题，再启动。撤销选择时，在停止状态把 `--study-id STUDY-001` 换成 `--clear`。策略在进程启动时确定，编辑运行中的文件不会重新加载权限；移除客户端连接也不会删除课题记录。

### 已有远程电脑的接入

已经配置远程协调器时，可用 [mcp.remote.example.toml](config/mcp.remote.example.toml)，由服务端强制固定 SSH 命令。无法向协调器发起入站 SSH 时，按现有[SSH 反向连接说明](docs/STUDY_CONNECTION.md#remote-access-when-the-coordinator-is-a-local-computer)设置。回环网关不是 HTTP MCP 地址，不能公开网关或 Zotero 端口。新建账号、主机密钥和远程部署属于另一项工作，不由选择上面的客户端自动完成。

## 进阶：工作区与命令

### 了解部署角色

**协调端**（Coordinator）是正式课题记录的唯一写入者。**开发工作区**（Development Workspace）保存用于开发和检查的源码；配置字段 `active_agent` 指向它。**执行节点**（Execution Node）由独立人工提交者运行经批准的实验。三个角色可以位于同一硬件，但账户、路径、权限和凭据应分别核验。选择开发工作区不会改变执行节点或移动运行中的实验。

文档使用 `C:\OpenSci` 和 `/home/researcher/OpenSci` 作为示例路径。真实账号、SSH 别名和工具路径以忽略的本地配置为准。不要把开发副本启用为同一课题的第二个协调端。

<a id="git-prerequisites"></a>
### 建立源码基线

如果尚未建立 Git 基线，由操作者确认真实提交姓名、邮箱和仓库来源，在项目范围配置身份，审查待提交内容，再创建首个提交。不要提交本机配置、凭据、正式记录和实验产物，也不要擅自假定操作者身份。

涉及源码的工作流要求两份源码来自**同一 Git 历史的同一干净提交**。采用独立记录目录后，软件安装目录与协调端不再充当研究源码；源码依据单独记录在课题中。在两端各自提交相同文件不满足这个条件。通过已授权的仓库、克隆或 Git bundle 传递同一提交；已有目录先核对，不能盲目覆盖。如果配置了 `origin`，两端 URL 拼写必须一致，因为系统比较其摘要。

<a id="command-context"></a>
### 命令示例的运行环境

日常使用优先选择菜单。需要执行后面的命令时，Windows 用户先把以下完整内容粘贴到同一个 PowerShell 窗口。它使用本副本配置的 Python 和 Git，在每次调用后恢复当前目录与 PATH，不修改个人 Profile。路径不同则先修改 `$OpenSciRoot`。

```powershell
function Invoke-OpenSci {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    $OpenSciRoot = 'C:\OpenSci'
    $OpenSciRuntime = Get-Content -LiteralPath "$OpenSciRoot\config\runtime.local.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $OpenSciPreviousPath = $env:PATH
    $OpenSciPreviousLocation = Get-Location
    try {
        if ($OpenSciRuntime.git) { $env:PATH = (Split-Path -Parent $OpenSciRuntime.git) + [IO.Path]::PathSeparator + $OpenSciPreviousPath }
        Set-Location -LiteralPath $OpenSciRoot
        & $OpenSciRuntime.python -B -X utf8 @Arguments
        if ($LASTEXITCODE -ne 0) { throw "OpenSci exited with code $LASTEXITCODE" }
    } finally {
        $env:PATH = $OpenSciPreviousPath
        Set-Location -LiteralPath $OpenSciPreviousLocation.Path
    }
}
Invoke-OpenSci -Arguments @('scripts/hub.py', '--coordinator-root', 'C:/OpenSci-Data', 'list')
```

例如，读取已有课题使用 `Invoke-OpenSci -Arguments @('scripts/hub.py', '--coordinator-root', 'C:/OpenSci-Data', 'show', '--study', 'STUDY-001')`。后文的 `python -B scripts/...` 是通用命令形式：Windows 将脚本路径与后续参数逐项放入该函数的参数数组；Linux 在实际项目目录使用配置的解释器，例如 `/usr/bin/python3 -B`。`STUDY-001` 是示例，必须替换为已经创建的课题编号。读取列表或查看手册不会创建这个示例课题。

## 日常课题工作

### 菜单与正式功能

| 菜单 | 中文含义 | 作用 |
| --- | --- | --- |
| 1 Browse Studies | 浏览课题 | 读取本地课题记录 |
| 2 Create Study | 新建课题 | 经操作服务创建并返回可恢复的回执 |
| 3 Resume Study | 继续课题 | 核对开发工作区与已记录源码 |
| 4 Choose Development Workspace | 选择开发工作区 | 检查并切换研究开发所用工作区 |
| 5 Choose Execution Node | 选择执行节点 | 指定后续任务的执行节点 |
| 6 Check Development Environment | 检查开发环境 | 检查所选课题的开发工作区，不是首次安装向导 |
| 7 Preview Evidence Review | 预览证据评审 | 展示输入、模型、限制和计划摘要 |
| 8 Record Progress | 记录进展 | 经源码核对后登记阶段和笔记 |
| 9 Literature Workspace | 文献工作台 | 输入 `capabilities` 检查能力，或执行已准备的请求文件 |
| 10 Study Overview | 课题概览 | 有界读取目标、进展、证据与下一步 |
| 11 Save Discussion Progress | 保存讨论进展 | 无需 Git，保存结论、假设和待办 |
| 0 Exit | 退出 | 关闭菜单 |

课题编号由 3–48 个大写字母、数字或连字符组成，并以大写字母开头。新建时输入目标；新建、切换和记录进展前保存菜单显示的请求编号。工作区、节点和阶段会列出可选项，输入序号或对应编号，留空取消。新课题自动使用操作服务，无需选择记录模式。菜单 2 可建立不关联源码的讨论课题；命令行 `hub.py init` 用于关联研究源码的课题，需要先完成源码设置。当前课题的切换、进展和材料登记命令也通过操作服务更新。可用 `--request-id` 指定固定编号，未指定时会在写入前输出生成的编号；保留它与原参数用于恢复。

研究阶段依次表达证据整理、方案评审、实现、等待批准、实验进行中、分析、归档；对应字段值为 `evidence`、`plan_review`、`implementation`、`awaiting_approval`、`experiment_running`、`analysis`、`archived`。它们是人工规划标签，软件会校验阶段转换条件，但标签本身不能证明实验完成。

### 接续与记录进展

开始时核对目标、修订号、最近笔记、开发工作区、源码提交、缺失材料及全部运行编号。`show`、`history` 和 `brief` 读取协调端记录；无源码课题的 `resume` 只恢复讨论上下文；有源码课题会探测配置的开发工作区。菜单在连接前询问，明确调用远程检查命令则代表请求进行该检查。

```text
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data show --study STUDY-001
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data history --study STUDY-001 --limit 20
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001
```

上面的 `hub_command.py brief` 与菜单 10 一样，包含保存的结构化讨论进展，适合讨论交接。另一个命令 `hub.py brief` 显示检查点笔记（`checkpoint_note`）、阶段建议和运行信息，不包含菜单 11 保存的进展。概览是带时间戳的已保存快照，不会自动保存为文件、发送到另一段对话或查询节点实时状态；需要文件时明确保存输出。

<a id="saved-progress"></a>
涉及源码的检查点先审查、验证、提交并核对同一来源。普通讨论或文献研究可直接用菜单 11 或 `save_progress` 保存，不以 Git 为前提。每次保存替换当前摘要和全部五个列表，应先读旧内容并保留仍然有效的部分；菜单中每个列表只接受一项文字，留空会清空该列表。需要保留多项独立条目时，通过已连接助手或操作服务提交结构化列表。普通文字笔记可通过 `note` 写入，不探测开发工作区；`checkpoint` 校验涉及源码的阶段变更。

概览出现 `has_more: true`，表示部分完整字段因篇幅限制未显示。可在软件目录运行 `python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data show --study STUDY-001` 读取完整记录，其中 `project.project.progress.content` 是当前进展；Windows 用户通过前面的命令辅助函数传入这些参数。也可让已连接助手按 `detail_refs` 的修订号调用 `opensci_get_study_detail`。需要找回较早进展时，用上面的 `history` 命令找到修订号，再让助手读取该修订的 `field: progress`，按 `next_offset` 继续读取，直到它为 null。核对恢复内容后再保存为新版本，不直接修改历史文件。结束前用概览及必要细节交接当前进展，并核对原运行编号和状态。

### 自动化请求与回执

操作服务要求唯一请求编号和最新课题修订号。新建请求的期望修订号为 0。将实际请求保存为 `config/command.local.json`，不要在菜单创建同一课题后重复执行这个示例。

```json
{
  "schema_version": 1,
  "request_id": "STUDY-001-INIT-001",
  "study_id": "STUDY-001",
  "expected_revision": 0,
  "operation": "create_study",
  "arguments": {"goal": "Define the question and acceptance criteria", "research_workspace": null, "binding": null}
}
```

```text
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data execute --request config/command.local.json
python -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data receipt --study STUDY-001 --request-id STUDY-001-INIT-001
```

请求上限为 64,000 个 UTF-8 字节，编号和内容不得擅自复用。身份和角色由受信入口提供，不能由请求自报。写入请求的 `committed=true` 表示操作已经登记；`false` 表示明确未提交；`null` 表示结果未知。只读响应同时出现 `read_only=true`、`committed=false` 属于正常情况，表示没有请求更新课题；是否连接成功应查看各项能力状态。结果未知时保留原编号、内容、身份和角色，查询原回执，再用完全相同的请求恢复。不能换新编号猜测重试。

操作服务提供 `init`、`note`、`checkpoint`、`select_agent`、`select_compute`、`attach` 等操作；内部 `observe` 只供运行监测使用。完整字段契约见 [INTEGRATION.md](INTEGRATION.md)。附加材料先放在 `coordination/imports/`，用可信的原始 SHA-256 关联；任务先于其批准与运行登记。

<a id="source-study"></a>
### 创建时登记研究源码

需要源码依据的检查点或实验，应使用创建时已登记源码的新课题。保留原讨论课题，当前没有为已有课题追加或替换研究目录的受支持操作。先完成[源码准备](#git-prerequisites)：研究目录必须位于协调端这台电脑、能够访问、已有经过审查的 Git 提交且没有未提交改动；普通文件夹不能建立源码依据。

把以下内容另存为 UTF-8 文件 `C:\OpenSci\config\source-study.local.json`。换成未使用的课题编号和请求编号、自己的研究目标，并把 `C:/Research/MyStudy` 改成真实研究仓库路径。`host_id: local` 表示协调端本机，`additional` 保持空列表以使用当前支持的单仓库流程，`binding: null` 表示暂不关联助手原生项目。

```json
{
  "schema_version": 1,
  "request_id": "STUDY-CODE-001-INIT-001",
  "study_id": "STUDY-CODE-001",
  "expected_revision": 0,
  "operation": "create_study",
  "arguments": {
    "goal": "Test the reviewed research method",
    "research_workspace": {"primary": {"host_id": "local", "path": "C:/Research/MyStudy"}, "additional": []},
    "binding": null
  }
}
```

先在 PowerShell 加载[命令辅助函数](#command-context)，再在同一窗口执行：

```powershell
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'execute', '--request', 'config/source-study.local.json')
Invoke-OpenSci -Arguments @('scripts/hub.py', '--coordinator-root', 'C:/OpenSci-Data', 'show', '--study', 'STUDY-CODE-001')
```

成功时回执显示 `committed: true`，记录中的 `research_workspace.primary.path` 是实际研究目录，`anchor.commit` 对应已审查的 Git 提交。保留请求文件和回执；结果未知时按[保存恢复](#save-recovery)处理。创建记录不会自动配置开发工作区、执行节点或批准实验，后续源码操作仍须满足相应前提。

<a id="literature-workspace"></a>
## 文献工作台：从第一篇论文到论文引用

本教程带你完成“找到论文 → 决定是否入库 → 阅读并留下依据 → 按需分析 → 插入真实引用”。Zotero 保存文献、附件和个人笔记；OpenSci 保存课题采用过哪些材料、筛选理由和处理结果。检索先产生候选，确认收集后才写入文献库。

第一次使用先完成[连接和读取](#literature-first-paper)，随后按需进入[检索入库](#literature-search)、[阅读整理](#literature-evidence)、[分析任务](#literature-analysis)、[论文引用](#literature-writing)和[恢复](#literature-recovery)。每一步完成后都可以停下。

### 开始前准备

先完成[零基础开始](#beginner-start)，建立一个课题。仅讨论和整理文献不要求 Git、远程电脑或付费模型服务。以下假设软件在 `C:\OpenSci`、记录在 `C:\OpenSci-Data`、课题编号为 `STUDY-001`；请全部换成自己的实际值。macOS/Linux 使用本机绝对路径和 Python 3.10+；Windows 启动器及原生 Word 操作需分别满足其环境条件。

在保存记录的电脑上打开 Zotero 10，在“我的文库”中准备一篇已有论文和一个愿意试用的小集合，并保留 Zotero 与 OpenSci 各自的备份。当前不支持群组文库。需要通过助手操作时先完成[助手接入](#assistant-setup)；也可以直接使用下面的请求文件步骤。

<a id="literature-first-paper"></a>
### 第 1 步：连接 Zotero，读到一篇已有论文

1. 在 Zotero 的“设置 → 高级”中，启用“允许此计算机上的其他程序与 Zotero 通信”，并保持 Zotero 打开。这是本机连接，不是 Zotero 网站密码。[Zotero 本机接口说明](https://www.zotero.org/support/dev/web_api/v3/local_api)
2. 打开 OpenSci 菜单，选 **9 Literature Workspace**，输入 `capabilities`。查看返回的 `result.zotero`，应有 `read: available`、`api_version: 3` 和 `instance_id`。复制实际 `instance_id`，它标识这份文献库。这里的 `read_only: true`、`committed: false` 是正常的只读检查结果；浏览器、Word、检索来源和模型仍可能显示未验证。
3. **仅第一次配置时**，把软件中的 `config/literature.example.json` 复制到 `C:\OpenSci-Data\config\literature.local.json`。目标文件已存在时不要覆盖，按[设置更新](#literature-settings)处理。用文本编辑器打开副本，找到 `zotero` 对象，仅把这个对象替换为下列内容；将 `INSTANCE_FROM_CAPABILITIES` 换成上一步实际值，保留示例中的其他设置。保存为 UTF-8，文件名不要多出 `.txt`。

```json
{
  "base_url": "http://127.0.0.1:23119",
  "binding_id": "personal-library",
  "instance_id": "INSTANCE_FROM_CAPABILITIES",
  "user_id": null,
  "credential_ref": null,
  "allow_authorization_prompt": false,
  "allowed_operations": []
}
```

`personal-library` 是你为这个库起的固定名称；实例编号来自 Zotero。尚未核对个人条目返回的数字 `library.id` 时，`user_id` 保持 `null`。23119 端口只供本机使用，不转发到其他电脑。出现不同实例时，先对账，不能直接用新编号覆盖旧绑定。

4. 按下面的请求方法，用 `literature.search_library` 搜索那篇论文题名中的词。在 `result.items` 中核对题名，复制对应 `key`（8 位大写字母或数字）。这是论文条目编号，不是 PDF 附件编号，也不是 DOI。
5. 使用 `literature.get`，其 `payload` 为 `{"item_key":"ABCD1234"}`，将示例编号替换成实际值。返回预期题名的条目，就完成了第一次读取；此时不需要 Zotero 写入权限。

#### 请求怎么提交，结果怎么看

已经接入助手时，可以说：“读取已选课题，在我的本机 Zotero 文库中查找题名含 reusable food packaging 的论文，列出匹配题名和条目编号，先不要修改文库。”助手使用的仍是下列操作；需要变更时先核对它提出的目标。菜单本身没有自然语言模型或可视化设置编辑器。

手动操作时，在 PowerShell 中进入软件目录，读取课题当前修订号：

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
$OpenSciPython = (Get-Content -LiteralPath '.\config\runtime.local.json' -Raw -Encoding UTF8 | ConvertFrom-Json).python
& $OpenSciPython -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data show --study STUDY-001
```

把返回的 `cursor.revision` 整数填入 `expected_revision`。将下面完整请求保存为 `C:\OpenSci-Data\config\literature-request.local.json`，换成实际题名、课题编号和修订号：

```json
{
  "schema_version": 1,
  "request_id": "LIT-LOCAL-001",
  "study_id": "STUDY-001",
  "expected_revision": 1,
  "operation": "literature.search_library",
  "arguments": {"payload": {"query": "reusable food packaging", "limit": 10}}
}
```

执行这个文件：

```powershell
& $OpenSciPython -B scripts/hub_command.py --coordinator-root C:/OpenSci-Data execute --request C:/OpenSci-Data/config/literature-request.local.json
```

也可以在菜单 **9** 输入同一个**绝对文件路径**。菜单从记录目录解析相对路径，命令行从当前目录解析；使用绝对路径可避免两者差异。菜单 9 只接受 `literature.*` 请求。

macOS/Linux 从软件目录调用本机 Python，例如 `/usr/bin/python3 -B scripts/hub_command.py --coordinator-root /home/researcher/OpenSci-Data ...`，将 `...` 换成上面的 `show` 或 `execute` 参数，记录目录和请求文件也换成本机实际绝对路径。用 `command -v python3` 查找 Python，并确认版本为 3.10+。

下文只列操作名称及 `payload` 时，保留这六个外层字段，替换 `operation` 和 `arguments.payload` 内部对象。每个新动作使用新的 `request_id`，每次变更前重新读取课题修订号。保留原请求原文用于恢复，不把单独的 `payload` 当成完整请求提交。

只读操作的数据在 `result` 中。变更操作返回提交回执及文献结果引用；需要看详细结果时，再提交一个 `literature.get` 只读请求，`payload` 为 `{"request_id":"THE_ORIGINAL_CHANGE_REQUEST_ID"}`，填入刚才变更的原请求编号。从详细结果中复制真实的 `run_id`、`snapshot_id`、`job_id` 或 `task_id` 供下一步使用。课题已提交回执只证明记下了这次操作；其中某篇论文或外部步骤仍可能处于部分完成、等待或失败状态。

<a id="literature-settings"></a>
### 第 2 步：选择权限，把论文关联到课题

#### 已有设置如何更新

把记录目录中的 `config/literature.local.json` 另存一份工作副本，记下原 `revision`，只修改需要的设置，再把 `revision` 加 1。通过操作者身份提交 `literature.config_update`；其 `payload` 包含 `expected_config_revision`（原配置修订号）和 `config`（**修改后的完整配置**，不是几个变更字段）。外层 `expected_revision` 仍是课题修订号，这两个编号不要混用。完成后读回结果和配置文件；编号过期就重新读取核对，不能直接覆盖。助手不能给自己增加这些权限。

需要收集论文或添加笔记时，将 `allow_authorization_prompt` 设为 `true`，在 `allowed_operations` 中只选择需要的操作：`create` 用于新条目、笔记和附件，`update` 用于添加标签、集合归属。首次写入时 Zotero 会弹出本机授权对话框，由你选择是否允许。如明确希望在 Windows 保留授权，可设置 `credential_ref: "wincred:OpenSci/Zotero/personal"` 并同意保留；一次性授权不会持久保存。其他系统可使用本机提示或由操作者提供的环境变量引用。密钥原文不写进请求、配置或聊天。`delete` 与 `annotation` 是另外的权限，以下常规步骤不需要它们。

如果要让助手为指定论文建立阅读快照，把空的 `grants` 对象替换为下面这种小范围授权，换成实际课题和条目编号：

```json
{
  "STUDY-001": {
    "operations": ["literature.bind_study", "literature.read", "literature.export"],
    "item_keys": ["ABCD1234"],
    "collection_keys": [],
    "manuscript_paths": []
  }
}
```

这是 `grants` 的值，不是整个配置文件。只在同意相应工作时加入操作、条目、集合或稿件路径；MCP 策略也要允许写入。这里限制的是委托变更与快照目标，不能把不需认证的 Zotero 本机读取接口视为文库隔离机制。

#### 关联并记录筛选理由

使用 `literature.bind_study`：

```json
{
  "config_mode": "inherit",
  "collection_refs": [],
  "item_refs": [{"binding_id": "personal-library", "item_key": "ABCD1234"}],
  "item_links": {"ABCD1234": {"status": "included", "reason": "Relevant to the packaging question; full text still needs checking"}}
}
```

`inherit` 让新任务采用当前研究设置；`pinned` 固定一份设置副本，二者都不能越过当前权限和预算。`included`、`excluded`、`undecided` 分别表示纳入、排除、待定，理由属于这个课题。后续绑定会替换本课题的条目/集合引用列表，请保留仍需使用的关联。读回结果，核对编号和理由。

需要关联集合时，先取得它的 8 位编号，再把 `{"binding_id":"personal-library","collection_key":"COLL1234"}` 放进 `collection_refs`。下面的 Windows 只读命令列出前 20 个集合：

```powershell
(Invoke-RestMethod -Uri 'http://127.0.0.1:23119/api/users/0/collections?limit=20&start=0' -Headers @{'Zotero-API-Version'='3'; 'Zotero-Allowed-Request'='1'}) | Select-Object key, @{Name='name'; Expression={$_.data.name}}
```

macOS/Linux 使用 `curl -H 'Zotero-API-Version: 3' -H 'Zotero-Allowed-Request: 1' 'http://127.0.0.1:23119/api/users/0/collections?limit=20&start=0'`，核对每项 `key` 与 `data.name`。后续页把 `start` 换成 20、40 等。请求头适配 Zotero 10 的浏览器请求保护。[Zotero 10 本机接口变更](https://www.zotero.org/support/dev/zotero_10_for_developers)

通过助手读取已绑定集合时，除集合编号外，还要明确授权其中**每篇实际读取的论文编号**；集合新增论文可能需要更新授权。集合改名不改变编号；集合被删除则需人工核对替代目标。

<a id="literature-search"></a>
### 第 3 步：检索、筛选，再决定入库

#### 先检索一个来源

先说明问题、日期/类型限制、来源和停止条件。例如：“在 PubMed 查找最多 10 篇可重复使用食品包装相关论文，先展示相关性、文献类型和缺失信息，不要入库。”使用 `literature.search`：

```json
{"intent":"Find evidence about reusable food packaging","queries":{"pubmed":"reusable food packaging"},"limit":10}
```

用 `literature.get` 读取详细结果，保留 `run_id`，核对每个来源的实际查询、返回范围、状态和候选，记下选中论文的 `candidate_id`。前 10 条只是一次有限检索，不代表完整系统综述。要接续同一检索，在请求中加入 `resume_run`，填前一次 `run_id`，保留原查询/设置并检查新范围。

| 来源编号 | 需要准备什么 | 直接检索不可用时 |
| --- | --- | --- |
| `pubmed` | 能访问 PubMed 的文献信息接口 | 保留错误，恢复网络后继续原定检索 |
| `web_of_science` | 获授权的 Starter API 凭据 | 在网站人工筛选，导出原生引文 |
| `scopus` | 获授权的 Scopus API 凭据 | 在网站筛选后导出 |
| `ieee` | 获授权的 IEEE Xplore API 凭据 | 在网站筛选后导出 |
| `google_scholar` | 浏览器与必要的人工交互 | 导出已选择的条目；OpenSci 不提供通用批量接口 |

来源凭据使用 `env:SCOPUS_API_KEY` 这样的引用，由操作者提供给运行进程；机构网站登录不等于获得 API 凭据。来源、研究方向和 Edge/Chrome 选择放在记录目录的设置中；两个浏览器分别需要 Connector 和访问核验。仅增加来源名称不会产生新适配器。

使用浏览器导出时，先发起包含该来源的检索，让 OpenSci 留下查询记录。在来源网站筛选，导出 RIS 或 BibTeX，打开下载的文本。提交 `literature.search_import`，填写原 `search_run`、对应 `source_id`、`format`（`ris` 或 `bibtex`）、导出原文 `text`、来源页面的 HTTPS `source_url`，以及说明已选范围和未检索部分的 `coverage_note`。可让助手把文本整理为正确转义的 JSON 字符串，提交前核对引号和换行。完整请求不得超过 64,000 字节，大文件分成可追溯的小批次。导入后收集时使用**新返回的** `run_id`；导出导入仍属于部分覆盖，也不会自动写入 Zotero。

#### 只收集确认过的候选

确认题名、标识和目标集合后，使用 `literature.collect`：

```json
{"search_run":"RUN_ID_FROM_RESULT","candidate_ids":["CANDIDATE_ID_FROM_RESULT"],"collection_keys":["COLL1234"],"tags":["packaging-screening"]}
```

全部示例值换成真实结果；让助手执行前授权这项操作和目标集合。查看逐项回执，并到 Zotero 的目标集合确认。明确匹配的已有记录可能被复用；疑似重复会等待复核。文献信息、全文和阅读状态分别记录，不因某篇或某个 PDF 失败而丢弃其他成功记录。

为一个已有条目补充可公开取得的 PDF，可用 `literature.fetch_fulltext`，`payload` 为 `{"item_keys":["ABCD1234"],"url":"https://publisher.example/paper.pdf"}`，将 URL 换成实际获准使用的 PDF。也可以删除 `url`，改为真实文章的 `pmcid: "PMC1234567"`。两种方式只能选一种。登录页、摘要页或订阅阻挡不是 PDF；需要浏览器权限时，按自己的合法访问途径取得附件并放入 Zotero，再重新读取。结果未知时不要反复点击浏览器保存。

<a id="literature-evidence"></a>
### 第 4 步：阅读、做笔记、核对证据

对选中的论文使用 `literature.read`：

```json
{"level":"regular","item_keys":["ABCD1234"],"index":true}
```

这一步把材料保存为 OpenSci 的证据快照，本身不调用模型写摘要，也不在 Zotero 中自动划线。读回结果，保留 `snapshot_id`，先看材料覆盖和失败项再下结论。

要打开保存的材料，在 `C:\OpenSci-Data\coordination\literature\` 下找到返回的 `manifest` 路径，例如 `snapshots/ACTUAL_SNAPSHOT_ID/manifest.json`。其中列出的文件路径相对于这份快照目录，包括各论文的 `metadata.json`、笔记及实际提取到的附件文本。只打开清单中确实存在的文件，缺失全文不会自动补齐。另获本机文件读取权限的助手可以读取这些文件；仅通过 OpenSci MCP 接入的聊天拿到的是结果位置和覆盖情况，并没有任意文件读取工具或完整快照正文。需要在该聊天中讨论时，由你提供选定材料，或使用下面已配置的分析任务路线。

| 层级 | 用来做什么 | 仍需核对什么 |
| --- | --- | --- |
| `discovery` | 按题名、文献信息、摘要初筛 | 方法、全文与细节主张 |
| `regular` | 读取可取得的文本、笔记、批注 | 缺失附件、失败页面、图表和扫描内容 |
| `deep` | 为深入证据检查准备材料 | 科学有效性、公式、视觉内容和补充材料；文本提取不能证明这些已核验 |

PDF 文本提取需要[依赖说明](#requirements)中的可选 PyMuPDF；解析器缺失或文本覆盖不足要保留在结果里。查询已明确建立的索引时，用 `literature.search_library`，`payload` 为 `{"query":"packaging","limit":10,"index":true}`。查看新鲜度和快照编号；Zotero 有变更后，为受影响论文重新建立快照，不能把旧命中当成当前证据。

可以这样要求助手阅读：“针对这份快照，分清作者发现、我的笔记和你的解释；每项主张给出条目、实际存在的附件/页码、不确定性和未查看材料。”不能从摘要或缺失文件中猜页码。论文正文也不能授予工具或扩大权限。

需要添加已审阅的笔记时，使用 `literature.organize`：

```json
{"item_keys":["ABCD1234"],"collection_keys":[],"tags":["needs-method-check"],"notes":{"ABCD1234":"Screening note: check the sample size and reuse conditions in the full text before using this result."}}
```

OpenSci 新建带请求标记的子笔记；到 Zotero 核对，并保留原笔记。PDF 新批注需要操作者明确授权和实际位置数据，阅读不会顺带创建批注。新建集合结构也属于操作者操作。跨论文结论保存到课题。

<a id="literature-analysis"></a>
### 第 5 步：按需启动分析任务

你可以先阅读并与选定助手讨论，不启用 OpenSci 的分析任务执行器；助手本身仍按其服务规则计费/计量。要创建可跟踪的分析任务，先按[配置参考](docs/CONFIGURATION.md)配置一个已存在、已启用、通过 SSH 连接且角色为 `agent` 的开发节点。使用节点编号，不是 SSH 主机名。零基础的无节点配置不能派发任务。

使用 `literature.analyze`：

```json
{"snapshot_id":"SNAPSHOT_ID_FROM_RESULT","node_ref":"remote-agent","analysis_kind":"evidence_matrix"}
```

这只创建任务，尚未启动。`evidence_matrix` 生成确定性的、尚未评判证据强弱的表格，不调用模型。读回结果并保留 `job_id`。

若使用 `analysis_kind: model`，先在执行端 `config/providers.local.json` 配置已启用的服务，核对模型、账号和凭据来源，再把文献设置的 `models.provider_ref` 指向该服务条目名称。具体字段见[配置参考](docs/CONFIGURATION.md)，不要假定示例模型名称在自己的账号上可用。`limits` 的**每一个字段**都必须是有限值，`accounting` 还要指定统计周期和累计额度。例如，由你选择并同意金额后，一次小规模试用可采用下列两个对象：

```json
{
  "limits":{"max_requests":1,"max_tokens":4000,"max_cost_usd":1.0,"concurrency":1,"node_concurrency":1,"model_concurrency":1,"study_concurrency":1},
  "accounting":{"period_id":"trial-01","max_requests":1,"max_tokens":4000,"max_cost_usd":1.0}
}
```

这只是设置片段，不是完整配置或价格承诺；按第 2 步应用。额度缺失时模型任务停在 `waiting_budget`，不要为了消除提示直接提高预算。费用记录是估计，不是服务商账单。

| 下一步 | 操作和 `payload` | 应检查的结果 |
| --- | --- | --- |
| 启动已准备任务 | `literature.job_dispatch`，`{"job_id":"JOB_ID_FROM_RESULT"}` | 固定执行端接受原任务 |
| 不联系执行端，只查已记录状态 | `literature.job_status`，同一任务编号 | 本地状态，可能尚未更新 |
| 联系执行端查状态 | `literature.job_status`，另加 `"refresh":true` | 当前执行端响应，尚不等于正式导入结果 |
| 登记分析结果 | `literature.job_import`，任务编号 | 核对后的结果关联到原任务/课题 |
| 暂停、恢复、取消 | `literature.job_pause`、`literature.job_resume`、`literature.job_cancel`，任务编号 | 工作进程确认，而不只是“已登记控制请求” |

派发、导入、刷新状态需要可信启动策略允许远程检查。已审阅的命令行请求在 `execute` **之前**加入 `--allow-remote-check`；MCP 则由操作者停止连接后开启策略中的 `allow_remote_checks`，再重启。普通本地阅读保持默认权限。超时后先核对原任务和回执，不新建替代任务猜测结果；未知付费调用会保留预算预留，直到对账完成。

<a id="literature-writing"></a>
### 第 6 步：在论文中使用真实引用

#### LaTeX / BibTeX 与 Quarto

这类工具把文本稿件和书目文件变成排版后的论文。使用 `literature.export`，`payload` 为 `{"snapshot_id":"SNAPSHOT_ID_FROM_RESULT","manuscript_id":"paper-01"}`。同一篇稿件后续保持相同 `manuscript_id`，核对结果中的 `entry_count`、`citation_map` 和引用键冲突。

文件位于 `C:\OpenSci-Data\coordination\literature\exports\paper-01\`：`references.bib`、`sample.tex`、`sample.qmd`。对照 Zotero 检查题名和作者。已有固定引用键保持稳定，映射记录它们对应的真实条目。在 `C:\OpenSci-Data\manuscript\` 下创建工作目录，如 `manuscript/paper-01/`，把需要的示例和书目复制进去。按下文引用示例操作时，将工作稿件命名为 `draft.tex` 或 `draft.qmd`。

在引用位置放一个只出现一次的标记，如 `OPENSCI_CITE_HERE_01`，保存并关闭其他编辑器。Windows 用下面命令取得已保存文件的 SHA-256（用来确认文件没有在操作间被改动）：

```powershell
(Get-FileHash -LiteralPath 'C:\OpenSci-Data\manuscript\paper-01\draft.tex' -Algorithm SHA256).Hash.ToLowerInvariant()
```

macOS 用 `shasum -a 256 /absolute/path/to/draft.tex`，Linux 用 `sha256sum /absolute/path/to/draft.tex`，路径换成自己的稿件，复制返回的 64 位摘要。提交 `literature.cite`：

```json
{"manuscript_id":"paper-01","path":"manuscript/paper-01/draft.tex","expected_sha256":"SAVED_FILE_SHA256","format":"latex","item_refs":[{"binding_id":"personal-library","item_key":"ABCD1234"}],"marker":"OPENSCI_CITE_HERE_01"}
```

Quarto 使用 `.qmd` 路径和 `format: quarto`。助手还需要该精确稿件路径的授权。标记必须只出现一次，文件摘要仍需匹配；结果给出新摘要和恢复副本。再次导出后，把对应 `references.bib` 更新到稿件旁。

已安装所用排版工具后，在工作稿件目录打开终端。LaTeX 示例依次执行 `pdflatex sample.tex`、`bibtex sample`、再执行两次 `pdflatex sample.tex`；Quarto 执行 `quarto render sample.qmd`。重命名过稿件就换成实际文件名。打开生成的 PDF/HTML，处理缺失引用。使用哪一种格式就验证哪一种；导出结果的 `not_compiled` 不代表已经编译通过。

#### Word 与 Zotero 插件

1. 在具备 Word 和 Zotero Word 插件的本机桌面，先在记录目录中创建 `manuscript` 文件夹（如尚不存在），将副本保存为 `C:\OpenSci-Data\manuscript\draft.docx`。在已有引用域之外放置一次 `OPENSCI_CITE_HERE_01`，保存并按上面的方式计算摘要。
2. 用文本示例的字段提交 `literature.cite`，但改为 `path: manuscript/draft.docx`、`format: word`，加入 `phase: prepare`，填写真实条目。读取返回任务并保留 `task_id`；`waiting_local` 表示仍需在 Word 中操作。
3. 你或获授权的桌面助手必须看到实际文档路径和窗口。只选中标记，用 Zotero 的 **Add/Edit Citation**（添加/编辑引文）选择指定真实论文并保存。遇到未保存/并发修改、焦点不清或插件缺失时停止；不能用普通文字冒充动态引用，也不解除引用域。[Zotero Word 插件说明](https://www.zotero.org/support/word_processor_plugin_usage)
4. 重新计算**保存后文件的新摘要**。提交新的 `literature.cite` 请求，保留原稿件、路径、条目和标记，加入原 `task_id`，把 `phase` 改为 `verify`，`expected_sha256` 改为新摘要。返回 `succeeded` 才表示已保存的引用结构和改动范围通过检查。
5. 在副本中测试重新打开、通过 Zotero 编辑引用。书目、刷新或样式变化分别准备和验证独立任务，使用 `native_action: bibliography`、`refresh` 或 `style`；书目/刷新可使用空标记，样式使用已安装样式的 Zotero URL。不要把这些变化合并到一次插入任务中。插件实际操作验收与文件结构验证分别记录。

OpenSci 本身不会打开 Word 或代替用户点击插件。这个流程依赖真实本机桌面会话；连接 ChatGPT、Claude 或 Codex 不会自动授予桌面控制，也不能证明所有操作系统的原生 Word 集成都已验收。

<a id="literature-recovery"></a>
### 第 7 步：遇到问题时恢复，保留已完成部分

| 看到的情况 | 接下来做什么 |
| --- | --- |
| 首次检查显示 `waiting_local`、`local_api_disabled`、`unsupported_version` | 打开 Zotero 10、检查本机通信设置，再做只读检查 |
| `binding_required` / `instance_changed` | 核对实际个人文库；恢复或迁移后先对账身份，再重新绑定 |
| `forbidden` / `authorization_required` | 核对课题选择、助手授权、写入类型和 Zotero 提示，不扩大无关权限 |
| 零条结果与 `permission_denied`、`waiting_user`、`partial` | 区分没有结果和访问未完成；保留来源失败范围，完成获准的浏览器步骤 |
| 文献信息已保存，PDF 或文本缺失 | 保留条目，解决访问/解析覆盖问题，仅补取或重读缺失部分 |
| `version_conflict` | 重新读取发生变化的课题、Zotero 条目或稿件，核对后再提交新请求 |
| 响应丢失或 `outcome_unknown` | 通过原调用身份查询原请求，不能假定外部写入没有发生 |
| `waiting_budget` 或控制请求待确认 | 核对原任务的预算预留或工作进程确认状态，再决定后续动作 |

已完成但部分失败的 `collect`、`organize`、`fetch_fulltext`，通过原调用身份和原课题提交 `literature.reconcile`，`payload` 为 `{"original_request_id":"ORIGINAL_REQUEST_ID"}`。它保留已核实对象并对账不确定操作。若命令本身还没有课题回执，先按[保存恢复](#save-recovery)核对原请求。

替换字段/笔记、移除关系或删除对象，先做 `literature.preview_change`。例如 `{"kind":"items","item_key":"ABCD1234","change":{"action":"update","fields":{"title":"Reviewed corrected title"}}}` 返回旧内容、影响、`preview_id` 和 `digest`。人类检查具体变更后，操作者才以 `{"preview_id":"PREVIEW_ID_FROM_RESULT","confirmed_digest":"DIGEST_FROM_PREVIEW"}` 提交 `literature.apply_change`；期间有人手动修改对象，预览就会失效。重复条目的原生合并在 Zotero 中完成，随后核对存续编号、引用和课题关联。

OpenSci 备份包含自己的回执、快照和稿件，不包含 Zotero 外部数据库、原始附件、浏览器资料或凭据。按自己的 Zotero 备份方案分别备份恢复，先在隔离位置做恢复演练，核对文库身份、引用和未结束任务后再启用唯一协调器。阅读教程或安装源码不代表完成实际部署验收；真实来源权限、浏览器 Connector、PDF/视觉材料覆盖、模型限制、Word/排版工具和独立恢复仍要在使用环境中验证。完整参数见 [LITERATURE.md](LITERATURE.md)。

## 证据评审与实验流程

使用 `literature/evidence_matrix.csv` 记录来源与主张，使用 `methodology/experiment_protocol.md` 明确估计对象、数据、方法、指标、资源和验收标准。协议与源码摘要绑定任务，不得篡改已批准材料来迁就运行结果。

证据评审先生成固定计划，核对材料、模型、端点、轮数、并行量、时限及费用，再显式执行。每次保留相同的规则快照、提示词、原始响应、报告、时间和摘要。模型拒绝、截断、缺少完成证据或材料被改动时停止后续步骤。未知模型版本如实记录为未知；供应商间不自动切换。离线示例评审必须标记为模拟。

实验依次经过：研究计划与证据 → 评审 → 固定源码和执行环境 → 任务草案 → 独立人工批准 → 人工提交执行 → 按原运行编号核验。

1. 在实际 Linux/WSL 执行节点，用将要执行实验的解释器运行 `capture_environment.py --out` 采集环境。
2. `prepare_task.py` 绑定课题、任务、节点、环境、协议、证据和资源限制，只生成任务与 DRAFT 批准模板。
3. 人工在受保护目录制作单独批准文件，填写真实批准人、时区明确的批准和到期时间、理由及 APPROVED 状态，不改变绑定字段。
4. 独立提交账户使用 `run_task.py` 指定任务、批准原文摘要和实际解释器执行。开发助手不能控制批准原文或自行提交。
5. 使用 `inspect_run.py --run` 核对状态、日志、六项必要产物和指标。心跳过期不能单独证明进程已经结束。

源码、规则、解释器、依赖或节点变化后，重新准备适当的任务与批准。新尝试使用新的运行编号，保留逻辑任务与尝试关系；原运行目录不得覆盖。运行器负责超时、信号与子进程组清理；记录失败或清理失败须明确保留，不假报完成。完整可执行参数见 [IMPLEMENTATION.md](IMPLEMENTATION.md)，字段和验证规则见 [RECORDS.md](RECORDS.md)。

实验追踪只上传通过校验的完成产物，使用明确 MLflow 地址和可信状态摘要，指定一个上传者并保留回执。成功上传集合不能代表所有尝试的成功率。工作流调度需要配置明确的 Prefect 工作池、源码快照、任务、批准和 `OPENSCI_EXPERIMENT_PYTHON`；其默认不自动重试，工作池名称也不会扩大执行能力。

## 助手接入与运行监测

助手接入使用 MCP 标准输入输出接口，提供课题、回执、事件和文献读取；受保护策略明确允许时才提供写入工具。默认只读，固定助手角色和允许课题范围。读当前记录 → 提交已授权请求 → 核对回执 → 读取事件，是一致的操作顺序。聊天内容不会自动变成正式记录，聊天赞同不构成人工实验批准。

运行监测读取记录目录中的 `C:/OpenSci-Data/config/observer.local.json`，其中登记固定的本地或只读挂载来源，不自行建立 SSH。它核对原任务、批准、节点、时间、序号和产物，保留已有终态，在冲突时要求对账。新鲜度过期显示 stale，来源缺失显示 unavailable，结构或绑定错误显示 invalid，启动或清理异常需要 reconciliation；这些状态都不能授权重跑。在软件目录运行以下命令，`--workspace` 和 `--sources` 均按实际记录目录填写，工具不会自动读取启动器的 `studies.local.json`。

```text
python -B scripts/observe_runs.py --workspace C:/OpenSci-Data --sources C:/OpenSci-Data/config/observer.local.json
python -B scripts/observe_runs.py --workspace C:/OpenSci-Data --sources C:/OpenSci-Data/config/observer.local.json --watch --interval 30
```

第二条命令在前台持续运行。需要常驻时，由明确配置的服务管理器托管；安装包不会自动启用服务。关闭桌面后的持续运行依赖实际服务部署和验收。助手接入不读取聊天数据库，也不自动向关闭的聊天推送消息。

接口角色不能阻止同一账户绕过接口直接修改文件。应保护正式状态、批准原文、服务源码、解释器导入路径和启动策略。远程受限 MCP 账户需要服务器实际强制固定命令和访问范围，示例配置本身不建立账户隔离。

## 配置与本机工具

下表路径相对于注明的位置。“软件目录”指示例中的 `C:\OpenSci`，“记录目录”指 `C:\OpenSci-Data`。样例文件随软件分发，本地设置应复制到对应组件实际读取的位置。

| 文件 | 放在哪里／如何指定 | 用途 |
| --- | --- | --- |
| `config/runtime.local.json` | 软件目录 | Windows 已安装 Python、Git、PowerShell 的绝对路径 |
| `config/studies.local.json` | 软件目录 | 启动器选择的记录目录 |
| `config/hub.local.json` | 记录目录；也可用 `--config` 明确指定 | 协调端节点目录与默认开发工作区 |
| `config/providers.local.json` | 执行任务的节点；评审用 `--config` 指定，文献工作进程从所选工作区读取 | 模型供应商配置 |
| `config/literature.local.json` | 记录目录 | 个人库绑定、来源、授权、方向和费用限制 |
| `config/command.local.json` | `--request` 指定的位置；本手册命令行示例放在软件目录 | 准备执行的单次请求，不是服务开关 |
| `config/mcp.policy.local.json` | 本手册放在记录目录，以 `--policy` 指定 | 助手接入允许的课题与操作 |
| `config/observer.local.json` | 本手册放在记录目录，以 `--sources` 指定 | 运行监测允许读取的运行来源 |
| `config/device.local.json` | 接受核验的设备，以 `--device` 指定 | 资源编号在本设备的绝对路径 |
| `coordination/resources.json` | `verify_resources.py --manifest` 指定的位置 | 稳定资源身份、版本和文件摘要 |
| `environments/*.local.json` | `capture_environment.py --out` 指定的实际保存位置 | 在实际执行环境采集的记录 |
| `tools/claude-launcher/machine.local.psd1` | 软件目录 | 本副本 Claude 可执行文件和凭据引用 |

备份、运行监测和维护计划的 `--workspace` 应明确指向记录目录，不能在软件目录里用 `.` 代替；这些工具不跟随启动器的记录位置设置。运行脚本仍从软件目录使用[命令辅助函数](#command-context)。

示例文件定义格式，不代表服务已开通。所有路径按实际设备填写，不能将 `~` 或占位符当作绝对路径。节点配置中的能力值是声明，不是实时监测。现有课题会保留工作区配置快照；修改账号、目录、解释器等绑定时使用明确维护流程，不覆盖历史记录。

Windows 选择 Python 的顺序是显式 `-Python`、本地运行配置、PATH 查找。启动器只在进程内临时加入配置的 Git 路径，并在结束时恢复；命令包装器的执行策略设置仅作用于子进程，不修改全局策略。直接运行 Python 示例时，使用实际配置的解释器并确保当前终端可找到 Git。

Claude Code 开发启动器需要 Windows、PowerShell 7 与原生 `claude.exe`。打开项目根目录的 `Start-ClaudeCode.cmd`，在开发启动器菜单选择 Setup 创建本副本映射；已有文件不会覆盖。`-ClaudeProvider deepseek` 或 `kimi` 明确选择供应商。检查与凭据管理只作用于相应本地配置，不改变个人 Profile、其他安装副本或研究执行授权。模型名称和端点以配置文件为准，配置声明不代表服务已验证。Windows 交互开发与自动证据评审的供应商配置各自独立。

## 每次升级前：完整备份与安全升级

**每次升级前，都应备份自己的全部数据并核验备份。** 保留一份在独立设备或加密备份服务上的副本；同一磁盘上的另一个文件夹不能防范磁盘损坏。备份中可能包含私人研究和配置，不能放入公开仓库或问题反馈中。

### 第 1 步：列出需要备份的全部位置

| 内容 | 如何找到与保存 |
| --- | --- |
| OpenSci 软件及本机配置 | 包含 `Start-OpenSci.cmd` 的整个安装文件夹，尤其是 `config`、本机启动文件和连接配置 |
| 课题、历史、证据、回执 | 用记事本打开 `config/studies.local.json`，找到 `coordinator_root` 指向的目录并完整备份；旧部署没有该文件时核对实际记录位置，可能与软件同目录 |
| 研究代码、未提交修改、论文、数据集、模型、稿件和结果 | 逐项列出课题使用的外部文件夹；OpenSci 中保存一个文件路径不等于备份了该文件。服务器上的数据要在所属设备另行备份 |
| 加密隧道密钥 | 按 Windows+R，输入 `%LOCALAPPDATA%\OpenSci\connections`。升级菜单会自动纳入现有目录并复制密文，不解密。换电脑或账户时通常需要重新签发密钥或使用密码管理器的恢复方法 |
| 其他凭据与应用设置 | 按各应用支持的方式备份密码管理器、Codex/Claude 设置、SSH、模型供应商及浏览器配置。自动备份不会扫描整个用户目录或导出系统凭据库 |
| Zotero 原库和附件 | 在 Zotero 设置/首选项的“高级→文件和文件夹”查看数据目录；关闭 Zotero 后按[官方备份说明](https://www.zotero.org/support/zotero_data)完整备份，并单独纳入外置链接附件。文献列表导出和同步不能替代完整备份 |

### 第 2 步：停止写入并生成备份

先完成保存并保留回执。在 **Manage-Study-Connection.cmd → 4** 停止隧道，关闭其他助手连接、OpenSci 菜单、监测程序、导入和相关编辑器。复制 Zotero 库之前先关闭 Zotero。不要仅为备份而取消独立运行的计算任务；记录原运行编号，并按对应系统备份结果。

在软件和所有数据目录之外创建一个私人备份文件夹，例如 `D:\OpenSci-Backups`。双击 **Update-OpenSci.cmd**，选择 **4**，填写这个已存在文件夹的完整路径。核对显示的软件和课题目录，逐个添加需要纳入的外部文件夹，空行表示结束。确认确实停止写入后输入 **STOPPED**。

程序会创建新的受限目录、`backup.zip` 和 `receipt.json`；输出 `verified: true` 表示归档内的文件清单和摘要已核验。完整目录备份包括所选目录中的普通文件和空目录，以及未提交代码和本机配置；它会拒绝符号链接、目录联接及变化中的输入，不会悄悄忽略。总上限为 20 GiB 文件内容和 100,000 个 ZIP 条目，超出时使用经过验证的专用备份工具。空间不足、文件不可读或备份失败时不要继续升级。

ZIP **没有额外加密**。把它和回执复制到独立的加密设备或受权限保护的加密备份服务，并另外保存回执中的 SHA-256（文件指纹），用于确认副本未变化。Windows 目录权限会限制本机访问，但复制到别处后要重新核对访问权限。

### 第 3 步：验证独立副本并演练恢复

打开 PowerShell，先输入 `Set-Location -LiteralPath 'C:\OpenSci'`，把路径换成自己的安装目录。使用已配置的 Python；下面示例中 `C:\Tools\Python\python.exe` 要替换为 `config/runtime.local.json` 的 `python` 值，备份路径换成真实路径，`TRUSTED_BACKUP_SHA256` 换成原回执里的摘要：

```powershell
& 'C:\Tools\Python\python.exe' -B scripts/update_runtime.py verify-backup --archive 'D:\OpenSci-Backups\backup.zip' --sha256 TRUSTED_BACKUP_SHA256
& 'C:\Tools\Python\python.exe' -B scripts/update_runtime.py restore-backup --archive 'D:\OpenSci-Backups\backup.zip' --sha256 TRUSTED_BACKUP_SHA256 --destination 'D:\OpenSci-Recovery-Check'
```

恢复目标必须尚不存在。恢复目录中有 `runtime`、`coordinator` 和可能的 `extra-N`，原路径记录在归档的 `backup-manifest.json` 中。检查代表性的课题、稿件和附件；Zotero 恢复应按 Zotero 自己的流程在隔离位置验证。程序不会自动启动连接或把恢复副本设为第二个协调端。

这不是整机镜像：原文件权限、Windows 注册表和自启动设置、已安装软件、运行中进程以及跨账户可用的凭据不会由 ZIP 恢复。正式切换前须逐项重新配置和验证。记录备份范围、独立副本、可信摘要及恢复演练是否成功；未演练的恢复不能当作已经验证。

### 第 4 步：通过升级入口更新软件

1. 从 1.1.0 开始，在现有安装目录双击 **Update-OpenSci.cmd**。**1** 检查版本，**2** 下载并准备最新稳定版，**3** 使用已经下载的完整运行包。只从[官方发行页](https://github.com/yanboyang97/OpenSci/releases)获取文件；检查更新不会上传课题或本机设置。
2. 选择安装及数据目录以外的备份父目录，核对默认备份位置并补充外部文件夹。程序核验 ZIP、文件清单和各文件摘要，生成 `plan.json`。用记事本查看 `changes` 中列出的软件文件；`before`、`after` 是变更前后指纹。此时尚未修改安装。
3. 遇到“本地软件文件已修改/丢失”或“新文件与现有文件冲突”时停止，保留自定义内容并审查，不要为继续升级而删除自己的文件。软件只更新清单内的发行文件，保留 `.local.*` 配置、课题数据、额外用户文件和加密凭据；已退役的旧文件也不自动删除。
4. 完成独立备份后输入 **BACKED UP**。菜单会停止它管理的后台连接；手动停止其余写入者，然后输入 **STOPPED**，最后输入 **UPDATE** 执行已查看的清单。这些确认词是操作者声明，程序不能自动识别所有外部写入程序。
5. 替换前程序还会生成并核验本地完整备份。每个软件文件替换前再次核对指纹，保留原文件权限，并写入 `transaction.json` 记录进度。安装目录中保留的 `.opensci-update.lock` 是空闲时不工作的并发锁，不含用户数据。
6. 看到 `updated: true` 后核对版本、读取原课题概览；需要连接时重新打开 **Start-Study-Chat.cmd**。保存的密钥与登录启动偏好不变。升级不自动创建课题、迁移记录格式或启动实验。确认真实研究工作正常后再安排旧备份的保留周期。

### 首次从 1.0.1 升级到 1.1.0

旧版没有升级入口。先从 [1.1.0 发行页](https://github.com/yanboyang97/OpenSci/releases/tag/v1.1.0)下载 `OpenSci-1.1.0.zip` 和 `SHA256SUMS.txt`。在 Windows 开始菜单搜索 PowerShell 并打开，执行下面第一条命令，把 ZIP 路径换成实际下载位置，核对输出与校验文件中对应 ZIP 的摘要一致：

```powershell
Get-FileHash -LiteralPath 'C:\Users\YOURNAME\Downloads\OpenSci-1.1.0.zip' -Algorithm SHA256
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Downloads\OpenSci-1.1.0\Update-OpenSci.ps1' -RuntimeRoot 'C:\OpenSci'
```

核对通过后，在资源管理器对 ZIP 右键选择“全部解压”，解压到新文件夹。再执行第二条命令：第一个路径换成解压后 `Update-OpenSci.ps1` 的实际位置，`-RuntimeRoot` 后填**已有安装目录**。执行策略设置只作用于这个进程，不修改全局设置。选择 **4** 可先做备份，再重新运行选择 **3**，填写原 ZIP 和可信摘要并按上面的流程升级。不要直接把 ZIP 覆盖解压到旧安装。升级完成前保留解压出来的完整新版副本。

### 更新失败或断电后的恢复

保持写入停止，不要直接重做 Apply 或删除事务记录。安装里的入口打不开时，用解压出来的完整新版入口并指定原安装目录，选择 **5**，填写失败更新的 `transaction.json` 完整路径。状态为 `applying` 或 `recovery_required` 的事务可从已验证备份恢复原软件；中断后被人修改的文件会报冲突，需人工审查。恢复只撤回本次软件替换、删除本次新增且字节未再变化的软件文件，保留最新课题和配置，不会把旧数据盖回来。它不是对已完成升级的一键降级工具。

看到 `recovered: true` 后，检查原故障、核验旧安装，再用新目录重新生成升级计划。需要恢复数据时，采用上面的“恢复到全新目录”流程，不覆盖仍有更新记录的协调端。Windows 本机流程应在实际环境验证；Linux 可使用同一个 Python 入口，但不会自动获得 Windows 的加密保存和自启动能力。


## 备份、迁移与恢复

### 保存完整状态

变更前停止所有记录写入者和自动保存，包括已启用的助手接入与运行监测；核对原运行编号。实验可能仍在独立节点运行，但备份期间不应更新本地正式记录。

入门安装把记录放在 `C:\OpenSci-Data`，软件放在 `C:\OpenSci`。下面用 `--state-only` 备份独立记录目录，无需 Git；工具不会读取 `studies.local.json` 帮你寻找记录。先在文件资源管理器创建受控的外部目录 `C:\OpenSci-Backups`，它应位于软件和记录目录之外，并使用尚未存在的压缩包文件名。

```text
python -B scripts/backup_project.py backup --workspace C:/OpenSci-Data --output C:/OpenSci-Backups/OpenSci-backup-001.zip --quiesced --state-only
python -B scripts/backup_project.py verify --archive C:/OpenSci-Backups/OpenSci-backup-001.zip --expected-sha256 REPLACE_WITH_TRUSTED_SHA256
```

第一条成功后应显示压缩包路径和 `scope: coordinator_state`。把输出中的 `sha256` 值另存到可信位置，再用它替换第二条命令的 `REPLACE_WITH_TRUSTED_SHA256`；核验成功显示 `verified: true`。失败时保留错误和原备份，不能仅凭 ZIP 文件存在就判定成功。`--quiesced` 是操作者对停写的声明，不会代为停止服务。备份工具不自动加密，也不能清除已经混入历史的秘密。

状态备份包含所选记录目录内的指定正式记录、不可变历史、列入范围的本地配置、文献状态和稿件。运行软件及其本地配置、外部研究仓库和其他外部材料另行保存。只有源码与记录确实位于同一个干净 Git 根目录时，才使用合并备份：将 `--workspace` 换成那个根目录，去掉 `--state-only`，并事先审查和提交源码、另存未提交工作；它不会自动包含另一个 `C:\OpenSci-Data`。

合并备份还包含可达源码历史。未提交源码、Git 配置、外部批准与运行产物、数据模型、LFS 对象、凭据、软件环境、ACL、服务及本机运行映射等按具体收集范围单独保存。派生的文献 SQLite 索引可重建；Zotero 原库与附件仍需独立管理。准确范围以 [BACKUP_AND_MIGRATION.md](BACKUP_AND_MIGRATION.md) 和备份工具清单为准。

### 恢复到新目录

```text
python -B scripts/backup_project.py restore --archive C:/OpenSci-Backups/OpenSci-backup-001.zip --expected-sha256 REPLACE_WITH_TRUSTED_SHA256 --destination C:/OpenSci-Recovery-001
```

目标必须尚不存在，摘要使用前面独立保存的可信值。成功返回 `restored: true`、新目录下的 `workspace` 路径及 `writable_coordinator_activated: false`，表示尚未启用新的写入者。保持原写入者停止，先读取恢复结果：

```text
python -B scripts/hub.py --coordinator-root C:/OpenSci-Recovery-001/workspace list
python -B scripts/hub.py --coordinator-root C:/OpenSci-Recovery-001/workspace history --study STUDY-001 --limit 20
```

换成自己的课题编号，核对目标、当前进展、修订号和历史是否与备份时一致。状态备份不含 Git 源码；合并备份恢复的 Git 处于分离 HEAD 状态，后续分支由操作者选择。核对记录与引用、适用的 Git 来源、身份、运行路径、环境、资源、服务账户和权限，再明确交接唯一写入权。分别评价材料完整性、历史完整性、原运行可追溯性和科学可复现性；恢复文件不等于恢复进程。

### 维护计划

正常新建课题已经可以使用操作服务。导入或恢复的记录若提示需要准备，按诊断先执行 `lifecycle.py` 的 `upgrade` 预检和应用，再在需要时执行 `enable-commands`。这是维护动作，不是用户必须选择的记录模式。不要手改格式标记。

源码绑定更新使用 `upgrade`；源码不变而工作区迁移使用 `relocate`；恢复计划字段使用 `rollback --to-revision`。先生成外部预检计划，核对课题、修订号、摘要、源码、目标配置和原运行，再以可信计划摘要应用。计划一小时失效；材料或配置变化后重新预检。`--quiesced --backup-saved --runs-reconciled` 是实际完成这些工作的声明，不是工具自动执行的动作。

维护命令的 `--workspace` 指向记录目录，入门示例为 `C:/OpenSci-Data`，恢复验收时则换成恢复出的 `workspace` 路径；它不读取 `studies.local.json`。涉及远程探测时，授权后在预检与应用子命令都明确加入 `--allow-remote-check`。具体模板见 [docs/UPGRADE_GUIDE.md](docs/UPGRADE_GUIDE.md)。计划恢复生成更高修订号并保留后来的证据、批准、引用和运行；不会删除事实，也不会撤销 Zotero 写入或 Word 编辑。

### 容量与持续维护

当前课题记录上限为 4,000,000 个 UTF-8 字节，接近 80% 时提示 near_capacity。历史快照另行保存，不自动删除。备份未压缩载荷上限为 4 GiB。运行监测频繁变更会积累完整快照，应关注磁盘、扫描延迟和备份时间。超过限制时保留原状态并停止，不删历史强行继续。

<a id="feature-catalog"></a>
## 功能与模块名称

以下名称统一用于产品说明；括号中的英文是对应的正式英文名称。文件名、命令和 JSON 字段是稳定的技术接口，不代表另一套产品或模块。用户不需要选择记录格式，格式标记由软件维护。

| 模块 | 用途与主要入口 |
| --- | --- |
| 课题工作台（Research Workspace） | 浏览、新建、继续课题，选择开发工作区与执行节点，记录进展；主菜单 |
| 研究计划（Research Plans） | 编写研究问题、假设、方法、验收标准与人工决策；`methodology/` 和 `coordination/templates/` |
| 文献工作台（Literature Workspace） | 检索、收集、阅读、分析、组织与引用文献；菜单选项 9 |
| 证据评审（Evidence Review） | 预览评审计划，冻结所提供的材料与规则，执行经授权的模型评审并保留分歧；菜单选项 7 |
| 任务准备（Task Preparation） | 将源码、证据、环境、执行节点和资源限制绑定为任务草案；`scripts/prepare_task.py` |
| 人工批准（Human Approval） | 独立人工核对固定任务，填写受保护的批准文件及有效期；任务准备生成的批准模板 |
| 实验执行（Experiment Execution） | 执行一次已批准任务，记录心跳、日志和产物；`scripts/run_task.py` |
| 结果核验（Results Verification） | 按原运行编号检查状态、环境、产物及指标；`scripts/inspect_run.py` |
| 研究简报（Research Brief） | 生成带记录时间的只读课题摘要，供接续和交接；`hub.py brief` |
| 操作服务（Operation Service） | 校验结构化请求、角色和记录修订号，保存操作回执并恢复不确定结果；`scripts/hub_command.py` |
| 助手接入（Assistant Access） | 通过模型上下文协议 MCP 提供受限的课题与文献工具；`scripts/hub_mcp.py` |
| 手机科研（Mobile Research Access） | 通过 ChatGPT 手机应用接续电脑中的任务，并将成果保存到同一课题；使用宿主的远程电脑连接 |
| 运行监测（Run Monitor） | 读取指定运行来源，验证状态、产物、新鲜度与冲突；`scripts/observe_runs.py` |
| 历史与恢复（History and Recovery） | 保存不可变课题历史，通过明确的维护计划更新来源、迁移工作区或恢复计划字段；`scripts/lifecycle.py` |
| 备份与迁移（Backup and Transfer） | 备份源码和记录，校验归档，恢复到新目录；`scripts/backup_project.py` |
| 资源目录（Resource Catalog） | 将稳定的资源编号与设备路径分开，核对清单中的文件；`scripts/verify_resources.py` |
| 环境检查（Environment Check） | 检查工具条件，采集实际执行解释器和环境；`doctor.py`、`capture_environment.py` |
| 模拟验证（Simulation Lab） | 用求和计算与二次式计算验证软件接口、取消及恢复流程；`scripts/simulation.py` |
| Claude Code 开发启动器（Claude Development Launcher） | 在 Windows 中明确选择供应商，使用本副本的本机配置启动开发会话 |
| 实验追踪（Experiment Tracking） | 将核验后的已完成运行产物上传至明确配置的 MLflow 服务 |
| 工作流调度（Workflow Scheduling） | 经明确配置的 Prefect 工作进程调用固定实验流程 |
| 分发包校验（Package Verification） | 核对发行文件与摘要；`verify_delivery.py` |
| 文档生成（Documentation Builder） | 生成和检查相互独立的中英文离线手册；`tools/build_docs.py` |

完整英文命名索引见 [FEATURES.md](FEATURES.md)。

## 当前能力与使用边界

内置实验执行器仅支持**合成估计量示例**（Estimator Comparison）：公开合成数据、一个 CPU 线程、零 GPU。它比较指定分布下均值与中位数对既定位置参数的估计表现，不能据此推断真实科研领域的结论。专业科学软件、GPU 执行和自主研究服务不在内置执行器范围内。

安装文件不会自动创建 Git 身份与提交、开通模型或文献权限、启动常驻服务或批准实验。每项外部接入需要在实际环境中配置和核验。课题阶段、模型一致意见和离线测试通过都不等于科学验收。

文献来源、浏览器采集、原生引用编辑和扫描材料解析，取决于实际安装的软件与访问权限。每次操作应检查覆盖范围与返回状态。OpenSci 备份不包含外部 Zotero 数据库和原始附件存储，需要另外安排备份与恢复。

遇到部分完成、来源无权访问、全文缺失或结果未知，应保留原记录并显示原因。不要把“未执行”“等待用户”或“无法判断”改写成成功。

## 模拟验证与开发维护

模拟验证提供**求和计算**（Sum Calculation，接口编号 `sum-v1`）和**二次式计算**（Quadratic Calculation，接口编号 `quadratic-v1`）。编号用于选择固定适配器，不是产品版本名称。依次执行 preflight、prepare、submit、query、advance、collect、validate；queued 状态需要显式 advance，不会在终端关闭后自动执行。取消只对支持的状态生效，重启按原模拟编号读取，不自动重跑。

模拟验证使用独立存储和 `simulation_only` 标记，不进入正式实验批准或执行路径。它证明软件接口行为，不证明科学结论。扩展时注册固定模块、限制输入、独立核验结果并测试失败路径；不从请求加载任意模块或 shell 命令。

开发前核对适用规则、分支或原始文件状态。源码、接口、配置、文档和测试一起更新。保留既有数据、历史包和冻结证据；一次性报告、验证日志、缓存台账和打包过程材料放在发行包外。技术内容与文件名使用英文，中英文总手册分开维护。

正式公开仓库和安装包不包含回归套件、测试夹具或验证结果，这些材料保存在独立开发归档中。根目录 `AGENTS.md` 是共用规则来源，`rules.snapshot.md` 仅作为评审冻结证据。

```text
python -B tools/build_docs.py
python -B tools/build_docs.py --check
python -B verify_delivery.py
```

文档生成会核对源清单、链接、锚点和版本，并分别生成两种语言的 HTML。完成行为验证后再生成发行文件摘要，解压到新目录核验最终分发包；部署与打包分别记录结果。每次交付列出所有实际修改主机上的完整文件清单，以及验证配置、缓存、临时目录的保留或清理情况。

## 故障处理与术语

| 现象 | 先检查什么 | 正确处理 |
| --- | --- | --- |
| 源码操作提示缺少基线 | 是否在创建课题时登记研究源码及干净 Git 提交 | 保留原讨论课题，按[源码课题示例](#source-study)新建；当前不支持给原课题追加或替换研究目录 |
| 运行路径失效 | 本地配置与实际工具位置 | 更新本副本绑定后复核入口，不盲改全局 PATH |
| 修订号冲突 | 当前课题修订号与请求 | 按[保存恢复](#save-recovery)读取新记录，核对差异后再准备新请求 |
| 操作结果未知 | 原请求编号、内容与角色 | 按[保存恢复](#save-recovery)查询原回执，不换编号猜测重试 |
| 工作区不匹配 | 账号、目录、源码提交及 origin | 核对实际差异，必要时制定维护计划 |
| 心跳过期或状态缺失 | 原节点、进程、日志与运行编号 | 保留最后事实并对账，不推断已停止或自动重跑 |
| 文献部分成功 | 每来源或每条目的实际状态 | 保留成功项，只在恢复条件明确后继续 |
| 文献库实例变化 | 恢复或合并操作、原绑定 | 重新绑定并对账外部效果和引用 |
| 模型或全文不可用 | 当前服务、访问权限和预算 | 如实报告，等待明确授权，不自动换供应商 |
| 记录或历史损坏 | 原始字节、可信摘要与备份 | 保留现场，明确人工恢复，不能重算摘要掩盖损坏 |

<a id="save-recovery"></a>
### 保存失败后如何继续

1. 保留课题编号、原 `request_id`、完整请求或菜单输入和错误信息。在结果明确前，先停止继续保存。
2. 如果原操作来自本机菜单或操作者命令行，用**相同 Windows 账户**打开 PowerShell，加载[命令辅助函数](#command-context)，再执行下面两条命令。把 `STUDY-001` 和 `STUDY-001-NOTE-001` 换成原操作显示的真实编号。

```powershell
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'receipt', '--study', 'STUDY-001', '--request-id', 'STUDY-001-NOTE-001')
Invoke-OpenSci -Arguments @('scripts/hub_command.py', '--coordinator-root', 'C:/OpenSci-Data', 'show', '--study', 'STUDY-001')
```

如果原保存来自已连接助手，回到**同一个受保护连接**，要求它用原 `study_id` 和 `request_id` 调用 `opensci_get_receipt`，再读取当前课题。本机命令不能冒充私有连接身份。只有原操作确实以本机命令行的 agent 角色执行时，才在 `receipt` 前添加 `--agent`；它不能取回其他身份的回执。

| 看到的结果 | 下一步 |
| --- | --- |
| 回执为 `committed: true` | 已经保存。核对回执修订号和当前记录，后面可能已有新保存；不要换新编号重复执行。 |
| 回执查询成功，返回 `committed: false` 且没有错误 | 经核验的历史中没有该编号的已提交回执。确认原操作已停止后，只能用相同编号、完整原内容和相同调用身份重试；命令行使用原 `execute --request` 文件。菜单或请求文件若已不能提供完整原请求，交由操作者核对，不直接重做菜单 11，因为它会生成新编号。 |
| 查询报错、`committed: null`、`request_conflict` 或历史损坏 | 结果仍未明确。保留文件和返回信息，交由操作者处理；改编号、改身份或改历史不能解决问题。 |
| 保存明确返回 `revision_conflict` 且 `committed: false` | 此次请求被拒绝。读取 `show` 中的 `cursor.revision`（当前修订号）和 `project.project.progress.content`（当前进展），与草稿对照并保留新增内容，再用新编号和当前 `expected_revision` 提交经过核对的新请求。菜单用户先看 10，再重新填写 11。 |

重试或核对后的新保存都要取得已提交回执，再读回结果。如果涉及文献外部写入，还需保留文献操作／任务编号并按[文献恢复说明](#literature-workspace)对账；没有课题回执不能证明 Zotero 等外部操作没有发生。

**课题**是持续研究目标的记录容器；**任务**是固定输入和限制的工作定义；**运行**是一次实际尝试。**修订号**标识课题记录更新；**源码提交**标识代码；**格式标记**供验证器读取；它们不能互相替代。

**回执**证明操作登记结果，**摘要**用于对照可信原文核验字节，**人工批准**赋予固定任务在规定条件内的执行权限。三者含义不同，也都不能单独证明科学结论。**对账**是把原编号和已记录效果与实际系统核对；**覆盖**说明真正检查了哪些材料及遗漏范围。

提交问题时提供模块名、操作编号、修订号、实际环境、可复现步骤和脱敏日志。注明哪些结果已经验证、哪些仍未知，不提供凭据值。节点配置与课题记录中的 `agent` / `active_agent` 表示开发工作区，`compute` / `compute_target` 表示执行节点，`checkpoint` 对应记录进展，`anchor` 表示绑定的源码提交。这些是稳定字段或操作编号，不是额外功能或产品版本；助手接入的 `agent` 角色则表示受限助手。具体英文参考见 [DOCUMENTATION.md](DOCUMENTATION.md) 和 [FEATURES.md](FEATURES.md)。

## 普通 Chat 与 Work 接续同一课题

本机和远程文件夹中的 Work 都可以独立开展阅读、讨论、分析、写作和开发；普通 Chat 是可选入口，不要求先经过 Chat。进展保存本身不启动 Work、不新建对话、不调用额外模型、不提交实验，也不自动购买额度。无法可靠归因的用量保持未知，不承诺固定节省比例。

### 当前可用范围

当前可在创建课题时登记研究目录，尚未提供为已有课题追加或替换研究目录的受支持操作。无源码依据的课题可继续讨论和文献工作，依赖源码的检查点及实验准备继续阻止；不得手工修改记录中的目录或提交摘要。

OpenSci Study 插件与课题 MCP 服务可在选定课题中读取和保存结构化进展。普通 Chat 使用账户自己的私有隧道，本机和远程 Work 使用各自配置的 MCP 传输。只有可信宿主提供的原生项目身份才能用于关联；否则明确选择一个课题，并把来源信息记为未知。当前不提供多用户托管服务。

当前连接明确选择一个课题。没有可信宿主信息时，项目类型、Chat/Work 模式、主机与对话引用记为未知，不从标题、路径或模型自报推断。私有连接使用受保护的连接身份，不把本机 SID/UID 当成云端用户。共享原生项目不自动授予 OpenSci 权限。

### 初次使用和日常保存

软件目录 `runtime_root`、唯一记录目录 `coordinator_root`、每课题的可选 `research_workspace` 分别管理。比如安装在 `C:/OpenSci`，记录保存在 `C:/OpenSci-Data`。在 `config/studies.local.json` 配置记录目录，或向启动器传入 `-CoordinatorRoot`。先用菜单 2 建立课题，再用菜单 10 读取、菜单 11 保存。没有 Git 或执行节点也可开展讨论和文献工作；需要源码依据的检查点和实验会明确阻止。多份仓库的实验来源验证尚未实现，不能以单仓库验证代替。

`save_progress` 使用原操作服务的请求编号与期望修订号，参数为 `arguments.progress`。内容必须有 `summary`、`decisions`、`hypotheses`、`evidence_refs`、`open_questions`、`next_steps` 六项；后五项为文本列表。每次保存替换完整当前进展，不会自动追加摘要或保留传入空列表的旧条目；先读完整现状，把仍需保留的内容一起提交。摘要上限 16000 UTF-8 字节，每列表最多 64 项、每项最多 4000 字节，整个进展对象最多 48000 字节，请求最多 64000 字节。来源由受保护入口填写，模型不能自行补身份。证据引用不表示已读取文件。较早进展保留在不可变历史中，读取方法见[进展与历史](#saved-progress)，完整聊天仍保留在原生应用。

普通 Chat 选择 **OpenSci Study** 后，可以说：“保持普通 Chat，读取当前课题概览，区分事实与假设，只加载有关细节，不启动 Work。”保存时说：“把这些结论和下一步保存到同一课题，先读最新修订号，返回已提交回执；超时保留原编号和内容。”本机或远程 Work 重新读取同一课题即可接续；它不会自动获得完整聊天、本机文件权限、云端附件或运行中的进程。

### 连接和工具

普通 Chat 通过私有 Secure MCP Tunnel 接入。默认单次输入模式需要保持连接窗口开启；Windows 用户也可以选择上文介绍的“加密记住密钥，登录后在后台连接”。后台模式将密钥以 Windows 当前账户加密方式存储，可按选择在登录后启动，不安装系统服务。保持电脑联网、唤醒并登录；平台密钥有效期仍然生效。离线快照不是实时保存成功的证明。

连接健康状态只表示传输就绪，不代表模型活动、订阅使用或计费用量。无法可靠归因的用量保持未知。

只读工具包括 `opensci_get_capabilities`、`opensci_resolve_study_link`、`opensci_get_study_brief`、`opensci_get_study_detail`。概览确定性生成，上限 8192 UTF-8 字节；超出部分用 `has_more` 与绑定修订号的细节引用标明。细节返回 JSON 文本片段，需要按顺序拼接后解析，不会读取引用文件。还提供课题详情、回执、事件和文献工具；MCP 输入输出帧均受 256000 字节限制。

项目绑定通过受保护的操作者管理入口执行 `create_study`、`bind_project`、`unbind_project`；普通 Agent 无此权限。身份包含 provider、namespace、原生 project_id、project_type 和 host_id，名称只是显示值。一个原生项目当前对应一个课题，一个课题可关联多个原生项目。改名不改身份，暂时不可见不等于删除，新工作树或复制目录不继承授权。跨课题重绑先解除、再绑定，产生两份回执；不会伪称原子跨文件事务。连接授权与课题绑定分开验收。

本机 MCP 配置参见 `config/mcp.desktop.example.toml`。远程 Work 必须通过另行配置的受限固定命令传输访问同一协调端，参见 `config/mcp.remote.example.toml`；示例不会自动创建 SSH 账户、密钥或 Windows SSH 服务。没有原生项目管理接口时，在宿主界面完成项目建立与明确关联，保留已有项目指令。

### 选择或取消连接的课题

先停止相关连接，再执行 `python -E -s -B scripts/select_study_connection.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.chat.local.json --clear --connection-stopped`，清除当前课题授权。连接策略允许空课题列表，但必须只读、无原生项目身份；能力检查仍可用，关联返回 `selection_required`，所有课题读写均拒绝。未选择课题是合法的初始状态，不会自动建立假课题。

以后通过菜单建立真实课题，把上述 `--clear` 替换为 `--study-id YOUR-STUDY`，再重启连接。命令核验课题确实存在，只选择该课题，清除推测的原生身份并保留连接身份；项目绑定仍由另一个有回执的管理操作完成。运行进程会保留启动时载入的策略，仅修改文件不能撤销活跃进程权限。

保存和查回执必须使用同一受保护身份。`local_process` 取决于操作系统调用者，沙箱内外可能不同；私有单用户连接则使用固定连接身份。不能修改身份来冒领回执，也不能在提交结果未知时换编号重做。

### 本机协调端与远端 Work

当远端不能直接执行协调端固定命令时，可由操作者建立 SSH 反向转发，并使用 `scripts/study_remote.py`。服务端只监听 `127.0.0.1`，先验证独立的随机连接令牌，再开放固定协调端与策略的 MCP；最多八个会话，沿用帧大小和操作权限限制。令牌与 OpenAI 密钥分开，只存于两端仅所有者可读的受保护文件，不写入命令、项目内容或日志。

在协调端以 `study_remote.py server --port COORDINATOR_PORT --token-file PROTECTED_TOKEN --coordinator-root STATE_ROOT --policy PROTECTED_POLICY --ready-file NEW_READY_FILE` 启动；端口 0 可由系统分配。使用校验主机密钥、带 `ExitOnForwardFailure=yes` 的 SSH 连接，把远端回环端口转发到本机回环端口，避免影响已有转发。仅通过已认证通道传送客户端脚本和短期令牌，不传课题记录或 OpenAI 密钥。远端 MCP 采用 `config/mcp.ssh-loopback.example.toml`；固定命令入口也可调用同一客户端。先检查能力及关联，再读取和保存。

断线后重新建立相同权限范围并查询原回执，不能另建可写副本。停用时关闭网关和 SSH 转发，清除两端临时令牌；确认进程已停止后清理就绪标记。回环协议本身不是公共加密服务，依赖 SSH 提供传输加密与主机认证，不适用于公开或多用户部署。同一账户的文件访问也不是隔离边界。软件不自动创建服务或自启动项。

### 升级与恢复

新课题可以直接保存结构化进展。导入记录提示需要准备时，按诊断给出的维护操作执行预检和应用。先停止写入者、核对备份和原运行编号，保留原始字节与历史；不得手工修改格式标记。超时通过同一身份和角色查询原回执，私有连接身份不能用本机 `--agent` 身份冒充。版本冲突后先读差异，离线草稿恢复后再协调保存。

无 Git 协调端用 `backup_project.py backup --workspace PATH --output NEW_ARCHIVE --quiesced --state-only`；恢复必须到新目录，保留当前较新记录，不自动启动第二个写入者。状态备份不包含运行软件、外部研究文件、秘密和进程。规划回退新增修订并保留后续证据、运行与回执。英文细节与示例见 [Study connections](docs/STUDY_CONNECTION.md)。
