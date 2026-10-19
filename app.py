import config
from orderhub import create_app

app = create_app(secret_key=config.SECRET_KEY)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
