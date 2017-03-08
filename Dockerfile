FROM python:3.5.1-alpine

COPY . /src

WORKDIR /src

RUN pip install -r requirements.txt

CMD [ "python", "-u", "./app.py"]
