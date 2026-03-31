import os
from pathlib import Path

from flask import Flask

from models import repo
from routes import main_bp


def create_app():
    base_dir = Path(__file__).resolve().parent
    instance_dir = base_dir / "instance"
    instance_dir.mkdir(exist_ok=True)

    app = Flask(__name__, instance_path=str(instance_dir), instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
    app.config["MONGO_DB_NAME"] = os.environ.get("MONGO_DB_NAME", "mockprep_india")
    app.config["WHATSAPP_NUMBER"] = os.environ.get("WHATSAPP_NUMBER", "919999999999")
    app.config["WHATSAPP_MESSAGE"] = "Hi, I need help choosing a PYQ/mock pass for my PG exam prep."

    repo.init_app(app)
    repo.seed_database()
    app.register_blueprint(main_bp)

    @app.template_filter("currency")
    def currency_filter(value):
        return f"Rs. {int(value)}"

    @app.template_filter("dt")
    def datetime_filter(value):
        return value.strftime("%d %b %Y, %I:%M %p") if value else "-"

    return app


app = create_app()


if __name__ == "__main__":
    debug_enabled = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug_enabled, use_reloader=debug_enabled)
