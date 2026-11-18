# Notes for build sessions

Read the Notion page [EVE AI Program: Flight World Model Experiment](https://app.notion.com/p/418e33e50bb181658113d9561988b084) first. It says what the project is. Linear says what to work on: project [EVE Frontier Flight Model](https://linear.app/nciao/project/eve-frontier-flight-model-33869fa89756).

## Who does what

- **Windows session:** everything that touches the game client. Capture, the readers, input, and the live loop. Code in `capture/`.
- **WSL session:** LeWM, training, and offline evaluation. Code in `model/`.

## Rules

- Automated input is sent only on Nick's own account, with Nick at the keyboard.
- Both pilots use only what is on the screen. The client's own logs are saved only where that needs no change to the client, and neither pilot sees them.
- The world model is never trained on the Stage 2 readings without Nick's decision.
- Recordings, frames, datasets, and checkpoints are never committed. This repo is public.
- Publishing any footage, frames, or data needs Nick's decision first.
- No cloud GPU spending.
- Secrets go in `.env`, which is ignored. Never commit a key.

## Conventions

- Python, managed with uv. One `.venv` per environment.
- Start commit messages with the Linear issue ID, e.g. `NIC-125: add PushT eval notes`.
- Record confirmed facts in `docs/` with the date they were checked.
- At the end of a session, post a status update on the Linear project.
