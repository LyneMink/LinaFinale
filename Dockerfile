FROM  openeuler/openeuler:24.03-lts

RUN dnf update -y && \
    dnf install -y python3 python3-pip && \
    dnf clean all

WORKDIR /app

COPY /home/nzinga/Documents/ProjetFinalLINA/mindyolo /app

WORKDIR /app/mindyolo
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

WORKDIR /app
COPY /home/nzinga/Documents/ProjetFinalLINA/checkpoints /app

COPY requirements.txt .
COPY main.py .
COPY synthese_vocale.py .
COPY detection.py .
COPY description_environnement.py .
COPY capteur.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3", "main.py" ]
