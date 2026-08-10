FROM us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:1.8.0

COPY tools.yaml /app/tools.yaml

CMD ["--config", "/app/tools.yaml", "--address", "0.0.0.0", "--port", "5000", "--disable-reload", "--allowed-hosts", "localhost,127.0.0.1", "--allowed-origins", "http://localhost:5000,http://127.0.0.1:5000"]
