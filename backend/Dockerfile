FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

WORKDIR /app/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/stable.txt" && \
    curl -LO "https://dl.k8s.io/release/$(cat stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/ && \
    rm stable.txt

ENV PYTHONPATH=/app

COPY ./scripts/ /app/

COPY ./alembic.ini /app/

COPY ./prestart.sh /app/

COPY ./tests-start.sh /app/

COPY . /tmp/build/

RUN if [ -f /tmp/build/kubeconfig.yaml ]; then \
    cp /tmp/build/kubeconfig.yaml /app/; \
    echo "kubeconfig.yaml copied"; \
    echo "export KUBECONFIG=/app/kubeconfig.yaml" >> /etc/bash.bashrc; \
    else \
    echo "kubeconfig.yaml not found, continuing build..."; \
    fi

COPY ./app /app/app

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
