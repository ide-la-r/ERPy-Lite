"""
main.py - Punto de entrada del ERP Lite.

Menú interactivo con gestión de inventario, registro de ventas
y módulo de análisis de datos. Todas las entradas del usuario
están protegidas con bloques try-except.
"""

import os
import sys

# Ajustar path para poder importar desde src/
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    Producto,
    ProductoDigital,
    ProductoFisico,
    cargar_inventario,
    guardar_inventario,
    inicializar_bd,
    registrar_venta,
)
from analytics import (
    cargar_ventas,
    grafico_barras_trimestre,
    grafico_lineas_ingresos,
    limpiar_datos,
    resumen_ventas,
)

# ── Rutas de datos ───────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RUTA_BD = os.path.join(DATA_DIR, "erpy.db")

MENU = """
╔══════════════════════════════════════════╗
║           ERP Lite - Menú Principal      ║
╠══════════════════════════════════════════╣
║  1. Añadir producto físico               ║
║  2. Añadir producto digital              ║
║  3. Listar inventario                    ║
║  4. Actualizar stock de un producto      ║
║  5. Registrar venta                      ║
║  6. Ver resumen de ventas                ║
║  7. Generar gráfico de barras (trimestre)║
║  8. Generar gráfico de líneas (ingresos) ║
║  0. Salir                                ║
╚══════════════════════════════════════════╝
"""


# ── Funciones auxiliares de entrada ──────────────────────────

def pedir_float(mensaje: str) -> float:
    """Solicita un float al usuario con validación."""
    while True:
        try:
            valor = float(input(mensaje))
            if valor < 0:
                print("  ✗ El valor no puede ser negativo.")
                continue
            return valor
        except ValueError:
            print("  ✗ Entrada inválida. Introduce un número.")


def pedir_int(mensaje: str, minimo: int = 0) -> int:
    """Solicita un entero al usuario con validación."""
    while True:
        try:
            valor = int(input(mensaje))
            if valor < minimo:
                print(f"  ✗ El valor debe ser al menos {minimo}.")
                continue
            return valor
        except ValueError:
            print("  ✗ Entrada inválida. Introduce un número entero.")


def buscar_producto(productos: list[Producto], id_prod: int) -> Producto | None:
    """Busca un producto por su ID en la lista."""
    for p in productos:
        if p.get_id() == id_prod:
            return p
    return None


# ── Opciones del menú ────────────────────────────────────────

def opcion_anadir_fisico(productos: list[Producto]):
    print("\n── Añadir Producto Físico ──")
    nombre = input("  Nombre: ").strip()
    if not nombre:
        print("  ✗ El nombre no puede estar vacío.")
        return
    precio = pedir_float("  Precio base (€): ")
    stock = pedir_int("  Stock inicial: ")
    peso = pedir_float("  Peso (kg): ")
    envio = pedir_float("  Coste de envío (€): ")
    p = ProductoFisico(nombre, precio, stock, peso, envio)
    productos.append(p)
    guardar_inventario(productos, RUTA_BD)
    print(f"  ✔ Producto añadido: {p}")


def opcion_anadir_digital(productos: list[Producto]):
    print("\n── Añadir Producto Digital ──")
    nombre = input("  Nombre: ").strip()
    if not nombre:
        print("  ✗ El nombre no puede estar vacío.")
        return
    precio = pedir_float("  Precio base (€): ")
    stock = pedir_int("  Stock inicial (licencias): ")
    tamano = pedir_float("  Tamaño (MB): ")
    enlace = input("  Enlace de descarga: ").strip()
    p = ProductoDigital(nombre, precio, stock, tamano, enlace)
    productos.append(p)
    guardar_inventario(productos, RUTA_BD)
    print(f"  ✔ Producto añadido: {p}")


def opcion_listar(productos: list[Producto]):
    print("\n── Inventario Actual ──")
    if not productos:
        print("  (vacío)")
        return
    for p in productos:
        print(f"  {p}")


def opcion_actualizar_stock(productos: list[Producto]):
    print("\n── Actualizar Stock ──")
    if not productos:
        print("  (no hay productos)")
        return
    opcion_listar(productos)
    id_prod = pedir_int("  ID del producto: ", minimo=1)
    producto = buscar_producto(productos, id_prod)
    if producto is None:
        print(f"  ✗ No se encontró el producto con ID {id_prod}.")
        return
    cantidad = int(input("  Cantidad (+añadir / -retirar): "))
    try:
        producto.actualizar_stock(cantidad)
        guardar_inventario(productos, RUTA_BD)
        print(f"  ✔ Stock actualizado: {producto}")
    except ValueError as e:
        print(f"  ✗ Error: {e}")


def opcion_registrar_venta(productos: list[Producto]):
    print("\n── Registrar Venta ──")
    if not productos:
        print("  (no hay productos)")
        return
    opcion_listar(productos)
    id_prod = pedir_int("  ID del producto: ", minimo=1)
    producto = buscar_producto(productos, id_prod)
    if producto is None:
        print(f"  ✗ No se encontró el producto con ID {id_prod}.")
        return
    cantidad = pedir_int("  Cantidad a vender: ", minimo=1)
    try:
        registrar_venta(producto, cantidad, RUTA_BD)
        guardar_inventario(productos, RUTA_BD)
        total = producto.calcular_precio_final() * cantidad
        print(f"  ✔ Venta registrada: {cantidad} × {producto.get_nombre()} "
              f"= {total:.2f} €")
    except ValueError as e:
        print(f"  ✗ Error: {e}")


def opcion_resumen():
    df = cargar_ventas(RUTA_BD)
    df = limpiar_datos(df)
    resumen_ventas(df)


def opcion_grafico_barras():
    df = cargar_ventas(RUTA_BD)
    df = limpiar_datos(df)
    ruta = os.path.join(DATA_DIR, "grafico_barras_trimestre.png")
    grafico_barras_trimestre(df, ruta)


def opcion_grafico_lineas():
    df = cargar_ventas(RUTA_BD)
    df = limpiar_datos(df)
    ruta = os.path.join(DATA_DIR, "grafico_lineas_ingresos.png")
    grafico_lineas_ingresos(df, ruta)


# ── Bucle principal ──────────────────────────────────────────

def main():
    print("\n🏢 Bienvenido al ERP Lite - Gestión de Inventario y Facturación")
    inicializar_bd(RUTA_BD)
    productos = cargar_inventario(RUTA_BD)

    while True:
        print(MENU)
        opcion = input("Selecciona una opción: ").strip()

        try:
            if opcion == "1":
                opcion_anadir_fisico(productos)
            elif opcion == "2":
                opcion_anadir_digital(productos)
            elif opcion == "3":
                opcion_listar(productos)
            elif opcion == "4":
                opcion_actualizar_stock(productos)
            elif opcion == "5":
                opcion_registrar_venta(productos)
            elif opcion == "6":
                opcion_resumen()
            elif opcion == "7":
                opcion_grafico_barras()
            elif opcion == "8":
                opcion_grafico_lineas()
            elif opcion == "0":
                print("\n👋 ¡Hasta pronto!")
                break
            else:
                print("  ✗ Opción no válida. Introduce un número del 0 al 8.")
        except KeyboardInterrupt:
            print("\n\n👋 Programa interrumpido. ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\n  ✗ Error inesperado: {e}")
            print("    Volviendo al menú principal...\n")


if __name__ == "__main__":
    main()
