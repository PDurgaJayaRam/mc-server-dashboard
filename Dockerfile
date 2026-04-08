FROM itzg/minecraft-server

USER root

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_dashboard.txt .
RUN pip3 install --break-system-packages -r requirements_dashboard.txt

COPY dashboard.py /dashboard.py
COPY templates/ /templates/
COPY static/ /static/

# Start script that runs both
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
