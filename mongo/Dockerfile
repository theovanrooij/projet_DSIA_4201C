FROM mongo

RUN apt-get update && apt-get install -y curl

COPY feed /feed

ENTRYPOINT bash /feed

