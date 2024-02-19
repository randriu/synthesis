ARG paynt_base=randriu/paynt:ci
FROM $paynt_base

RUN pip install torch==2.1.*

RUN pip install ipykernel joblib tensorboard==2.15.* einops==0.7.* gym==0.22.* pygame==2.5.*

WORKDIR /opt/learning
