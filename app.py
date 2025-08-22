import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "relevamientos.db")
PDF_DIR = os.path.join(BASE_DIR, "informes")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(PDF_DIR, exist_ok=True)
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS relevamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operador TEXT NOT NULL,
            ubicacion TEXT NOT NULL,
            proyecto TEXT NOT NULL,
            observaciones TEXT,
            fecha TEXT NOT NULL,
            pdf_nombre TEXT
        );
        """)
        conn.commit()

def generar_pdf(registro):
    os.makedirs(PDF_DIR, exist_ok=True)
    pdf_filename = f"relevamiento_{registro['id']}.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_filename)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, "Informe de Relevamiento")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 2.7*cm, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Cuerpo
    y = height - 4*cm
    def draw_field(label, value):
        nonlocal y
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(6*cm, y, value if value else "-")
        y -= 0.9*cm

    draw_field("ID", str(registro["id"]))
    draw_field("Operador", registro["operador"])
    draw_field("Ubicación", registro["ubicacion"])
    draw_field("Proyecto", registro["proyecto"])
    draw_field("Fecha", registro["fecha"])

    # Observaciones como bloque de texto multilínea
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Observaciones:")
    y -= 0.6*cm
    c.setFont("Helvetica", 11)

    # Envolver texto manualmente
    wrap_width = 80
    obs = registro["observaciones"] or ""
    lines = []
    while obs:
        lines.append(obs[:wrap_width])
        obs = obs[wrap_width:]
    for line in lines:
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm
        c.drawString(2*cm, y, line)
        y -= 0.6*cm

    # Pie
    if y < 2*cm:
        c.showPage()
        y = height - 2*cm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2*cm, 1.5*cm, "Sistema de relevamientos - Informe automático")

    c.showPage()
    c.save()

    return pdf_filename

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    init_db()

    @app.route("/")
    def index():
        return render_template("form.html")

    @app.route("/guardar", methods=["POST"])
    def guardar():
        operador = request.form.get("operador", "").strip()
        ubicacion = request.form.get("ubicacion", "").strip()
        proyecto = request.form.get("proyecto", "").strip()
        observaciones = request.form.get("observaciones", "").strip()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Validaciones básicas
        errores = []
        if not operador:
            errores.append("El campo Operador es obligatorio.")
        if not ubicacion:
            errores.append("El campo Ubicación es obligatorio.")
        if not proyecto:
            errores.append("El campo Proyecto es obligatorio.")

        if errores:
            for e in errores:
                flash(e, "error")
            # Conservar lo ingresado
            return render_template("form.html", data={
                "operador": operador,
                "ubicacion": ubicacion,
                "proyecto": proyecto,
                "observaciones": observaciones
            }), 400

        with get_db() as conn:
            cur = conn.execute("""
                INSERT INTO relevamientos (operador, ubicacion, proyecto, observaciones, fecha)
                VALUES (?, ?, ?, ?, ?)
            """, (operador, ubicacion, proyecto, observaciones, fecha))
            new_id = cur.lastrowid
            conn.commit()

            # Generar PDF
            cur = conn.execute("SELECT * FROM relevamientos WHERE id = ?", (new_id,))
            registro = cur.fetchone()
            pdf_nombre = generar_pdf(registro)

            conn.execute("UPDATE relevamientos SET pdf_nombre = ? WHERE id = ?", (pdf_nombre, new_id))
            conn.commit()

        flash("Relevamiento cargado y PDF generado.", "success")
        return redirect(url_for("listado"))

    @app.route("/listado")
    def listado():
        with get_db() as conn:
            cur = conn.execute("SELECT * FROM relevamientos ORDER BY id DESC")
            filas = cur.fetchall()
        return render_template("listado.html", filas=filas)

    @app.route("/descargar/<int:rid>")
    def descargar(rid):
        with get_db() as conn:
            cur = conn.execute("SELECT * FROM relevamientos WHERE id = ?", (rid,))
            reg = cur.fetchone()
            if not reg:
                abort(404)
            pdf_nombre = reg["pdf_nombre"]
            if not pdf_nombre or not os.path.exists(os.path.join(PDF_DIR, pdf_nombre)):
                # Regenerar si falta
                pdf_nombre = generar_pdf(reg)
                conn.execute("UPDATE relevamientos SET pdf_nombre = ? WHERE id = ?", (pdf_nombre, rid))
                conn.commit()
        return send_from_directory(PDF_DIR, pdf_nombre, as_attachment=True)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
