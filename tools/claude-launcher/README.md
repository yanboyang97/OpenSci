# Claude Development Launcher

## Built-in development launcher

This Windows PowerShell 7 launcher explicitly selects DeepSeek or Kimi. Follow [the full guide](../../CLAUDE_LAUNCHER.md). From the project root use Start-OpenSci.ps1 with LauncherAction Setup, ClaudeProvider deepseek/kimi, or LauncherAction Doctor plus ClaudeProvider kimi.

Setup records the local native CLI and DPAPI credential-file references, refuses overwrite and does not copy keys. Dot-sourcing init.ps1 registers current-session functions without editing Profile. Machine mapping and credentials stay outside Git/delivery. Provider data declares models/endpoints; local schema/decryption checks still need separate live-service acceptance. Automated text review uses independent Vertex settings. Development launch never changes study/compute bindings or approves experiments.
