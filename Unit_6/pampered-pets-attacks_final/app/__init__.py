"""Application factory for the attack tree analyzer.

This module defines ``create_app``, a function that builds and
configures a Flask application.  The factory pattern allows for easy
testing and makes it possible to create multiple isolated app
instances if needed.  Routes are registered via a blueprint in
``routes.py``.
"""


def create_app():
    """Create and configure a new Flask application.

    Returns
    -------
    Flask
        The configured Flask application.
    """
    # Import Flask only when creating the app to avoid requiring the
    # dependency for consumers that merely import submodules (e.g. for
    # testing the model).  Without this lazy import the module import
    # would fail if Flask is unavailable in the environment.
    from flask import Flask

    app = Flask(__name__, static_folder="static", template_folder="templates")

    # A secret key is required for session management and flash messages.
    # In a production deployment this should be set from an environment
    # variable or a secrets manager rather than hard‑coded.  The default
    # provided here is sufficient for development and testing.
    app.config["SECRET_KEY"] = "change-me-in-production"

    # Register blueprints.  The routes blueprint encapsulates all HTTP
    # endpoints for the application.
    from . import routes  # import inside function to avoid circular deps

    app.register_blueprint(routes.bp)

    def currency(v):
        try:
            return f"£{float(v):,.2f}"
        except Exception:
            return v

    def pct(v, decimals=1):
        # v is a probability in [0,1]
        try:
            return f"{float(v) * 100:.{int(decimals)}f}%"
        except Exception:
            return v

    def prob(v, decimals=3):
        try:
            return f"{float(v):.{int(decimals)}f}"
        except Exception:
            return v

    app.jinja_env.filters["currency"] = currency
    app.jinja_env.filters["pct"] = pct
    app.jinja_env.filters["prob"] = prob

    return app
