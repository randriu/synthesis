ARG paynt_base=randriu/paynt:ci
FROM $paynt_base

RUN pip install torch

RUN pip install ipykernel joblib tensorboard einops
