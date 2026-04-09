FROM itzg/minecraft-server

USER root

# Install Python and dos2unix to fix line endings from Windows
RUN apt-get update && apt-get install -y \
    python3 python3-pip dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_dashboard.txt .
RUN pip3 install --break-system-packages -r requirements_dashboard.txt

COPY dashboard.py /dashboard.py
COPY templates/ /templates/
COPY static/ /static/
COPY start.sh /start.sh

# FORCE Linux line endings and set permissions
RUN dos2unix /start.sh && chmod +x /start.sh

# Enable unbuffered logging so errors show up instantly in ClawCloud
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
EXPOSE 25565

CMD ["/start.sh"]
