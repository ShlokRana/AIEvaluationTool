FROM python:3.11-slim

RUN mkdir -p /usr/src/app/
RUN mkdir -p /models/
WORKDIR /usr/src/app/

COPY requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

# logger.py is hard-link to the logger.py in the utils directory
COPY voice_layer /usr/src/app/
COPY generator.py /usr/src/app/
COPY logger.py /usr/src/app/
COPY main.py /usr/src/app/
COPY safety.py /usr/src/app/
COPY translator.py /usr/src/app/

EXPOSE 16000

CMD ["python3", "/usr/src/app/main.py"]

