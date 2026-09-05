"""
Point d'entrée de OpsDesk.

Lance le serveur de développement Flask, en écoutant sur 0.0.0.0
et sur le port défini par la variable d'environnement PORT
(ceci facilite la conteneurisation future de l'application).
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = app.config.get("PORT", 5000)
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
