# Relevamiento App (Flask + PDF)

MVP para cargar relevamientos mediante formulario web, guardar en SQLite y generar un PDF automático por cada registro.

## Requisitos
- Python 3.9+ recomendado

## Instalación y ejecución

```bash
cd relevamiento_app
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrí http://localhost:5000 para cargar un relevamiento. El PDF se guarda en `informes/` y también se puede descargar desde **Listado**.

## Personalización rápida
- **Campos**: editar esquema en `init_db()` (archivo `app.py`) y el formulario en `templates/form.html`.
- **Formato del PDF**: función `generar_pdf()` en `app.py` (usa ReportLab).
- **Estilos**: `static/styles.css`.
- **Mensajes/validaciones**: flashes en el backend (`/guardar`) y atributos `required` en el HTML.

## Seguridad básica
- Definí `SECRET_KEY` por variable de entorno en producción: `export SECRET_KEY="algo-super-secreto"`.
- Si se publica en internet, usar HTTPS y autenticación para rutas sensibles (ej., `/listado`).

## Despliegue
- Gunicorn + Nginx o contenedor Docker.
- Montar volumen para `informes/` y respaldo periódico de `relevamientos.db`.