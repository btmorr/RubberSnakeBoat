FROM python:3-alpine

WORKDIR /app

COPY . .

# For a real install, this would be separated into install vs run dockerfiles,
# and would not use poetry for environment or install. Dependencies can be installed
# directly via pip, and then run would be handled by a WGSI server such as gunicorn
ENV POETRY_HOME /opt/poetry
RUN python3 install-python-poetry.py --version 1.5.1
RUN $POETRY_HOME/bin/poetry install
CMD $POETRY_HOME/bin/poetry run flask run --host=0.0.0.0
