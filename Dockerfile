FROM  openeuler/openeuler:24.03-lts

RUN dnf update -y && \
    dnf install -y python3 python3-pip && \
    dnf clean all

WORKDIR /app

RUN git clone -b v0.5.0 https://github.com/mindspore-lab/mindocr.git /app/mindocr && \
    cd /app/mindocr && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .


RUN git clone https://github.com/mindspore-lab/mindyolo.git /app/mindyolo && \
    cd /app/mindyolo && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

COPY requirements.txt .
COPY main.py .
COPY synthese_vocale.py .
COPY detection.py .
COPY description_environnement.py .
COPY capteur.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3", "main.py" ]
