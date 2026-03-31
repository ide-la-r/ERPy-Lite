"""
test_analytics.py - Pruebas unitarias para el módulo analytics.py.
"""

import os
import sqlite3
import tempfile

import pandas as pd
import pytest

from analytics import (
    cargar_ventas,
    grafico_barras_trimestre,
    grafico_lineas_ingresos,
    limpiar_datos,
)


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def ventas_ejemplo():
    """Devuelve una lista de ventas de ejemplo."""
    return [
        {"fecha": "2026-01-10", "id_producto": 1, "nombre": "Teclado",
         "tipo": "ProductoFisico", "cantidad": 5, "precio_unitario": 55.0,
         "total": 275.0, "descuento": 0.0},
        {"fecha": "2026-01-20", "id_producto": 2, "nombre": "Antivirus",
         "tipo": "ProductoDigital", "cantidad": 10, "precio_unitario": 36.3,
         "total": 363.0, "descuento": None},
        {"fecha": "2026-02-05", "id_producto": 1, "nombre": "Teclado",
         "tipo": "ProductoFisico", "cantidad": 8, "precio_unitario": 55.0,
         "total": 440.0, "descuento": 5.0},
        {"fecha": "2026-02-15", "id_producto": 3, "nombre": "Ebook",
         "tipo": "ProductoDigital", "cantidad": 20, "precio_unitario": 12.1,
         "total": 242.0, "descuento": 0.0},
        {"fecha": "2026-03-01", "id_producto": 1, "nombre": "Teclado",
         "tipo": "ProductoFisico", "cantidad": 3, "precio_unitario": 55.0,
         "total": 165.0, "descuento": 0.0},
    ]


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def ruta_bd(tmp_dir, ventas_ejemplo):
    """Crea una BD SQLite temporal con las ventas de ejemplo."""
    ruta = os.path.join(tmp_dir, "test.db")
    conn = sqlite3.connect(ruta)
    conn.execute("""
        CREATE TABLE ventas (
            id_venta        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT NOT NULL,
            id_producto     INTEGER NOT NULL,
            nombre          TEXT NOT NULL,
            tipo            TEXT NOT NULL,
            cantidad        INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            total           REAL NOT NULL,
            descuento       REAL DEFAULT 0.0
        )
    """)
    for v in ventas_ejemplo:
        conn.execute("""
            INSERT INTO ventas (fecha, id_producto, nombre, tipo, cantidad,
                                precio_unitario, total, descuento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (v["fecha"], v["id_producto"], v["nombre"], v["tipo"],
              v["cantidad"], v["precio_unitario"], v["total"], v["descuento"]))
    conn.commit()
    conn.close()
    return ruta


# ── Tests de carga ───────────────────────────────────────────

class TestCargarVentas:

    def test_carga_correcta(self, ruta_bd):
        df = cargar_ventas(ruta_bd)
        assert len(df) == 5
        assert "fecha" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["fecha"])

    def test_archivo_inexistente(self, tmp_dir):
        ruta = os.path.join(tmp_dir, "no_existe.db")
        df = cargar_ventas(ruta)
        assert df.empty


# ── Tests de limpieza ────────────────────────────────────────

class TestLimpiarDatos:

    def test_rellena_descuentos_nulos(self, ruta_bd):
        df = cargar_ventas(ruta_bd)
        df = limpiar_datos(df)
        assert df["descuento"].isna().sum() == 0

    def test_no_pierde_filas_validas(self, ruta_bd):
        df = cargar_ventas(ruta_bd)
        df_limpio = limpiar_datos(df)
        assert len(df_limpio) == 5

    def test_df_vacio_no_falla(self):
        df = pd.DataFrame()
        resultado = limpiar_datos(df)
        assert resultado.empty

    def test_elimina_outliers(self):
        base = {"id_producto": 1, "nombre": "X",
                "tipo": "ProductoFisico", "precio_unitario": 10,
                "total": 50, "descuento": 0}
        datos = [
            {**base, "fecha": f"2026-01-{str(i).zfill(2)}", "cantidad": 5}
            for i in range(1, 11)
        ]
        # Añadir un outlier extremo
        datos.append({**base, "fecha": "2026-01-15", "cantidad": 99999,
                      "total": 999990})
        df = pd.DataFrame(datos)
        df["fecha"] = pd.to_datetime(df["fecha"])
        df_limpio = limpiar_datos(df)
        # El outlier extremo debería ser eliminado
        assert len(df_limpio) < len(df)


# ── Tests de gráficos ───────────────────────────────────────

class TestGraficos:

    def test_grafico_barras_genera_archivo(self, ruta_bd, tmp_dir):
        df = cargar_ventas(ruta_bd)
        df = limpiar_datos(df)
        ruta_img = os.path.join(tmp_dir, "barras.png")
        grafico_barras_trimestre(df, ruta_img)
        assert os.path.exists(ruta_img)

    def test_grafico_lineas_genera_archivo(self, ruta_bd, tmp_dir):
        df = cargar_ventas(ruta_bd)
        df = limpiar_datos(df)
        ruta_img = os.path.join(tmp_dir, "lineas.png")
        grafico_lineas_ingresos(df, ruta_img)
        assert os.path.exists(ruta_img)

    def test_grafico_barras_df_vacio(self, tmp_dir, capsys):
        df = pd.DataFrame()
        ruta_img = os.path.join(tmp_dir, "barras.png")
        grafico_barras_trimestre(df, ruta_img)
        assert not os.path.exists(ruta_img)

    def test_grafico_lineas_df_vacio(self, tmp_dir, capsys):
        df = pd.DataFrame()
        ruta_img = os.path.join(tmp_dir, "lineas.png")
        grafico_lineas_ingresos(df, ruta_img)
        assert not os.path.exists(ruta_img)
