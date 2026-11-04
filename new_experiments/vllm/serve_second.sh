#!/bin/bash
# Second Qwen3.8-27B instance to double throughput for the inspection probes (GPU chosen at launch).
GPU=${1:-0}; PORT=${2:-8211}
export CUDA_VISIBLE_DEVICES=$GPU
export LD_LIBRARY_PATH=/usr/local/cuda-13.0/lib64
export PYTHONPATH=/dataDisk/home/thanhdo/failure-attribution-datasets/new_experiments/vllm/pyshim
exec /dataDisk/home/thanhdo/.local/bin/vllm serve /dataDisk/home/thanhdo/hub/Qwen/Qwen3.8-27B \
  --served-model-name qwen3.8-27b --port $PORT --dtype bfloat16 --gpu-memory-utilization 0.90 \
  --max-model-len 200000 --max-num-seqs 32 --enable-prefix-caching --generation-config vllm --seed 0 \
  --limit-mm-per-prompt '{"image":0,"video":0}' --reasoning-parser qwen3 \
  --speculative-config '{"method":"qwen3_5_mtp","num_speculative_tokens":2}'
