ARG paynt-base=randriu/paynt:ci
FROM paynt-base

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install ipykernel joblib tensorboard
