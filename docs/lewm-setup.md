# LeWM setup on WSL

How LeWM was installed and run on its own PushT environment, and what the code's settings are. Checked on 2026-11-18 on Nick's PC (WSL2 Ubuntu 24.04, RTX 5090, 30 GB of memory visible to WSL).

LeWM is kept as a separate clone at `~/code/le-wm`, at commit `8edfeb3` (2026-05-22). It is not vendored into this repo.

## Install

```bash
git clone https://github.com/lucas-maes/le-wm ~/code/le-wm
cd ~/code/le-wm
uv venv --python=3.10
source .venv/bin/activate
uv pip install 'stable-worldmodel[train,env,format]' 'transformers<5'
export STABLEWM_HOME=$HOME/.stable-wm
```

Three things differ from LeWM's README:

- **The `format` extra is needed.** Without it the HDF5 reader is not registered and `eval.py` fails.
- **`transformers` must be below 5.** The published checkpoints were saved with the 4.x ViT, whose layer names differ from 5.x. Installing it in the same command as `stable-worldmodel` lets uv pick matching versions of `datasets` and `huggingface-hub`.
- **`STABLEWM_HOME` must be set.** The README says the default is `~/.stable-wm`. The installed library (stable-worldmodel 0.1.1) defaults to `~/.stable_worldmodel`.

Versions that worked: stable-worldmodel 0.1.1, stable-pretraining 0.1.8, torch 2.14.1+cu130, lightning 2.6.6.

## Data and checkpoints

The library looks for datasets in `$STABLEWM_HOME/datasets/` and checkpoints in `$STABLEWM_HOME/checkpoints/`.

```bash
hf download quentinll/lewm-pusht --repo-type dataset --local-dir $STABLEWM_HOME/dl_pusht
# decompress pusht_expert_train.h5.zst to $STABLEWM_HOME/datasets/pusht_expert_train.h5
hf download quentinll/lewm-pusht --local-dir $STABLEWM_HOME/checkpoints/pusht_published
```

The PushT dataset is 13 GB compressed and 46 GB as HDF5: 2,336,736 frames in 18,685 episodes, with `pixels` (224 by 224), `action` (2 numbers), `proprio`, and `state`.

The `zstd` command is not installed on this machine. The Python `zstandard` package in the venv decompresses it.

A checkpoint is a folder holding one `weights.pt` and a `config.json`. The published one loads directly, with no conversion step. It has 18.0M parameters.

## Evaluate

```bash
python eval.py --config-name=pusht.yaml policy=pusht_published
```

The published PushT checkpoint reached a **92% success rate** over 50 episodes (seed 42). The run took 64 seconds. One round of planning for all 50 episodes at once took about 4 seconds.

## Train

```bash
python train.py data=pusht data.dataset.name=pusht_expert_train.h5 \
  output_model_name=pusht_repro subdir=pusht_repro \
  trainer.max_epochs=10 num_workers=6 loader.prefetch_factor=1
```

- **The dataset name needs an override.** `config/train/data/pusht.yaml` names a `.lance` dataset. The published data is `.h5`.
- **The default loader settings run out of memory here.** With 6 workers and a prefetch of 3, the run was killed after filling about 15 GB of shared memory. A prefetch of 1 fixes it.
- **Six workers, not eight.** Eight workers ran at 5.6 batches a second but left only about 4 GB of memory spare with swap full. Six workers run at 4.5 batches a second with about 10 GB spare.
- **Ten epochs, not the config's 100.** The paper trains each world model for 10 epochs.
- **Speed is limited by data loading.** The GPU sits at 50 to 75%. One epoch is 13,933 batches, about 57 minutes with six workers. Training uses about 13.7 GB of GPU memory.
- **WandB is off by default** in the local launcher (`wandb.enabled: False`).

To evaluate a trained model, put the last `weights_epoch_N.pt` and `config.json` in a folder of their own under `checkpoints/`. The loader refuses a folder with more than one `.pt` file.

## Reproduction result

Trained from scratch on PushT on 2026-11-18 and 2026-11-19, then evaluated with the same command and seed as the published checkpoint.

| Model | PushT success over 50 episodes |
| --- | --- |
| Published checkpoint | 92% |
| Trained here, 10 epochs | 92% |

- **GPU time:** about 9.6 hours. One epoch at 8 workers (47 minutes), nine at 6 workers (57 minutes each), and about 13 minutes lost to the hang below.
- **Final validation losses:** prediction 0.0034, SIGReg 1.32.

## GPU driver hang

The first training run stopped making progress at 17:09 on 2026-11-18, in its second epoch. Windows logged one NVIDIA driver error in the same second (`nvlddmkm` event 153, "Error occurred on GPUID: 100"). The training process did not exit. It kept one CPU thread busy with the GPU idle and wrote nothing for six hours.

The cause is not known. It was the only such event in eight days of the Windows system log. WSL memory was tight at the time. The restarted run, with six workers, ran nine epochs with no further error.

Long runs should be started under a supervisor that restarts them when the log stops moving. The one used here, [`model/scripts/run_repro.sh`](../model/scripts/run_repro.sh), resumes from the newest Lightning checkpoint, which the trainer writes once an epoch under `~/.cache/stable-pretraining/runs/`. To resume, copy that `last.ckpt` to `$STABLEWM_HOME/checkpoints/<subdir>/<output_model_name>_weights.ckpt` before starting `train.py`.

## Settings in the code

| Setting | Value | Where |
| --- | --- | --- |
| Image size | 224 by 224 | `img_size` in `config/train/lewm.yaml` |
| Frames grouped into one step | 5 | `frameskip` in `config/train/data/*.yaml`, `action_block` in `config/eval/*.yaml` |
| Past steps the predictor sees | 3 | `history_size` in `config/train/lewm.yaml` |
| Steps the planner looks ahead | 5 | `plan_config.horizon` in `config/eval/*.yaml` |
| Vector size | 192 | `embed_dim` in `config/train/lewm.yaml` |
| Steps predicted ahead in training | 1 | `num_preds` in `config/train/lewm.yaml` |
| Planner samples, rounds, kept | 300, 30, 30 | `config/eval/solver/cem.yaml` |
| Planned steps carried out before planning again | 5 | `plan_config.receding_horizon` in `config/eval/*.yaml` |
| Goal distance and budget in evaluation | 25 frames, 50 frames | `eval.goal_offset_steps`, `eval.eval_budget` |

The action given to the model for one step is the five per-frame actions joined together, so its size is 5 times the per-frame action size (10 for PushT).
