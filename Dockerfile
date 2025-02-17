FROM quay.io/jupyterhub/k8s-hub:4.1.0

COPY tljh_repo2docker*.whl .
USER root
RUN python3 -m pip install tljh_repo2docker*.whl

USER jovyan