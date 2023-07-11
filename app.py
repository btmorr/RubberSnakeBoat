from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p>"

    return app


if __name__ == '__main__':
    print("Run RubberSnakeBoat using `flask run`")
