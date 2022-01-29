FROM python:3.8

RUN mkdir /home/app/

WORKDIR /home/app/

COPY . . 

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT bash launchAPP