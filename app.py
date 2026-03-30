import os
import sys
import runpy

# Ajouter le dossier app au path
app_dir = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_dir)
os.chdir(app_dir)

# Exécuter l'application avec __file__ correctement défini
runpy.run_path('app.py', run_name='__main__')
