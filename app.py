import os
import sys

# Ajouter le dossier app au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
os.chdir(os.path.join(os.path.dirname(__file__), 'app'))

# Importer et exécuter l'application
exec(open('app.py').read())
