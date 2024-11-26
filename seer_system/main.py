from flask import Flask
from asgiref.wsgi import WsgiToAsgi
from flask_restx import Api, Resource

app = Flask(__name__)
api = Api(
    app, title="My API", description="This is a sample API with Swagger documentation"
)


@app.route("/")
def home():
    return "Hello, Flask with Uvicorn!"


@api.route("/hello")
class HelloWorld(Resource):
    def get(self):
        """Returns a simple Hello World message"""
        return {"message": "Hello, World!"}


# Wrap the WSGI app to ASGI
asgi_app = WsgiToAsgi(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
