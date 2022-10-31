#! /bin/sh

#CUDA_VISIBLE_DEVICES=0,1 \
TOKENIZERS_PARALLELISM=true \
HF_DATASETS_CACHE=~/.cache/huggingface/datasets \
python run.py
