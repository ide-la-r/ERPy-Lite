import os
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, send_from_directory, session)
from models import (ProductoFisico, ProductoDigital,
                     cargar_inventario, guardar_inventario, registrar_venta,
                     inicializar_bd, crear_usuario, buscar_usuario, verificar_contraseña)
from analytics import (cargar_ventas, limpiar_datos, resumen_ventas,
                       grafico_barras_base64, grafico_lineas_base64,
                       resumen_ventas_dict)

app = Flask(__name__)
app.secret_key = "erpy-lite-clave-secreta-2026"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_BD = os.path.join(BASE_DIR, "data", "erpy.db")

# Crear tablas al arrancar
inicializar_bd(RUTA_BD)


# ── Decorador de protección ──────────────────────────────────

def login_requerido(f):
    """Decorador que requiere estar logueado."""
    @wraps(f)
    def decorador_login(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión primero", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorador_login


# ── Rutas ────────────────────────────────────────────────

@app.route("/sw.js")
def service_worker():
    return send_from_directory(app.static_folder, "sw.js",
                               mimetype="application/javascript")


@app.route("/")
def inicio():
    if "usuario_id" in session:
        return redirect(url_for("inventario"))
    return redirect(url_for("login"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """GET: mostrar formulario. POST: crear usuario."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        nombre = request.form.get("nombre", "").strip()
        contraseña = request.form.get("contraseña", "")
        contraseña2 = request.form.get("contraseña2", "")

        if not email or not nombre or not contraseña:
            flash("Todos los campos son obligatorios", "danger")
            return redirect(url_for("registro"))

        if contraseña != contraseña2:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for("registro"))

        if len(contraseña) < 6:
            flash("La contraseña debe tener al menos 6 caracteres", "danger")
            return redirect(url_for("registro"))

        if crear_usuario(email, contraseña, nombre, RUTA_BD):
            flash("Usuario creado exitosamente. Inicia sesión.", "success")
            return redirect(url_for("login"))
        else:
            flash("El email ya está registrado", "danger")
            return redirect(url_for("registro"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """GET: mostrar formulario. POST: autenticar usuario."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        contraseña = request.form.get("contraseña", "")

        if not email or not contraseña:
            flash("Email y contraseña son obligatorios", "danger")
            return redirect(url_for("login"))

        if verificar_contraseña(email, contraseña, RUTA_BD):
            usuario = buscar_usuario(email, RUTA_BD)
            session["usuario_id"] = usuario["id_usuario"]
            session["usuario_email"] = usuario["email"]
            session["usuario_nombre"] = usuario["nombre"]
            flash(f"¡Bienvenido, {usuario['nombre']}!", "success")
            return redirect(url_for("inventario"))
        else:
            flash("Email o contraseña incorrectos", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Cierra la sesión del usuario."""
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("login"))




@app.route("/inventario")
@login_requerido
def inventario():
    productos = cargar_inventario(RUTA_BD)
    return render_template("inventario.html", productos=productos)


# ── Producto: crear ──────────────────────────────────────

@app.route("/producto/nuevo", methods=["GET", "POST"])
@login_requerido
def producto_nuevo():
    if request.method == "GET":
        return render_template("producto_form.html")

    try:
        tipo = request.form["tipo"]
        nombre = request.form["nombre"].strip()
        precio_base = float(request.form["precio_base"])
        stock = int(request.form["stock"])

        if not nombre:
            raise ValueError("El nombre no puede estar vacío.")

        if tipo == "ProductoFisico":
            peso_kg = float(request.form.get("peso_kg", 0))
            costo_envio = float(request.form.get("costo_envio", 0))
            producto = ProductoFisico(nombre, precio_base, stock,
                                      peso_kg, costo_envio)
        else:
            tamano_mb = float(request.form.get("tamano_mb", 0))
            enlace_descarga = request.form.get("enlace_descarga", "")
            producto = ProductoDigital(nombre, precio_base, stock,
                                       tamano_mb, enlace_descarga)

        productos = cargar_inventario(RUTA_BD)
        productos.append(producto)
        guardar_inventario(productos, RUTA_BD)
        flash(f"Producto '{nombre}' añadido correctamente.", "success")
        return redirect(url_for("inventario"))

    except (ValueError, KeyError) as e:
        flash(f"Error al crear el producto: {e}", "danger")
        return render_template("producto_form.html")


# ── Producto: actualizar stock ───────────────────────────

@app.route("/producto/<int:id_producto>/stock", methods=["POST"])
@login_requerido
def actualizar_stock(id_producto):
    try:
        cantidad = int(request.form["cantidad"])
        productos = cargar_inventario(RUTA_BD)
        producto = next((p for p in productos if p.get_id() == id_producto), None)

        if producto is None:
            flash("Producto no encontrado.", "danger")
            return redirect(url_for("inventario"))

        producto.actualizar_stock(cantidad)
        guardar_inventario(productos, RUTA_BD)
        signo = "+" if cantidad >= 0 else ""
        flash(f"Stock de '{producto.get_nombre()}' actualizado ({signo}{cantidad}).", "success")

    except ValueError as e:
        flash(f"Error al actualizar stock: {e}", "danger")

    return redirect(url_for("inventario"))


# ── Venta: registrar ────────────────────────────────────

@app.route("/venta/nueva", methods=["GET", "POST"])
@login_requerido
def venta_nueva():
    productos = cargar_inventario(RUTA_BD)

    if request.method == "GET":
        return render_template("registrar_venta.html", productos=productos)

    try:
        id_producto = int(request.form["id_producto"])
        cantidad = int(request.form["cantidad"])

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0.")

        producto = next((p for p in productos if p.get_id() == id_producto), None)
        if producto is None:
            raise ValueError("Producto no encontrado.")

        registrar_venta(producto, cantidad, RUTA_BD)
        guardar_inventario(productos, RUTA_BD)
        flash(
            f"Venta registrada: {cantidad}x '{producto.get_nombre()}' "
            f"por {producto.calcular_precio_final() * cantidad:.2f} €.",
            "success"
        )
        return redirect(url_for("inventario"))

    except (ValueError, KeyError) as e:
        flash(f"Error al registrar la venta: {e}", "danger")
        return render_template("registrar_venta.html", productos=productos)


# ── Análisis de datos ────────────────────────────────────

@app.route("/analytics")
@login_requerido
def analytics():
    try:
        df = cargar_ventas(RUTA_BD)
        df = limpiar_datos(df)

        img_barras = grafico_barras_base64(df)
        img_lineas = grafico_lineas_base64(df)
        resumen = resumen_ventas_dict(df)

        return render_template("analytics.html",
                               img_barras=img_barras,
                               img_lineas=img_lineas,
                               resumen=resumen)
    except Exception as e:
        flash(f"Error al generar el análisis: {e}", "danger")
        return render_template("analytics.html",
                               img_barras=None,
                               img_lineas=None,
                               resumen=None)


if __name__ == "__main__":
    app.run(debug=True)