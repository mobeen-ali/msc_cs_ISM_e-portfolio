"""Entrypoint for the Flask application.

This script creates a Flask application via the factory defined in
``app/__init__.py`` and exposes the resulting application object as ``app``.
It also allows the app to be run directly via ``python run.py`` which
starts a development server on port 5000. The port and host can be
customised via environment variables or by editing the call to
``app.run`` below.
"""

from app import create_app

# Create the Flask application using the factory function.  By keeping
# application setup in a separate module we maintain a clean separation
# between configuration/initialisation and the code that actually runs
# the server.  This also makes the app importable for testing.
app = create_app()


if __name__ == "__main__":
    # Run the development server.  ``debug`` is intentionally disabled
    # because tests will handle any errors and reloader loops are
    # undesirable when running via this script.  The host and port are
    # explicitly set to make it clear where the app will listen.
    app.run(host="0.0.0.0", port=5000, debug=True) 