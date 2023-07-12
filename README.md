# RubberSnakeBoat

This is a toy implementation of a k-v store database using the [Raft protocol](https://raft.github.io/) in Python

This project uses the following tools:
- [poetry](https://python-poetry.org/docs/)
- [flask](https://flask.palletsprojects.com)
- [pytest](https://docs.pytest.org)
- [mypy](https://mypy.readthedocs.io/en/stable/index.html)

To install, do:

```commandline
poetry install
```

To test, do:

```commandline
poetry run pytest
mypy
```

To run locally, do:

```commandline
poetry shell
flask run
```

To build in a container, do:

```commandline
docker build -t tag .
```
To run in a container, do:

```commandline
docker run -p 5000:5000 -t tag
```

## Troubleshooting

If you are using Windows/PowerShell, and you encounter an error that says "running scripts is disabled on this system", you may need to run this or a similar command before running `poetry` commands:

```commandline
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

This is designed to allow `poetry` to run scripts, without unnecessarily disabling security restrictions -- it only allows signed scripts, and only for the current PowerShell process. See [the Microsoft article on execution policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.3).
