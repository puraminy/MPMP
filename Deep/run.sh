#! /bin/sh

CUDA_VISIBLE_DEVICES=1 \
TOKENIZERS_PARALLELISM=false \
HF_DATASETS_CACHE=~/.cache/huggingface/datasets \
python run.py
