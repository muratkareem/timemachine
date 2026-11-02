# Your first protected session

Install published v0.2.0 using [INSTALL.md](INSTALL.md), then open a disposable project
for this walkthrough. Python 3.12+ and macOS/Linux are supported.

```sh
mkdir timemachine-demo
cd timemachine-demo
timemachine init
printf 'before\n' > hello.txt
timemachine status
```

Initialization only sets up TimeMachine. **No backup exists yet.**
Run a command through TimeMachine to save files before and after it:

```sh
timemachine run -- python3 -c "from pathlib import Path; Path('hello.txt').write_text('after\n')"
timemachine tui
```

Simple mode opens by default. Read the status, choose hello.txt, and inspect
What Changed. Click **Undo AI Changes**: review the exact paths and then choose
Apply changes. Cancel is selected initially. hello.txt returns to `before`.
Click **Redo Changes** and confirm to return to `after`.

You can replace the Python command with any installed coding agent and arguments:
`timemachine run -- codex`, for example. No specific agent is required. Agents have
their own authentication and billing. Start commands in your project terminal;
Help gives instructions and never launches a command automatically.

To try a conflict, exit the UI, edit hello.txt yourself and reopen it. Undo review
will refuse to overwrite the newer edit. Keep that edit; use Help and the
[recovery guide](RECOVERY.md) for next steps. Unrelated files remain untouched
by session Undo/Redo. Pause external writers before reviewing or applying recovery.

**Help (?)** explains every step. **Advanced (a)** reveals the full history,
snapshot IDs, storage and file metadata; **Simple (a)** returns. Mode selection is
session-local and never changes project metadata. Tab moves focus, arrows select,
Enter opens, and Escape cancels or returns to History. Buttons support the mouse.
Use **1 History / 2 Files / 3 Diff** on a small terminal. **t** changes the theme.

To make a manual save: `timemachine checkpoint -m 'Before my changes'`.
For an unfinished run/restore: preserve the store and run `timemachine doctor`.
Nothing resumes automatically. A checkpoint is a saved point in time, not a live backup.

See [the UI guide](PIXEL_UI_GUIDE.md) for advanced comparisons, selective file
restore, preview limits and diagnostics. The [safety contract](SAFETY.md) defines
exactly which files and metadata TimeMachine can recover.
