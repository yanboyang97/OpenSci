# Environment Capture and Binding

## Capture and freeze environments

The demo needs Python 3.10+ and Git. Give optional components separate virtual environments; do not install scheduler/tracking dependencies into an already approved experiment interpreter. requirements-optional.txt is an optional list, not an accepted target-node lockfile or an instruction to install everything.

On the actual Linux node, select a stable absolute invocation path, then run capture_environment.py with that interpreter and an output under environments/*.local.json. Share the record through an authorized channel; pass it as prepare_task --environment with the actual --node hostname. Capture installs nothing and uses no network. Local JSON is outside Git and belongs in the controlled task archive. Preparation on the target can use --python to capture directly.

After real dependency installation and acceptance, separately retain pip freeze output, package sources and platform details; use package-hash locks or image digests when required. This fingerprint compares versions, not fully reconstructible environments. Capture a fresh Execution Environment record on the actual target after environment changes. Keep the virtual environment's absolute bin/python invocation path; executable_realpath is diagnostic and must not replace it. Do not choose the experiment interpreter by resolving readlink -f.

Preparation validates Linux/hostname; execution compares Python/packages, invocation/real paths, prefixes, OS and machine. Moving paths requires new tasks and approval even with unchanged package versions. Kernel/system-library/wheel/driver equivalence is not fully guaranteed by this example.

Literature metadata/API/index operations use the standard Python runtime. PDF text extraction optionally uses PyMuPDF; record its exact version and failed pages. Word/Zotero desktop, LaTeX and Quarto toolchains need separate local acceptance. The SSH literature worker uses only received evidence and its own configured provider references; do not copy Windows credentials, raw library storage or browser sessions. See [LITERATURE.md](../LITERATURE.md).
