#!/bin/bash
# Addendum J: all Gemini runs, Flash first then Argon. Logs to runs/addendumJ.log. Budget guard per step via max_usd.
cd /Users/jason/workspace/nano-next/food-evolve
export PYTHONWARNINGS=ignore
run() { echo "[$(date '+%F %T')] $*"; "$@" 2>&1 | grep -v "^WARNING" ; }
for t in flash pro; do
  run python3 -m fe.intake run candidates/intake/dual_direct_gemini_$t.py all 25
  run python3 -m fe.evaluate candidates/gpt/b0_direct_gemini_$t.py --split acetada_intake --final --max-usd 15 --workers 12
  run python3 -m fe.intake run candidates/intake/sub_direct_gemini_$t.py all 15
  run python3 -m fe.intake run candidates/intake/dual_simple_gemini_$t.py all 15
  run python3 -m fe.intake run candidates/intake/before_struct_gemini_$t.py all 15
  run python3 -m fe.intake run candidates/intake/dual_direct_gemini_$t.py pilot 5 1
  run python3 -m fe.intake run candidates/intake/dual_direct_gemini_$t.py pilot 5 2
  run python3 -m fe.intake run candidates/intake/dual_high_gemini_$t.py pilot 8
done
echo "[$(date '+%F %T')] ALL DONE"
