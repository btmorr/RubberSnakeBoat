# poetry package manager docs: https://python-poetry.org/docs/
from flask import Flask


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p>"

    return app


if __name__ == '__main__':
    print("main")


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
