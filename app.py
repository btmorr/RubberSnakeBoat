from flask import Flask, make_response, request
from store import Store


def create_app() -> Flask:
    app = Flask(__name__)
    app.store = Store()

    @app.get("/")
    def db_get():
        """reads the specified value"""
        k = request.args.get('key')
        if k:
            v = app.store.read(k)
            if v:
                res = make_response(v, 200)
            else:
                res = make_response("not found", 404)
        else:
            res = make_response("'key' argument must be specified", 400)
        return res

    @app.post("/")
    def db_upsert():
        """inserts the specified value without checking for previous existence"""
        k = request.args.get('key')
        v = request.args.get('value')
        if k and v:
            app.store.upsert(k, v)
            res = make_response("", 201)
        else:
            res = make_response("error: 'key' and 'value' arguments must both be specified", 400)
        return res

    @app.delete("/")
    def db_delete():
        """deletes specified key without checking for existence"""
        k = request.args.get('key')
        if k:
            app.store.delete(k)
            res = make_response("", 204)
        else:
            res = make_response("'key' argument must be specified", 400)
        return res

    return app


if __name__ == '__main__':
    print("Run RubberSnakeBoat using `flask run` or use a WSGI server such as gunicorn")
