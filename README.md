# Proyecto-M2-Cliente-MesasM2

Instrucciones rápidas para poner en marcha localmente.

Requisitos:
- Python 3.11+ o la versión que uses (recomendado 3.12)
- Windows (instrucciones para `cmd`)

Pasos (cmd):

```cmd
cd C:\Users\Tati\Documents\GitHub\Proyecto-M2-Cliente-MesasM2
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
set DJANGO_SECRET_KEY=valor_secreto_local
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py createsuperuser
venv\Scripts\python manage.py runserver
```

Notas:
- No subas tu `venv` ni `db.sqlite3`. Asegúrate de que `.gitignore` esté en la raíz.
- `SECRET_KEY` debe definirse en la variable de entorno `DJANGO_SECRET_KEY` en producción; el proyecto usa un valor por defecto inseguro solo para desarrollo local.
- Si usas VS Code, selecciona el intérprete `venv\Scripts\python.exe` (Ctrl+Shift+P → "Python: Select Interpreter").

Cómo subir al repositorio (si aún no existe remoto):

```cmd
git init
git checkout -b main
git add .
git commit -m "Initial commit"
# crea el repo en GitHub y añade remote origin
git remote add origin https://github.com/<tu_usuario>/<tu_repo>.git
git push -u origin main
```

Opcional: añade un GitHub Actions workflow para ejecutar `pip install -r requirements.txt` y `python manage.py test` en cada push.
