# See .devcontainer/Dockerfile.dev.
FROM webis/longeval-pyterrier-baseline:dev-0.0.1

RUN pip3 uninstall -y ir-datasets-longeval \
	&& pip3 install ir-datasets-longeval

ADD baseline.py /

