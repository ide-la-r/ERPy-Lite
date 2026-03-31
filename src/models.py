"""
models.py - Módulo de modelos del ERP Lite.

Jerarquía de herencia:
  Producto (clase base)
  ├── ProductoFisico (producto con peso y coste de envío)
  └── ProductoDigital (producto con tamaño y enlace de descarga)

Persistencia en disco mediante base de datos SQLite en data/.
"""

import os
import sqlite3
from datetime import datetime


class Producto:
    """Clase base para todos los productos del inventario."""

    _contador_id = 0

    def __init__(self, nombre: str, precio_base: float, stock: int = 0,
                 id_producto: int | None = None):
        if id_producto is not None:
            self.__id_producto = id_producto
        else:
            Producto._contador_id += 1
            self.__id_producto = Producto._contador_id
        self.__nombre = nombre
        self.__precio_base = float(precio_base)
        self.__stock = int(stock)

    # ── Getters ──────────────────────────────────────────────

    def get_id(self) -> int:
        return self.__id_producto

    def get_nombre(self) -> str:
        return self.__nombre

    def get_precio_base(self) -> float:
        return self.__precio_base

    def get_stock(self) -> int:
        return self.__stock

    # ── Setters ──────────────────────────────────────────────

    def set_nombre(self, nombre: str):
        self.__nombre = nombre

    def set_precio_base(self, precio: float):
        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        self.__precio_base = float(precio)

    def set_stock(self, stock: int):
        if stock < 0:
            raise ValueError("El stock no puede ser negativo.")
        self.__stock = int(stock)

    # ── Lógica de negocio ────────────────────────────────────

    def actualizar_stock(self, cantidad: int):
        """Suma (positivo) o resta (negativo) unidades al stock."""
        nuevo = self.__stock + cantidad
        if nuevo < 0:
            raise ValueError(
                f"Stock insuficiente. Disponible: {self.__stock}, "
                f"solicitado: {abs(cantidad)}."
            )
        self.__stock = nuevo

    def calcular_precio_final(self) -> float:
        """Devuelve el precio final del producto (puede sobreescribirse)."""
        return self.__precio_base

    # ── Persistencia ─────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serializa el producto a diccionario."""
        return {
            "tipo": self.__class__.__name__,
            "id_producto": self.__id_producto,
            "nombre": self.__nombre,
            "precio_base": self.__precio_base,
            "stock": self.__stock,
        }

    @classmethod
    def from_dict(cls, datos: dict) -> "Producto":
        """Reconstruye un Producto genérico desde un diccionario."""
        return cls(
            nombre=datos["nombre"],
            precio_base=datos["precio_base"],
            stock=datos["stock"],
            id_producto=datos["id_producto"],
        )

    # ── Representación ───────────────────────────────────────

    def __str__(self) -> str:
        return (
            f"[{self.__class__.__name__} #{self.__id_producto}] "
            f"{self.__nombre} | Stock: {self.__stock} | "
            f"Precio final: {self.calcular_precio_final():.2f} €"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(nombre={self.__nombre!r}, "
            f"precio_base={self.__precio_base}, stock={self.__stock}, "
            f"id_producto={self.__id_producto})"
        )


class ProductoFisico(Producto):
    """Producto tangible con peso y coste de envío."""

    def __init__(self, nombre: str, precio_base: float, stock: int = 0,
                 peso_kg: float = 0.0, costo_envio: float = 0.0,
                 id_producto: int | None = None):
        super().__init__(nombre, precio_base, stock, id_producto)
        self.__peso_kg = float(peso_kg)
        self.__costo_envio = float(costo_envio)

    def get_peso_kg(self) -> float:
        return self.__peso_kg

    def set_peso_kg(self, peso: float):
        if peso < 0:
            raise ValueError("El peso no puede ser negativo.")
        self.__peso_kg = float(peso)

    def get_costo_envio(self) -> float:
        return self.__costo_envio

    def set_costo_envio(self, costo: float):
        if costo < 0:
            raise ValueError("El coste de envío no puede ser negativo.")
        self.__costo_envio = float(costo)

    def calcular_precio_final(self) -> float:
        """Precio base + coste de envío."""
        return self.get_precio_base() + self.__costo_envio

    def to_dict(self) -> dict:
        datos = super().to_dict()
        datos["peso_kg"] = self.__peso_kg
        datos["costo_envio"] = self.__costo_envio
        return datos

    @classmethod
    def from_dict(cls, datos: dict) -> "ProductoFisico":
        return cls(
            nombre=datos["nombre"],
            precio_base=datos["precio_base"],
            stock=datos["stock"],
            peso_kg=datos.get("peso_kg", 0.0),
            costo_envio=datos.get("costo_envio", 0.0),
            id_producto=datos["id_producto"],
        )


class ProductoDigital(Producto):
    """Producto digital con tamaño en MB y enlace de descarga."""

    IVA_DIGITAL = 0.21  # 21 % de impuesto digital

    def __init__(self, nombre: str, precio_base: float, stock: int = 0,
                 tamano_mb: float = 0.0, enlace_descarga: str = "",
                 id_producto: int | None = None):
        super().__init__(nombre, precio_base, stock, id_producto)
        self.__tamano_mb = float(tamano_mb)
        self.__enlace_descarga = enlace_descarga

    def get_tamano_mb(self) -> float:
        return self.__tamano_mb

    def set_tamano_mb(self, tamano: float):
        if tamano < 0:
            raise ValueError("El tamaño no puede ser negativo.")
        self.__tamano_mb = float(tamano)

    def get_enlace_descarga(self) -> str:
        return self.__enlace_descarga

    def set_enlace_descarga(self, enlace: str):
        self.__enlace_descarga = enlace

    def calcular_precio_final(self) -> float:
        """Precio base + IVA digital (21 %)."""
        return self.get_precio_base() * (1 + self.IVA_DIGITAL)

    def to_dict(self) -> dict:
        datos = super().to_dict()
        datos["tamano_mb"] = self.__tamano_mb
        datos["enlace_descarga"] = self.__enlace_descarga
        return datos

    @classmethod
    def from_dict(cls, datos: dict) -> "ProductoDigital":
        return cls(
            nombre=datos["nombre"],
            precio_base=datos["precio_base"],
            stock=datos["stock"],
            tamano_mb=datos.get("tamano_mb", 0.0),
            enlace_descarga=datos.get("enlace_descarga", ""),
            id_producto=datos["id_producto"],
        )


# ── Funciones de persistencia (SQLite) ────────────────────────

_CONSTRUCTORES = {
    "Producto": Producto,
    "ProductoFisico": ProductoFisico,
    "ProductoDigital": ProductoDigital,
}


def inicializar_bd(ruta_bd: str):
    """Crea las tablas de productos y ventas si no existen."""
    os.makedirs(os.path.dirname(ruta_bd) or ".", exist_ok=True)
    conn = sqlite3.connect(ruta_bd)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id_producto     INTEGER PRIMARY KEY,
            tipo            TEXT NOT NULL,
            nombre          TEXT NOT NULL,
            precio_base     REAL NOT NULL,
            stock           INTEGER DEFAULT 0,
            peso_kg         REAL,
            costo_envio     REAL,
            tamano_mb       REAL,
            enlace_descarga TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id_venta        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT NOT NULL,
            id_producto     INTEGER NOT NULL,
            nombre          TEXT NOT NULL,
            tipo            TEXT NOT NULL,
            cantidad        INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            total           REAL NOT NULL,
            descuento       REAL DEFAULT 0.0,
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
        )
    """)
    conn.commit()
    conn.close()


def guardar_inventario(productos: list[Producto], ruta_bd: str):
    """Guarda la lista de productos en la base de datos SQLite."""
    inicializar_bd(ruta_bd)
    conn = sqlite3.connect(ruta_bd)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos")
    for p in productos:
        d = p.to_dict()
        cursor.execute("""
            INSERT INTO productos
                (id_producto, tipo, nombre, precio_base, stock,
                 peso_kg, costo_envio, tamano_mb, enlace_descarga)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["id_producto"], d["tipo"], d["nombre"],
            d["precio_base"], d["stock"],
            d.get("peso_kg"), d.get("costo_envio"),
            d.get("tamano_mb"), d.get("enlace_descarga"),
        ))
    conn.commit()
    conn.close()


