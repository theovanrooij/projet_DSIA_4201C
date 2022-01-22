FROM python:3.8

RUN mkdir /home/dev/ && mkdir /home/dev/code/

WORKDIR /home/dev/code/

COPY  . .

RUN chmod +x Pipfile

RUN  pip install --upgrade pip &&  pip install pipenv && pipenv install --dev --skip-lock

CMD ["pipenv", "run", "jupyter", "notebook", "--ip=0.0.0.0", "--no-browser", "--allow-root", "--NotebookApp.token=''"]