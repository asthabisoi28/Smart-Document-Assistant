import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.embeddings import EmbeddingService
import numpy as np

embed_svc = EmbeddingService()

# Chunk 3 WITHOUT context:
chunk3_raw = "Python 3.11, FastAPI, Celery\n- Database: PostgreSQL, Redis\n- Machine Learning: PyTorch, HuggingFace Transformers for resume parsing\n- Infrastructure: Docker, Kubernetes, AWS ECS"

# Chunk 3 WITH Section Context:
chunk3_with_context = "[SmartHire Platform | Technical Stack]\nPython 3.11, FastAPI, Celery\n- Database: PostgreSQL, Redis\n- Machine Learning: PyTorch, HuggingFace Transformers for resume parsing\n- Infrastructure: Docker, Kubernetes, AWS ECS"

q_orig = "what tech stacks are used in SmartHire project?"
q_exp = "what technologies tools tech stack built using SmartHire project?"

v_q_orig = embed_svc.embed_query(q_orig)
v_q_exp = embed_svc.embed_query(q_exp)

v_c3_raw = embed_svc.embed_query(chunk3_raw)
v_c3_ctx = embed_svc.embed_query(chunk3_with_context)

score_raw_orig = float((v_q_orig @ v_c3_raw.T)[0, 0])
score_ctx_orig = float((v_q_orig @ v_c3_ctx.T)[0, 0])
score_ctx_exp  = float((v_q_exp  @ v_c3_ctx.T)[0, 0])

print(f"Chunk 3 Raw + Orig Query Score:          {score_raw_orig:.4f}")
print(f"Chunk 3 With Context + Orig Query Score: {score_ctx_orig:.4f}")
print(f"Chunk 3 With Context + Exp Query Score:  {score_ctx_exp:.4f}")
