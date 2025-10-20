"""Entrypoint for the Flask application.

Create the Flask app via the factory in ``app/__init__.py`` and expose it
as ``app``. You can also run the app directly with ``python run.py``, which
starts a development server on port 5000. The host and port can be
customised via environment variables or by editing the call to ``app.run``
below.
"""

from app import create_app

# Create the Flask application using the factory function. By keeping
# setup in a separate module, we separate configuration from runtime code.
# This also makes the app importable for testing.
app = create_app()


if __name__ == "__main__":
    # Run the development server with debug enabled.
    # The host and port are explicit for clarity.
    app.run(host="0.0.0.0", port=5000, debug=True)
