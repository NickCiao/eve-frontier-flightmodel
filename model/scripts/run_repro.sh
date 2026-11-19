#!/bin/bash
# Runs the PushT reproduction to 10 epochs. Resumes from the newest Lightning
# checkpoint, and restarts the run if the log stops moving for 10 minutes
# (a GPU driver error on 2026-11-18 left the process spinning with no output).
export STABLEWM_HOME=$HOME/.stable-wm
cd $HOME/code/le-wm && source .venv/bin/activate
RUN=$STABLEWM_HOME/checkpoints/pusht_repro
LOG=$STABLEWM_HOME/runs/pusht_repro.log
SUP=$STABLEWM_HOME/runs/pusht_repro_supervisor.log
for attempt in 1 2 3 4 5 6; do
  CK=$(ls -t $HOME/.cache/stable-pretraining/runs/*/*/*/checkpoints/last.ckpt 2>/dev/null | head -1)
  [ -n "$CK" ] && cp "$CK" $RUN/pusht_repro_weights.ckpt
  echo "$(date '+%F %T') attempt $attempt resume_from=$CK" >> $SUP
  python train.py data=pusht data.dataset.name=pusht_expert_train.h5 \
    output_model_name=pusht_repro subdir=pusht_repro trainer.max_epochs=10 \
    num_workers=6 loader.prefetch_factor=1 >> $LOG 2>&1 &
  PID=$!
  while kill -0 $PID 2>/dev/null; do
    sleep 60
    echo "$(date '+%F %T') $(free -m | awk 'NR==2{print "used="$3" shared="$5" avail="$7}')" >> $STABLEWM_HOME/runs/pusht_repro_mem.log
    AGE=$(( $(date +%s) - $(stat -c %Y $LOG) ))
    if [ $AGE -gt 600 ]; then
      echo "$(date '+%F %T') log stalled ${AGE}s, killing" >> $SUP
      pkill -KILL -P $PID; kill -KILL $PID; sleep 20
    fi
  done
  wait $PID; RC=$?
  echo "$(date '+%F %T') exited rc=$RC" >> $SUP
  if grep -q "max_epochs=10. reached" $LOG; then echo "$(date '+%F %T') finished" >> $SUP; exit 0; fi
  sleep 30
done
echo "$(date '+%F %T') gave up after 6 attempts" >> $SUP
