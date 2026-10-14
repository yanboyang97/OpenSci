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

适用版本：**OpenSci 1.0.0**。文档日期：**2026-10-14**。

这本手册从第一次安装开始，说明在哪里操作、需要填写什么、完成后会看到什么。先做完下面的入门流程，再选择需要的文献、助手或手机功能。项目的整体介绍见 [README](README.md#chinese)。打开 `OpenSci-Manual.zh-CN.html` 可离线阅读和搜索，英文版为 `OpenSci-Manual.html`。

<a id="beginner-start"></a>
## 零基础开始：建立课题并保存一次进展

第一次只完成一件事：**建立一个课题，保存一条进展，再把它读出来。** 此时只需一台 Windows 电脑、Python 和 OpenSci 文件。模型账户、Git、Zotero 和服务器可以以后按需添加。若已经有人替你配置好，确认记录保存位置后，从第 4 步开始。

“课题（Study）”就是一个研究问题的记录本，用来保存目标、证据、决定和下一步。OpenSci 菜单负责保存记录；需要自然语言对话时，再接入 ChatGPT、Codex 等助手。

### 第 1 步：分开存放软件和研究记录

把完整 OpenSci 软件包解压到一个新文件夹。本手册用 `C:\OpenSci` 举例；打开后应能看到 `Start-OpenSci.cmd`、`config` 和 `scripts`。如果它们还在下一层文件夹内，以那一层作为安装目录。

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

在文件资源管理器中打开“显示文件扩展名”，避免把 `.json` 误存为 `.json.txt`。复制后用记事本编辑，保存为 UTF-8。JSON 是一种文本设置格式，请保留示例中的括号、逗号和英文双引号。

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

| 屏幕提示 | 含义 | 示例 |
| --- | --- | --- |
| Saved summary | 这次完成或了解到什么，必填 | 已确定第一阶段的研究问题 |
| Decisions | 已经做出的决定 | 先做文献整理 |
| Hypotheses | 尚需证据支持的假设 | 没有则直接按 Enter |
| Evidence refs | 真实来源或文献条目的引用 | 没有则直接按 Enter |
| Open questions | 还没有解决的问题 | 应选择什么比较方法？ |
| Next steps | 下一步做什么 | 选出第一批阅读文献 |

看到保存回执后，输入 `10`（Study Overview，课题概览）和课题编号。概览中出现刚才保存的内容，就完成了基础使用。输入 `0` 退出菜单，记录会继续保存在数据目录中。

### 第 6 步：只添加现在需要的功能

先选择一个备份位置，再把课题用于持续研究。想用 AI 对话，接着看[助手接入](#assistant-setup)；想使用自己的论文，看[文献工作台](#literature-workspace)；想出门后继续工作，看[手机科研](#mobile-research)。全部软件要求集中在[依赖说明](#requirements)，可以按需安装。

如果以后需要把实验与源码版本关联，请按进阶配置创建一个登记研究源码位置的新课题。现有讨论课题仍可继续使用；当前没有把它直接转换为源码课题的操作入口，不要手动改写记录。

### 第一次打开遇到问题

| 现象 | 处理方法 |
| --- | --- |
| 窗口一闪而过 | 在 PowerShell 先输入 `Set-Location -LiteralPath 'C:\OpenSci'`，再输入 `.\Start-OpenSci.cmd`，保留窗口中的错误信息 |
| 提示需要 Python 3.10+ | 重做第 2 步，核对 `runtime.local.json` 中的完整解释器位置 |
| 提示记录目录不存在 | 核对 `studies.local.json` 与实际创建的 `C:\OpenSci-Data` 是否一致 |
| 提示缺少工作区配置 | 核对文件是否确实叫 `C:\OpenSci-Data\config\hub.local.json` |
| 提示 JSON 无法读取 | 核对英文双引号、逗号、UTF-8 编码，以及文件没有多出 `.txt` 后缀 |
| 提示 Git 文件不存在 | 初次讨论课题可以将 `git` 保持为空，不要保留不存在的示例路径 |
| 不确定是否保存成功 | 保留原 `request_id`，先查询该操作的回执，再决定是否重试 |

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
## 安装 OpenSci Study 插件与课题 MCP 服务

插件把 OpenSci 的工具交给 AI 助手使用；MCP 是它们之间的连接方式。先完成前面的入门流程，记下自己的课题编号。以下用 `STUDY-001` 举例；不要照抄不存在的编号。

### 第 1 步：指定助手可以访问的课题

在文件资源管理器中，将 `C:\OpenSci\config\mcp.unselected.example.json` 复制到 `C:\OpenSci-Data\config`，改名为 `mcp.policy.local.json`。用记事本打开，把 `connection_id` 的占位文字改成你选定的连接名称，例如 `opensci-desktop-01`。它用于识别这条连接，不是密码；每条连接使用不同名称，日后恢复请求时保持原名称。

首次配置时尚未启动连接。如果之前已经接入，请先在助手中停用对应连接；普通 Chat 隧道还需停止它的启动窗口。然后打开 PowerShell，输入以下命令。软件和记录目录不同则替换路径；最后一个编号换成自己的课题编号。

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
$OpenSciPython = (Get-Content -LiteralPath '.\config\runtime.local.json' -Raw -Encoding UTF8 | ConvertFrom-Json).python
& $OpenSciPython -E -s -B scripts/select_study_connection.py --coordinator-root C:/OpenSci-Data --policy C:/OpenSci-Data/config/mcp.policy.local.json --study-id STUDY-001 --connection-stopped
```

看到 `Study selected.` 表示选择已保存。此操作允许助手对该课题进行受限制的写入；只想读取时，在启动连接前把策略文件中的 `allow_write` 改成 `false`。每次改动策略都要重启连接才能生效。撤销选择时，在连接停止后将命令中的 `--study-id STUDY-001` 换成 `--clear`；此时不再允许访问任何课题。

### 第 2 步：告诉插件去哪里找记录

按 Windows 键加 R，输入 `%LOCALAPPDATA%` 并回车，在打开的位置新建 `OpenSci` 文件夹。把 `C:\OpenSci\config\plugin.connection.example.json` 复制进去，改名为 `connection.json`。用记事本打开，核对两个路径指向自己的记录目录和上一步的策略文件：

```json
{
  "schema_version": 1,
  "coordinator_root": "C:/OpenSci-Data",
  "policy": "C:/OpenSci-Data/config/mcp.policy.local.json"
}
```

保存为 UTF-8，确认文件没有多出 `.txt` 后缀。此文件不保存密钥，不放在插件缓存中；缺少或无效时插件拒绝启动。Linux 的对应位置是 `~/.config/opensci/connection.json`；有特殊存放需要时，可在宿主进程用 `OPENSCI_CONNECTION_FILE` 指定绝对路径。

### 第 3 步：在助手中安装并使用

公开仓库根目录就是插件根目录，包含 `plugin.json`、`mcp.json`、服务器源码和图标。支持插件市场的客户端可执行 `codex plugin marketplace add yanboyang97/OpenSci`，再在桌面插件目录安装 **OpenSci Study**。Python 必须能在宿主环境中以 `python` 启动；若你只能使用 Python 的完整路径，按 [直接 MCP 配置](docs/PLUGINS.md#direct-mcp-installation)接入。该页面提供可填写路径的完整配置样例。

安装后开始一个新对话，请助手“读取已选 OpenSci 课题的概览”。随后可请它讨论研究问题，并明确要求保存结论。保存成功会返回回执与课题修订号；只有聊天回答而没有保存回执时，不要假定记录已经更新。出现 `selection_required` 表示还未选课题，返回第 1 步处理。

### 可选：从普通 Chat 访问课题

普通 Chat 用户自行配置官方 Secure MCP Tunnel 和私有 MCP 连接。从官方发行页下载客户端，生成本机 stdio profile；以 `config/chat.example.json` 建立自己的 `chat.local.json`，填写经过核验的客户端摘要、profile、组织标识及私有 PID/健康/日志位置，创建必要目录。双击 `Start-Study-Chat.cmd`，在隐藏本机输入中填写仅有 Tunnels Read＋Use 权限的密钥，保持电脑和窗口运行。不同用户使用自己的组织、隧道和凭据。

GitHub 发布提供可下载、自部署的运行包、插件包和 MCP 包，不等于已上架 OpenAI 公共插件目录。该目录对本地 MCP 发布另有平台资格和审核要求。当前实现用于私有单用户，不把个人隧道公开为多用户服务。完整步骤见 [Plugins and MCP](docs/PLUGINS.md)，数据去向见 [Privacy](PRIVACY.md)。

## 进阶：工作区与命令

### 了解部署角色

**协调端**（Coordinator）是正式课题记录的唯一写入者。**开发工作区**（Development Workspace）保存用于开发和检查的源码；配置字段 `active_agent` 指向它。**执行节点**（Execution Node）由独立人工提交者运行经批准的实验。三个角色可以位于同一硬件，但账户、路径、权限和凭据应分别核验。选择开发工作区不会改变执行节点或移动运行中的实验。

文档使用 `C:\OpenSci` 和 `/home/researcher/OpenSci` 作为示例路径。真实账号、SSH 别名和工具路径以忽略的本地配置为准。不要把开发副本启用为同一课题的第二个协调端。

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
python -B scripts/hub.py --coordinator-root C:/OpenSci-Data brief --study STUDY-001
```

涉及源码的检查点先审查、验证、提交并核对同一来源。普通讨论或文献研究可直接用菜单 11 或 `save_progress` 保存，不以 Git 为前提。普通文字笔记可通过操作服务的 `note` 写入，不探测开发工作区；`checkpoint` 校验涉及源码的阶段变更。结束前记录完成事项、未决问题、下一步及原运行状态，生成研究简报用于交接。简报有时间戳，命令输出 JSON，不会自动保存文件、发送内容或查询节点的实时状态；需要文件时由操作者明确保存输出。

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

<a id="literature-workspace"></a>
## 文献工作台

### 设置与权限

保留 Zotero 自身数据和附件备份。在 `config/literature.local.json` 中配置个人文献库实例、检索方向、来源、授权范围、有限预算及执行节点。先执行连接检查，再在明确授权的试用集合中核验操作。不要直接修改 Zotero 数据库或存储布局；原笔记和批注必须保留。

Zotero Local API 仅使用回环地址。凭据通过环境引用或经同意的 Windows 凭据引用提供，不放进 JSON、文档和聊天。网页机构权限、API 权限和全文权益分别判断。当前全局授权与限制持续生效，课题固定设置不能保留已撤销权限或扩大预算。

菜单接收 `capabilities` 或已审阅的结构化请求文件路径；自然语言理解由获授权的聊天助手完成，菜单本身没有内置自然语言模型或可视化设置编辑器。将请求保存为如 `config/command.local.json` 后，在菜单 **9** 输入该路径；相对路径始终从 OpenSci 根目录解析。此入口只接受 `literature.*` 操作，其他请求使用操作服务。文献请求沿用操作服务封装，`arguments` 只包含 `payload`。设置通过受保护的本地配置文件或操作者的 `literature.config_update` 请求修改。

### 全部文献功能

| 功能正式名称 | 操作 | 用法与边界 |
| --- | --- | --- |
| 连接检查 | `literature.capabilities` | 检查已连接能力，未测试项目保持未验证 |
| 文献记录查询 | `literature.get` | 读取课题关联、条目、操作或原生写作任务 |
| 文献库检索 | `literature.search_library` | 检索本地库或派生索引，说明索引时间 |
| 文献检索 | `literature.search` | 按来源保留查询、窗口与覆盖；`resume_run` 接续原检索 |
| 引文导入 | `literature.search_import` | 读取原生 RIS/BibTeX 导出，生成候选记录 |
| 文献收集 | `literature.collect` | 将明确选择的候选收集到指定集合，逐项报告结果 |
| 全文获取 | `literature.fetch_fulltext` | 针对一个条目尝试已授权公开 URL 或 PMC 路径 |
| 文献整理 | `literature.organize` | 管理明确选择的集合、标签、笔记和批注 |
| 课题文献关联 | `literature.bind_study` | 绑定集合、条目与筛选理由，不改动其他课题的筛选 |
| 证据快照 | `literature.read` | 按发现、常规或深入层级冻结材料与提取覆盖 |
| 文献分析 | `literature.analyze` | 为证据矩阵或模型分析准备有界任务 |
| 分析任务派发 | `literature.job_dispatch` | 经明确远程授权向固定执行端派发 |
| 分析结果导入 | `literature.job_import` | 核对原任务及材料绑定后导入结果 |
| 分析状态查询 | `literature.job_status` | 读本地状态；显式刷新才联系执行端 |
| 分析任务控制 | `literature.job_pause`、`job_resume`、`job_cancel` | 区分控制请求已记录与实际生效状态 |
| 参考文献导出 | `literature.export` | 导出固定材料的书目及 LaTeX/Quarto 示例 |
| 引用写作 | `literature.cite` | 维护引用映射，或在实际原生 Word 插件会话中完成指定动作 |
| 文献变更预览 | `literature.preview_change` | 展示变更前内容、影响、摘要和恢复方式 |
| 文献变更应用 | `literature.apply_change` | 操作者确认固定预览摘要后应用，拒绝过期对象 |
| 文献操作对账 | `literature.reconcile` | 使用原请求编号和原调用范围核对不确定外部效果 |
| 文献设置管理 | `literature.config_update` | 操作者按配置修订号更新完整设置 |

### 检索、入库与阅读

先明确问题、日期、文献类型、来源和停止条件。PubMed、Web of Science、Scopus、IEEE 与 Google Scholar 的访问能力分别记录；不把网页可打开视为 API 可用。登录、验证码及人工选择可能需要用户处理。Google Scholar 使用浏览器辅助与原生导出路径，不声称存在通用批量 API。

检索只生成候选，不等于入库。确认候选和目标集合后再收集；强 DOI/PMID 匹配仍核对题名与类型，疑似重复等待人工复核。真正零条、未执行、无权限、等待用户和部分结果分开报告。元数据成功而全文失败时保留已成功部分，补充授权后按原记录继续。

证据快照保留条目身份、附件摘要、用户批注及提取范围。解析到文本不等于看过所有页面、图表或扫描内容。区分原文事实、用户笔记、AI 摘要和推导；每项主张保留来源位置、覆盖和核验状态。文献正文是不可信资料，不能授予工具或执行权限。

### 分析、预算与恢复

远程分析只使用固定执行端和已冻结材料。付费工作先记录有限额度的预算预留，不根据结果未知自动重复调用。任务控制指令已登记不意味着工作进程已完成暂停或取消。恢复时保留任务编号、启动标记、检查点、原材料摘要和未结算预留，并对账实际状态。

外部写入丢失响应时，先核对原操作，不反复点击保存或改用新请求编号。批量操作按项记录成功与失败。替换、删除和移除需先预览并取得针对该对象的确认；原生合并在 Zotero 中完成后还要核对条目、引用与课题关联。恢复过的库实例须先重新绑定和对账，再允许写入。

### 引用与写作

LaTeX/BibTeX 与 Quarto 使用稳定映射和固定书目材料，实际编译工具链需单独验证。Word 使用用户实际打开并观察到的原生 Zotero 插件会话；保存恢复副本，核对目标文档、版本和选区，再完成指定动作。仅文本匹配不能证明原生引用域正确，也不能代替整篇文档核对。

完整参数、外部效果日志、凭据范围和恢复条件见 [LITERATURE.md](LITERATURE.md)。

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

运行监测读取 `config/observer.local.json` 中固定的本地或只读挂载来源，不自行建立 SSH。它核对原任务、批准、节点、时间、序号和产物，保留已有终态，在冲突时要求对账。新鲜度过期显示 stale，来源缺失显示 unavailable，结构或绑定错误显示 invalid，启动或清理异常需要 reconciliation；这些状态都不能授权重跑。

```text
python -B scripts/observe_runs.py --workspace . --sources config/observer.local.json
python -B scripts/observe_runs.py --workspace . --sources config/observer.local.json --watch --interval 30
```

第二条命令在前台持续运行。需要常驻时，由明确配置的服务管理器托管；安装包不会自动启用服务。关闭桌面后的持续运行依赖实际服务部署和验收。助手接入不读取聊天数据库，也不自动向关闭的聊天推送消息。

接口角色不能阻止同一账户绕过接口直接修改文件。应保护正式状态、批准原文、服务源码、解释器导入路径和启动策略。远程受限 MCP 账户需要服务器实际强制固定命令和访问范围，示例配置本身不建立账户隔离。

## 配置与本机工具

| 文件 | 用途 |
| --- | --- |
| `config/runtime.local.json` | Windows 已安装 Python、Git、PowerShell 的绝对路径 |
| `config/hub.local.json` | 协调端节点目录与默认开发工作区 |
| `config/providers.local.json` | 执行节点的模型供应商配置，使用时明确传入 |
| `config/literature.local.json` | 个人库绑定、来源、授权、方向和费用限制 |
| `config/command.local.json` | 准备执行的单次请求，不是服务开关 |
| `config/mcp.policy.local.json` | 助手接入允许的课题与操作 |
| `config/observer.local.json` | 运行监测允许读取的运行来源 |
| `config/device.local.json` | 资源编号在本设备的绝对路径 |
| `coordination/resources.json` | 稳定资源身份、版本和文件摘要 |
| `environments/*.local.json` | 在实际执行环境采集的记录 |
| `tools/claude-launcher/machine.local.psd1` | 本副本 Claude 可执行文件和凭据引用 |

示例文件定义格式，不代表服务已开通。所有路径按实际设备填写，不能将 `~` 或占位符当作绝对路径。节点配置中的能力值是声明，不是实时监测。现有课题会保留工作区配置快照；修改账号、目录、解释器等绑定时使用明确维护流程，不覆盖历史记录。

Windows 选择 Python 的顺序是显式 `-Python`、本地运行配置、PATH 查找。启动器只在进程内临时加入配置的 Git 路径，并在结束时恢复；命令包装器的执行策略设置仅作用于子进程，不修改全局策略。直接运行 Python 示例时，使用实际配置的解释器并确保当前终端可找到 Git。

Claude Code 开发启动器需要 Windows、PowerShell 7 与原生 `claude.exe`。打开项目根目录的 `Start-ClaudeCode.cmd`，在开发启动器菜单选择 Setup 创建本副本映射；已有文件不会覆盖。`-ClaudeProvider deepseek` 或 `kimi` 明确选择供应商。检查与凭据管理只作用于相应本地配置，不改变个人 Profile、其他安装副本或研究执行授权。模型名称和端点以配置文件为准，配置声明不代表服务已验证。Windows 交互开发与自动证据评审的供应商配置各自独立。

## 备份、迁移与恢复

### 保存完整状态

变更前停止所有记录写入者和自动保存，包括已启用的助手接入与运行监测；核对原运行编号。实验可能仍在独立节点运行，但备份期间不应更新本地正式记录。

尚无 Git 基线时，先保留发行包、本地配置和快捷方式重建信息。这只能保存基础部署，不能声称完整课题备份。源码与记录合并备份需要 Git 根目录及干净提交。独立协调端可用 `backup_project.py backup --state-only` 备份课题状态，无需 Git；运行软件和外部研究文件另行保存。

```text
python -B scripts/backup_project.py backup --workspace . --output C:/OpenSci-Backups/OpenSci-backup-001.zip --quiesced
python -B scripts/backup_project.py verify --archive C:/OpenSci-Backups/OpenSci-backup-001.zip --expected-sha256 TRUSTED_SHA256
```

先创建受控的外部输出目录，使用新文件名，将工具输出摘要另存到可信位置。`--quiesced` 是操作者对停写的声明，不会代为停止服务。备份工具不自动加密，也不能清除已经混入历史的秘密。

备份包含可达源码历史、指定正式记录与不可变快照、列入范围的本地配置、文献状态和稿件。未提交源码、Git 配置、外部批准与运行产物、数据模型、LFS 对象、凭据、软件环境、ACL、服务及本机运行映射等按具体收集范围单独保存。派生的文献 SQLite 索引可重建；Zotero 原库与附件仍需独立管理。准确范围以 [BACKUP_AND_MIGRATION.md](BACKUP_AND_MIGRATION.md) 和备份工具清单为准。

### 恢复到新目录

```text
python -B scripts/backup_project.py restore --archive C:/OpenSci-Backups/OpenSci-backup-001.zip --expected-sha256 TRUSTED_SHA256 --destination C:/OpenSci-Recovery-001
```

目标必须尚不存在，恢复的项目位于目标下的 `workspace`。保持原写入者停止，核对记录与引用、Git 来源、身份、运行路径、环境、资源、服务账户和权限，再明确交接唯一写入权。分别评价材料完整性、历史完整性、原运行可追溯性和科学可复现性；恢复文件不等于恢复进程。

### 维护计划

正常新建课题已经可以使用操作服务。导入或恢复的记录若提示需要准备，按诊断先执行 `lifecycle.py` 的 `upgrade` 预检和应用，再在需要时执行 `enable-commands`。这是维护动作，不是用户必须选择的记录模式。不要手改格式标记。

源码绑定更新使用 `upgrade`；源码不变而工作区迁移使用 `relocate`；恢复计划字段使用 `rollback --to-revision`。先生成外部预检计划，核对课题、修订号、摘要、源码、目标配置和原运行，再以可信计划摘要应用。计划一小时失效；材料或配置变化后重新预检。`--quiesced --backup-saved --runs-reconciled` 是实际完成这些工作的声明，不是工具自动执行的动作。

涉及远程探测时，授权后在预检与应用子命令都明确加入 `--allow-remote-check`。具体模板见 [docs/UPGRADE_GUIDE.md](docs/UPGRADE_GUIDE.md)。计划恢复生成更高修订号并保留后来的证据、批准、引用和运行；不会删除事实，也不会撤销 Zotero 写入或 Word 编辑。

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
| 源码操作提示缺少基线 | 是否配置研究源码及干净 Git 提交 | 讨论和文献可继续；仅为需要源码的步骤建立已核对来源 |
| 运行路径失效 | 本地配置与实际工具位置 | 更新本副本绑定后复核入口，不盲改全局 PATH |
| 修订号冲突 | 当前课题修订号与请求 | 重新读记录；已执行结果先查原回执 |
| 操作结果未知 | 原请求编号、内容与角色 | 查询回执并用相同请求恢复，不换编号重试 |
| 工作区不匹配 | 账号、目录、源码提交及 origin | 核对实际差异，必要时制定维护计划 |
| 心跳过期或状态缺失 | 原节点、进程、日志与运行编号 | 保留最后事实并对账，不推断已停止或自动重跑 |
| 文献部分成功 | 每来源或每条目的实际状态 | 保留成功项，只在恢复条件明确后继续 |
| 文献库实例变化 | 恢复或合并操作、原绑定 | 重新绑定并对账外部效果和引用 |
| 模型或全文不可用 | 当前服务、访问权限和预算 | 如实报告，等待明确授权，不自动换供应商 |
| 记录或历史损坏 | 原始字节、可信摘要与备份 | 保留现场，明确人工恢复，不能重算摘要掩盖损坏 |

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

`save_progress` 使用原操作服务的请求编号与期望修订号，参数为 `arguments.progress`。内容必须有 `summary`、`decisions`、`hypotheses`、`evidence_refs`、`open_questions`、`next_steps` 六项；后五项为文本列表。摘要上限 16000 UTF-8 字节，每列表最多 64 项、每项最多 4000 字节，整个进展对象最多 48000 字节，请求最多 64000 字节。来源由受保护入口填写，模型不能自行补身份。证据引用不表示已读取文件。较早进展保留在不可变历史中，完整聊天仍保留在原生应用。

普通 Chat 选择 **OpenSci Study** 后，可以说：“保持普通 Chat，读取当前课题概览，区分事实与假设，只加载有关细节，不启动 Work。”保存时说：“把这些结论和下一步保存到同一课题，先读最新修订号，返回已提交回执；超时保留原编号和内容。”本机或远程 Work 重新读取同一课题即可接续；它不会自动获得完整聊天、本机文件权限、云端附件或运行中的进程。

### 连接和工具

通过账户支持的私有 Secure MCP Tunnel 与自定义 MCP 应用连接普通 Chat。本地仍是有界 stdio 服务，没有任意命令、文件代理或公共 HTTP 入口。Windows 双击 `Start-Study-Chat.cmd` 可运行 `Start-Study-Chat.ps1`，它检查官方客户端摘要和已有进程，并在本机隐藏输入中接收仅有 Tunnels Read＋Use 权限的密钥。密钥仅保留在进程及子进程环境中，正常退出时清除，不写入文件或聊天。启动器不安装服务、计划任务、自动启动或秘密持久化。保持电脑及连接窗口开启；根据自己选择的有效期及时更新受限密钥。离线时快照仍可阅读，但草稿不能宣称已实时保存。

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
