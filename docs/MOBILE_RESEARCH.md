# Research from Your Phone

[Handbook](../DOCUMENTATION.md) · [Basic setup](GETTING_STARTED.md)

Use the ChatGPT phone app to continue research on your own computer while traveling. You describe the work and review the outcome on your phone. The connected computer runs the task and uses the OpenSci setup already available there.

## Before you begin

Have OpenSci and a Study ready on the computer, following [Getting Started](GETTING_STARTED.md). Connect its assistant to that Study through [OpenSci Study](PLUGINS.md), or keep the configured OpenSci command entry available to the local task. Any literature library, model service or research software used by the task also needs its normal setup.

The phone and computer use the same ChatGPT account and workspace. Use versions of the mobile and desktop apps that provide remote computer access. The vendor currently documents the phone entry for iOS; availability follows the account and workspace. See [OpenAI's mobile guide](https://learn.chatgpt.com/docs/mobile) for the supported clients.

## Connect your computer once

1. In the desktop application's settings, open **Connections → Control this Mac or PC**, then choose **Set up** or **Add**.
2. Follow the device-linking instructions and any requested verification. Scan the displayed code with your phone and approve access to your own computer.
3. In the ChatGPT phone app, open **Codex**; an app that still labels this entry **Remote** uses that name instead. Choose the connected computer and the project containing your research work. Keep the computer awake and online.

These are host features; OpenSci does not establish the device connection itself. The [official remote-connections guide](https://learn.chatgpt.com/docs/remote-connections) explains device access and its settings. A linked Mac does not change OpenSci's own supported-platform requirements; this release's beginner setup uses Windows.

## Continue an existing Study

Open an existing task on the connected computer, or start one in the intended project. Give the Study ID and the work you want done. For example:

> Continue Study STUDY-001 in OpenSci. Read its latest saved goal and progress, summarize the open questions, and propose the next useful step.

After configuring literature access, you could ask:

> In the Zotero collection already linked to this Study, compare the abstracts of the papers I selected. List points of agreement and disagreement, with item references. Mark any unavailable evidence.

To preserve the outcome:

> Save the conclusions, unresolved questions and next steps to this OpenSci Study. Return the save receipt and the updated Study revision.

Replace `STUDY-001` with your own ID. The save receipt confirms a recorded change. Conversation history remains in ChatGPT; saved research progress remains in the Study, so another authorized session can continue from it.

## What runs while you are away

Authorized tasks can use the connected computer's configured tools and resources. You can direct work, review updates and respond when approval is needed. OpenSci records the relevant research progress; connecting a phone does not add a scheduler or automatically start experiments.

For a long analysis, ask for its task or job ID and the location of its output. After an interruption, follow that same job. A disconnected phone is not evidence that the computer stopped, and a displayed conversation is not proof that new progress was saved.

Experimental execution still follows OpenSci's independent human-approval procedure. The supplied runner supports the public Estimator Comparison, one CPU thread and no GPU. Other research software requires an implemented integration and its own access and resource settings.

## Ordinary Chat and computer tasks

Remote computer access lets you continue a task running on the computer. The [private MCP connection](PLUGINS.md#ordinary-chat) instead lets a supported ChatGPT conversation call OpenSci's bounded Study tools. It does not provide general access to the computer's screen, files or commands. Choose the connection that provides the work you need; creating one does not automatically configure the other.

If a task cannot reach a library or tool, check its configuration on the selected computer. If a save result is unknown, preserve its original request ID and retrieve that receipt before trying again. See [Troubleshooting](TROUBLESHOOTING.md).
