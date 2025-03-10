FROM arm32v7/python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY main.py .
COPY synthese_vocale .
COPY detection.py .
COPY description_environnement.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "main.py" ]
