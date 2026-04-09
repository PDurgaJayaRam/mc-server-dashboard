FROM itzg/minecraft-server

USER root

RUN apt-get update && apt-get install -y \
    python3 python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask flask-session mcrcon psutil gunicorn \
    --break-system-packages

COPY requirements_dashboard.txt .
RUN pip3 install --break-system-packages -r requirements_dashboard.txt

COPY dashboard.py /dashboard.py
COPY templates/ /templates/
COPY static/ /static/
COPY start.sh /start.sh

RUN chmod +x /start.sh

ENV PYTHONUNBUFFERED=1
ENV PORT=5000

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["/start.sh"]
