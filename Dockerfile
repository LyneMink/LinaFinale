FROM  openeuler/openeuler:24.03-lts

RUN dnf update -y && \
    dnf install -y python3 python3-pip && \
    dnf clean all

WORKDIR /app

COPY requirements.txt .
COPY main.py .
COPY synthese_vocale.py .
COPY detection.py .
COPY description_environnement.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "main.py" ]
