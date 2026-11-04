#!/bin/bash
# Local judge/assistant model for the experiments. One GPU only (GPU 5).
# Qwen3.8-27B is a hybrid linear/full-attention Qwen3.5-arch model (262k positions), so a 200k context fits one H200.
export CUDA_VISIBLE_DEVICES=5
# mpmath shim: see pyshim/ (sandbox hides files named libhyper*)
export PYTHONPATH=/dataDisk/home/thanhdo/failure-attribution-datasets/experiments/vllm/pyshim${PYTHONPATH:+:$PYTHONPATH}
exec vllm serve /dataDisk/home/thanhdo/hub/Qwen/Qwen3.8-27B \
  --served-model-name qwen3.8-27b \
  --port 8210 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 200000 \
  --max-num-seqs 16 \
  --enable-prefix-caching \
  --generation-config vllm \
  --seed 0 \
  --limit-mm-per-prompt '{"image":0,"video":0}' \
  --reasoning-parser qwen3 \
  --speculative-config '{"method":"qwen3_5_mtp","num_speculative_tokens":2}'
