from app import create_app
from config import settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.API_HOST, port=settings.API_PORT, debug=settings.FLASK_DEBUG)