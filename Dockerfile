FROM python:3.10.14

RUN mkdir /app

WORKDIR /app

COPY . .

RUN pip install -r ./requirements.txt

EXPOSE 5000

ENTRYPOINT [ "flask", "--app", "app", "run", "--host", "0.0.0.0" ]