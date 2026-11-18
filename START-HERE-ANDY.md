# Chassis handoff for Andy

November 18, 2026 · Fictional working demo

Chassis gives you and Homer a shared set of venture, initiative and task records. You can edit a task in the browser. A compatible agent can update the same task through the Model Context Protocol (MCP). The plain-text files and their Git history travel with you.

## Start with one task

Open the sandbox when Joe sends the address and login. Select Cedar Rentals, double-click a launch task, rename it, and save. Reload to see the title again. Use Undo to bring it back. The sandbox contains fictional records and uses temporary storage. Use your own local copy for edits you want to keep.

The desktop canvas is on [the integration branch](https://github.com/jderomanis1/chassis/tree/94974a2725fa46ccd273868ac5fdd54c1877a1bc). The [source used for the handoff](https://github.com/jderomanis1/chassis/tree/329e0faa10df33998396795f2ab53c4829047867) includes the same application plus the hosting and persistence work from [draft PR #13](https://github.com/jderomanis1/chassis/pull/13). The default branch is an earlier checkpoint.

## Give this to Homer

> Homer, study this Chassis repo using the fictional examples. Start with this guide, the architecture, the acceptance evidence and the findings. Trace one task from its Markdown file through a connector update, its Git commit and the canvas. Tell me which pieces would help me run my ventures, which you would adapt, and which you would leave out. Explain why and point to a file or test for each recommendation. Flag anything you could not verify. Propose one small experiment I could try and what I would see if it worked. Let me choose before changing code, connecting accounts or bringing in real data.

If Homer cannot see the private repository, give him the extracted source folder in a workspace he can read. The demo includes a prepared local MCP read and write. Connecting your own Homer client is a separate step.

## What you can reuse

| Piece | What it does |
| --- | --- |
| Project records | One Markdown file per record, typed relationships, version checks and attributed Git commits. SQLite builds a disposable index of the working files. |
| Agent connector | Six local MCP tools list, read, search, create, create from a template and update. The caller's grants and clearance govern access through the API. |
| Desktop canvas | Seven fictional ventures with drill-down, search, dependencies, editing, Undo and saved layout. A file edit or agent update can appear in an open browser. |
| Design and tests | The original prototype, screenshots, source, fixtures, regression tests and acceptance ledger let a successor inspect how decisions became working behavior. |

## What was verified

The locked all-extras suite passed 731 Python tests on a clean copy of the exported application. Firefox opened all seven venture tiles, saved a Cedar title, retained it after reload and undid it. A real local MCP client then marked a Lumen task blocked. The open canvas updated and Git showed the chief-of-staff commit plus both canvas-editor commits. A separate local restart retained an Acme edit, its version and its exact commit. All three GitHub CI jobs passed on the first attempt. [CI run 81](https://github.com/jderomanis1/chassis/actions/runs/44397271893)

The hosted sandbox runs the earlier 3ff1106 build. Hosted evidence records a refused wrong password, an edit appearing in a second browser, a rejected cross-site write and return after more than 22 idle minutes. The independent hosted Git checks, a chief write in the running service and recovery after an actual hosted restart remain open. The disk-backed variant passed a Docker restart and reset rehearsal. Its disk has not been attached to the sandbox. [Acceptance details](evidence/acceptance.md)

## Where to begin on your own machine

The downloadable kit includes a 44-second walkthrough and a launcher. On Linux, macOS or Windows with WSL, install Git and uv, unzip the kit, open a terminal in its top-level folder and run the command below. Python 3.12 and the locked dependencies must be available or downloadable on first use. The built frontend is included.

```sh
sh run-local-demo.sh
```

Open http://127.0.0.1:8765/ in a desktop browser. Ctrl+C stops it. Running the same command reopens your local demo. It stores its vault and local credentials under ~/.chassis-andy-demo/. Keep the credentials private. To try a separate board, pass --state followed by a new folder path.

If you only have the repository, use the same source commit and run the following from the repo root in a POSIX shell.

```sh
uv sync --locked --all-extras --python 3.12
umask 077
demo_dir=$(mktemp -d)
.venv/bin/chassis demo-init "$demo_dir/vault" > "$demo_dir/credentials.json"
token_for() {
  .venv/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))["credentials"][sys.argv[2]])' "$demo_dir/credentials.json" "$1"
}
export CHASSIS_PORTAL_VIEWER_AGENT=reviewer
export CHASSIS_AGENT_TOKEN="$(token_for reviewer)"
export CHASSIS_PORTAL_EDITOR_AGENT=canvas-editor
export CHASSIS_PORTAL_EDITOR_TOKEN="$(token_for canvas-editor)"
.venv/bin/chassis portal --host 127.0.0.1 --port 8765 --vault "$demo_dir/vault" --allow-writes
```

## If you decide to build

Reproduce one human edit and one agent edit on a machine you control, then choose the next workflow. A native Grok mobile write, voice control, chat import and optional Miro export remain separate work. The current demonstration uses fictional data. Before introducing actual ventures, verify the intended access rules, filesystem protection, backup and restore. Someone with direct access to the files or Git history can read the plaintext contents.

For technical details, open [project handoff](CHASSIS_PROJECT_HANDOFF.md), [architecture](docs/ARCHITECTURE.md), [canvas decision](docs/PORTAL-ADR.md), [MCP handlers](src/chassis/tool_handlers.py), [browser test](tests/e2e/live.spec.mjs), [findings](FINDINGS.md) and [deployment runbook](deploy/README.md). The existing sandbox's compute approval runs through December 1, 2026.
