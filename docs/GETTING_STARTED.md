# Getting Started

[Handbook](../DOCUMENTATION.md) · [All software requirements](INSTALLATION.md)

Your first goal is simple: **create a Study, save a progress note and read it back**. A Study is a saved research question with its evidence, decisions and next steps. This first session needs Python and the OpenSci files. AI accounts, Git, Zotero and servers can be added later.

The steps below use Windows. Linux users can use the short section near the end of this guide. If someone has already set up OpenSci for you, go straight to **Create your first Study** after confirming which folder holds your records.

<a id="deployment"></a>
## 1. Put the software and records in separate folders

Open the [OpenSci downloads page](https://github.com/yanboyang97/OpenSci/releases), expand **Assets** for version 1.1.0, and download **OpenSci-1.1.0.zip**, the runtime package. The Plugin and MCP packages are for assistant integration later. Extract the runtime archive into a new folder. This guide uses `C:\OpenSci`; the folder should contain `Start-OpenSci.cmd`, `config`, `scripts` and this handbook. If those files are inside a second nested folder, that inner folder is the installation folder.

Use a separate folder, `C:\OpenSci-Data`, for your research records. In File Explorer, create a `config` folder inside it. You can choose different writable locations; replace both example paths consistently throughout setup. Keep any existing records in place rather than overwriting them.

| Folder in this guide | What belongs there |
| --- | --- |
| `C:\OpenSci` | Software, examples and handbooks |
| `C:\OpenSci-Data` | Your Study records and their local settings |

The computer that saves these records is called the **Coordinator**. For your first setup, it is simply this computer. Keep one authoritative records folder for each Study.

## 2. Install or locate Python

Python is the program that runs OpenSci. Install **Python 3.10 or newer** from [python.org](https://www.python.org/downloads/windows/) if it is not already installed. Enable the installer option that makes Python available to commands, when offered.

Open the Windows Start menu, search for **PowerShell**, and open it. This is the window where you enter commands. Paste each line below, then press Enter:

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

The first line should report Python 3.10 or newer. The second prints the full path to `python.exe`; keep that path for step 3. If `python` opens the Store or is not recognized, try `py -3` in place of `python`. If neither works, finish Python installation and open a new PowerShell window.

Before adding local settings, verify a fresh runtime extraction:

```powershell
Set-Location -LiteralPath 'C:\OpenSci'
python -B verify_delivery.py
```

Use `py -3 -B` if that is the working Python command on your computer. A successful check says `Verified exact delivery file set`. For a Git checkout use `--installed`; Git's internal files are outside the runtime manifest. If files do not match, obtain an intact copy or reconcile the changes before continuing. Do not delete your own data to make a check pass.

## 3. Create three settings files

In File Explorer on Windows 11, select **View → Show → File name extensions**; on Windows 10, select **View** and check **File name extensions**. Confirm that a copied settings file ends in `.json`, not `.json.txt`. See [Microsoft's file extension guide](https://support.microsoft.com/en-us/windows/experience/storage-filemanagement/common-file-name-extensions-in-windows) if the controls differ. Open copied files with Notepad, replace their contents as described, and save as UTF-8. JSON is a small text settings format: keep the braces, commas and straight quotation marks as shown.

**Records settings.** Copy `C:\OpenSci\config\hub.study.example.json` to `C:\OpenSci-Data\config\hub.local.json`. Leave its contents unchanged. It is the supplied empty setup for a discussion Study.

**Records location.** Copy `C:\OpenSci\config\studies.example.json` to `C:\OpenSci\config\studies.local.json`. Replace its contents with:

```json
{
  "schema_version": 1,
  "coordinator_root": "C:/OpenSci-Data"
}
```

**Python location.** Copy `C:\OpenSci\config\runtime.example.json` to `C:\OpenSci\config\runtime.local.json`. Use the following contents, replacing the `python` value with the actual path from step 2. Forward slashes work here and avoid JSON backslash escaping.

```json
{
  "schema_version": 1,
  "python": "C:/Tools/Python/python.exe",
  "git": "",
  "powershell": ""
}
```

`C:/Tools/Python/python.exe` is only an example. Do not keep it unless it is your actual installation. Leave the last two values empty for this first session. The `.local.json` files belong to your installation; keep private paths and credentials out of the public repository.

## 4. Create your first Study

Double-click `C:\OpenSci\Start-OpenSci.cmd`. The menu uses English labels; enter the number and press Enter.

1. Enter `1` (**Browse Studies**). A new setup has an empty list.
2. Enter `2` (**Create Study**).
3. At **Study ID**, enter a new ID such as `STUDY-001`. Use 3–48 uppercase letters, digits or hyphens, beginning with a letter.
4. At **Research goal**, enter your own question, such as `Understand the evidence on reusable food packaging`.

The result should show your Study ID and goal, with a save receipt containing `committed: true`. Keep its `request_id`, the operation's reference number. If an ID already exists, open that Study instead of creating it again.

## 5. Save one progress note

Enter `11` (**Save Discussion Progress**) and the same Study ID. Fill the prompts below. The summary is required; you can press Enter to leave each remaining prompt empty.

Each save **replaces the whole current progress summary and all five lists**. Before a later save, read **10 Study Overview** and include any earlier content you still need. Leaving a list prompt empty clears that list in the current overview; it does not mean “keep the old value”. Earlier versions remain in history; see [reading progress and history](DAILY_USE.md#saved-progress).

| Prompt | What to enter | Example |
| --- | --- | --- |
| Saved summary | The current summary, including earlier points to keep | `Defined the first research question` |
| Decisions | A decision you made | `Start with a literature review` |
| Hypotheses | An idea still needing evidence | Leave empty if none |
| Evidence refs | A real source or item reference | Leave empty if none |
| Open questions | Something unresolved | `Which comparison method is appropriate?` |
| Next steps | Your next action | `Select the first papers to read` |

After the save receipt, enter `10` (**Study Overview**) and your Study ID to read the saved progress. You have completed the basic setup when the Overview contains your note. Enter `0` to close the menu; saved records remain in the records folder.

The menu is a local record tool. To have a natural-language conversation, connect an assistant in the next step.

## 6. Add the next feature you need

| Your next goal | Follow this guide |
| --- | --- |
| Discuss and save research with an AI assistant | [Plugins and MCP](PLUGINS.md) |
| Use your existing Zotero papers | [Literature Workspace](LITERATURE.md) |
| Continue work while traveling | [Research from Your Phone](MOBILE_RESEARCH.md) |
| Back up your work | [Maintenance](MAINTENANCE.md) |
| Work with research code and remote machines | [Configuration](CONFIGURATION.md), then the Git section below |

Choose a backup destination before relying on the records for ongoing research. The detailed [requirements table](INSTALLATION.md) separates necessary and optional software. You do not need to configure all integrations to use one of them.

If later work needs experiments tied to source versions, follow [Create a Study with research source](DAILY_USE.md#source-study). Your discussion Study remains available; there is currently no supported command to convert it into a source-backed Study by attaching a workspace afterwards.

## If something does not work

| What you see | What to do |
| --- | --- |
| The launcher closes immediately | Open PowerShell, enter `Set-Location -LiteralPath 'C:\OpenSci'`, then `.\Start-OpenSci.cmd`; keep the displayed error |
| Python 3.10+ required | Repeat step 2 and correct the full Python path in `runtime.local.json` |
| Coordinator directory unavailable | Check that `C:\OpenSci-Data` exists and matches `studies.local.json` |
| Missing workspace configuration | Check the exact name and location `C:\OpenSci-Data\config\hub.local.json` |
| JSON cannot be read | Check straight quotes, commas, UTF-8 and that the filename does not end in `.txt` |
| Configured Git executable is missing | For this discussion-only setup, leave `git` empty instead of keeping the example path |
| A save's outcome is unknown | Keep its `request_id` and follow [Recover a save](TROUBLESHOOTING.md#save-recovery) before repeating the operation |

See [Troubleshooting](TROUBLESHOOTING.md) for later workflows. Share the error text when asking for help, with keys and private details removed.

## Linux setup

Use Python 3.10+ and a writable records folder such as `/home/researcher/OpenSci-Data`. Create its `config` subfolder and copy `config/hub.study.example.json` there as `hub.local.json`. Replace the account and paths with your own. From the OpenSci installation folder, run:

```text
python3 -B scripts/hub.py --coordinator-root /home/researcher/OpenSci-Data menu
```

Continue with the same numbered menu. Linux does not use `runtime.local.json`; direct commands explicitly select the records folder. The Windows launcher reads `studies.local.json` for that selection.

The remaining sections are for command-based or source-dependent work. They are not prerequisites for your first discussion Study.

<a id="command-context"></a>
## Running the later examples

Direct Python examples use the session function below. Paste the complete block once into a PowerShell window and use `Invoke-OpenSci` in that same window. It selects the project's Python and Git, then restores PATH and the working directory after each call. It does not need to be added to your personal Profile.

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

The helper does not itself authorize SSH, model calls or study writes; the selected command determines the effect. Bare `python -B scripts/...` examples in reference chapters assume a configured interpreter, Git on the session PATH and the project root as the working directory. On Windows, pass those script arguments to `Invoke-OpenSci` as shown above. On Linux, use `/usr/bin/python3 -B` from `/home/researcher/OpenSci` and adapt paths. The remote copy is not designated to perform coordinator writes.

<a id="git-prerequisites"></a>
## Git prerequisites for source-dependent work

When the research workspace needs Git provenance, confirm the commit name, email and whether a shared Git repository will be used. Configure identity in the project repository rather than globally. Review the staged source, excluding machine configuration, credentials, real study state and run artifacts, then create the initial commit.

For source-dependent work, both source workspaces need the same clean commit from one Git history; the separated runtime and coordinator directories are not research source repositories. Independently initializing and committing identical files on both hosts does not establish a shared source baseline. Transfer one commit through an approved remote, clone or Git bundle. If a destination already contains files, inspect them and prepare a matching copy in a new directory. If `origin` is configured, use the same URL on both hosts because its digest is compared. Matching commits are still required if both origins are absent.

For a Git-backed Study, after both source copies are ready, use the [source-backed creation example](DAILY_USE.md#source-study). Do not invent identity, choose an unconfirmed origin or edit recorded source hashes merely to bypass a readiness check.

## Adding Zotero

Follow the [literature setup](LITERATURE.md) after preserving both applications' data. Menu option 9 can probe capabilities before a study exists. Literature writes use the Operation Service and require a Study and the appropriate literature grants; copying this release does not supply Git identity, create a study, grant access, enable paid models or complete production acceptance.

For independent record storage, ordinary Chat and full local/remote Work entry choices, follow [Study connections](STUDY_CONNECTION.md).
