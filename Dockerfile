FROM python:3.9-slim-buster

WORKDIR /app

# Build python libraries
RUN pip3 install poetry==1.1.10
COPY pyproject.toml poetry.lock ./
# DON'T create a virtual environment
# because the child process would be a zombie
# if it was executed via `poetry run`.
RUN mkdir cndl
COPY cndl/__init__.py cndl
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev

COPY cndl cndl

CMD ["cndl"]
