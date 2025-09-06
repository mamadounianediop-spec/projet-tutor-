#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application principale - Point d'entrée de la plateforme IEF Louga
"""

import os
import sys

# Ajouter le répertoire actuel au PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

try:
    from app import create_app
    print("✓ Module app importé avec succès")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

# Création de l'instance Flask
app = create_app()

if __name__ == '__main__':
    print("🚀 Démarrage de l'application IEF Louga")
    print("📍 URL: http://localhost:5000")
    print("🔧 Mode: Développement")
    
    # Configuration pour le développement
    app.run(debug=True, host='0.0.0.0', port=5000)
