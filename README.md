# RubberSnakeBoat

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/btmorr/RubberSnakeBoat/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/btmorr/RubberSnakeBoat/tree/main)

This is a toy implementation of a k-v store database using the [Raft protocol](https://raft.github.io/) in Python

This project uses the following tools:
- [poetry](https://python-poetry.org/docs/)
- [fastapi](https://fastapi.tiangolo.com)
- [pytest](https://docs.pytest.org)
- [mypy](https://mypy.readthedocs.io/en/stable/index.html)

To install, do:

```commandline
poetry install
```

To test, do:

```commandline
pytest --cov-report term-missing --cov
mypy
```

To run locally, do:

```commandline
poetry shell
uvicorn main:app --reload
```

To build in a container, do:

```commandline
docker build -t tag .
```
To run in a container, do:

```commandline
docker run -p 8000:8000 -t tag
```

To interact with a running server, navigate to [localhost:8000/docs](http://localhost:8000/docs) (or wherever the server is running)

## Troubleshooting

If you are using Windows/PowerShell, and you encounter an error that says "running scripts is disabled on this system", you may need to run this or a similar command before running `poetry` commands:

```commandline
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

This is designed to allow `poetry` to run scripts, without unnecessarily disabling security restrictions -- it only allows signed scripts, and only for the current PowerShell process. See [the Microsoft article on execution policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.3).