def cargar_inventario(ruta_bd: str) -> list[Producto]:
    """Lee los productos de la base de datos SQLite."""
    if not os.path.exists(ruta_bd):
        return []
    inicializar_bd(ruta_bd)
    conn = sqlite3.connect(ruta_bd)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    filas = cursor.fetchall()
    conn.close()

    productos = []
    for fila in filas:
        # Filtrar valores NULL para que from_dict use sus defaults
        d = {k: v for k, v in dict(fila).items() if v is not None}
        cls = _CONSTRUCTORES.get(d.get("tipo", ""), Producto)
        productos.append(cls.from_dict(d))
    # Ajustar contador para evitar colisiones de ID
    if productos:
        max_id = max(p.get_id() for p in productos)
        Producto._contador_id = max(Producto._contador_id, max_id)
    return productos


# ── Registro de ventas ───────────────────────────────────────

def registrar_venta(producto: Producto, cantidad: int, ruta_bd: str):
    """Registra una venta en la base de datos SQLite."""
    producto.actualizar_stock(-cantidad)
    inicializar_bd(ruta_bd)
    conn = sqlite3.connect(ruta_bd)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ventas
            (fecha, id_producto, nombre, tipo, cantidad,
             precio_unitario, total, descuento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        producto.get_id(),
        producto.get_nombre(),
        producto.__class__.__name__,
        cantidad,
        producto.calcular_precio_final(),
        round(producto.calcular_precio_final() * cantidad, 2),
        0.0,
    ))
    conn.commit()
    conn.close()
