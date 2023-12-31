FROM python:3-alpine

WORKDIR /app

COPY . .

# For a real install, this would be separated into install vs run dockerfiles,
# and would not use poetry for environment or install. Dependencies can be installed
# directly via pip
ENV POETRY_HOME /opt/poetry
RUN python3 install-python-poetry.py --version 1.5.1
RUN $POETRY_HOME/bin/poetry install
CMD $POETRY_HOME/bin/poetry run uvicorn main:app --host 0.0.0.0
