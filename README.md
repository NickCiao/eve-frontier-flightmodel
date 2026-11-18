# eve-frontier-flightmodel

Two ways of flying a ship in EVE Frontier, compared on one short approach task:

- **A hand-written controller.** A few rules that read numbers off the screen and steer.
- **A small learned world model with a planner.** The model is [LeWM](https://github.com/lucas-maes/le-wm). It learns from recordings how the view changes in response to control inputs, and a planner searches it for actions that reach a goal.

Both pilots use only what is on the screen.

## Where things live

- **What the project is, its stages, and its ground rules:** the Notion page [EVE AI Program: Flight World Model Experiment](https://app.notion.com/p/418e33e50bb181658113d9561988b084).
- **Status, next work, blockers, and questions:** the Linear project [EVE Frontier Flight Model](https://linear.app/nciao/project/eve-frontier-flight-model-33869fa89756).
- **Code and setup notes:** this repo.

## Layout

The work is split between two sessions on one Windows PC.

| Directory | Runs on | Holds |
| --- | --- | --- |
| `capture/` | Windows | The recording tool, the state readers, the input tool, and the live loop |
| `model/` | WSL | LeWM training, the dataset converter, and offline evaluation |
| `docs/` | | Setup notes and what was confirmed, with dates |

Directories are created when their first code lands.

## Recordings

Recordings are kept out of git. They live in `recordings/` at the repo root, which is ignored. Nothing recorded from the game is published without a separate decision.

## Setup

- LeWM on WSL: see [docs/lewm-setup.md](docs/lewm-setup.md).
