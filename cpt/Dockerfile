# Base image with CUDA 12.1 + cuDNN 8 — matches OVH AI Training GPU drivers
FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

WORKDIR /workspace

# Install Python deps first (cached layer if requirements unchanged)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy training scripts only — data and checkpoints are mounted at runtime
COPY train.py config.yaml eval_perplexity.py eval_qa.py qa_questions.py prepare_corpus.py ./

ENV PYTHONUNBUFFERED=1

# OVH AI Training mounts Object Storage volumes at paths defined in the job command.
# Expected layout at runtime:
#   /workspace/data/train.jsonl       ← mounted from OVH Object Storage
#   /workspace/data/held_out.jsonl    ← mounted from OVH Object Storage
#   /workspace/checkpoints/           ← mounted output volume (persisted after job)
#
# Launch command on OVH:
#   ovhai job run <image> \
#     --volume <bucket>/data@GRA/workspace/data:ro \
#     --volume <bucket>/checkpoints@GRA/workspace/checkpoints:rw \
#     -- python train.py --config config.yaml

CMD ["python", "train.py", "--config", "config.yaml"]
