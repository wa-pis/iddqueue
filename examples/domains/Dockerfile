FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY iddqueue ./iddqueue
COPY examples/domains ./examples/domains
RUN pip install --no-cache-dir '.[binary]'
CMD ["dramatiq", "--use-spawn", "--processes", "2", "--threads", "4", "examples.domains.worker"]
