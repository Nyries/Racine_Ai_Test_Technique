FROM python:3.11-slim

WORKDIR /workspace

# PyTorch with CUDA 12.1 runtime bundled in the wheel
RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY train.py config.yaml eval_perplexity.py eval_qa.py eval_hellaswag.py qa_questions.py prepare_corpus.py ./
COPY data/ ./data/

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/tmp/huggingface
ENV TRANSFORMERS_CACHE=/tmp/huggingface
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

CMD ["python", "train.py", "--config", "config.yaml"]
