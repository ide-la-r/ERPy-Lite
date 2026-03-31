"""
test_models.py - Pruebas unitarias para el módulo models.py.
"""

import os
import sqlite3
import tempfile

import pytest

from models import (
    Producto,
    ProductoDigital,
    ProductoFisico,
    cargar_inventario,
    guardar_inventario,
    inicializar_bd,
    registrar_venta,
)


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_contador():
    """Reinicia el contador de IDs antes de cada test."""
    Producto._contador_id = 0
    yield


@pytest.fixture
def producto_fisico():
    return ProductoFisico("Teclado", 50.0, 100, peso_kg=0.8, costo_envio=5.0)


@pytest.fixture
def producto_digital():
    return ProductoDigital(
        "Antivirus", 30.0, 500,
        tamano_mb=200.0, enlace_descarga="https://example.com/av"
    )


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


# ── Tests de Producto (clase base) ──────────────────────────

class TestProducto:

    def test_creacion_y_getters(self):
        p = Producto("Genérico", 10.0, 5)
        assert p.get_nombre() == "Genérico"
        assert p.get_precio_base() == 10.0
        assert p.get_stock() == 5
        assert p.get_id() == 1

    def test_setters(self):
        p = Producto("Test", 10.0, 0)
        p.set_nombre("Nuevo")
        p.set_precio_base(20.0)
        p.set_stock(50)
        assert p.get_nombre() == "Nuevo"
        assert p.get_precio_base() == 20.0
        assert p.get_stock() == 50

    def test_precio_negativo_error(self):
        p = Producto("Test", 10.0)
        with pytest.raises(ValueError):
            p.set_precio_base(-5)

    def test_stock_negativo_error(self):
        p = Producto("Test", 10.0)
        with pytest.raises(ValueError):
            p.set_stock(-1)

    def test_actualizar_stock_suma(self):
        p = Producto("Test", 10.0, 10)
        p.actualizar_stock(5)
        assert p.get_stock() == 15

    def test_actualizar_stock_resta(self):
        p = Producto("Test", 10.0, 10)
        p.actualizar_stock(-3)
        assert p.get_stock() == 7

    def test_actualizar_stock_insuficiente(self):
        p = Producto("Test", 10.0, 2)
        with pytest.raises(ValueError, match="Stock insuficiente"):
            p.actualizar_stock(-5)

    def test_precio_final_base(self):
        p = Producto("Test", 25.0)
        assert p.calcular_precio_final() == 25.0

    def test_to_dict_y_from_dict(self):
        p = Producto("Test", 15.0, 3)
        d = p.to_dict()
        assert d["tipo"] == "Producto"
        assert d["nombre"] == "Test"
        restaurado = Producto.from_dict(d)
        assert restaurado.get_nombre() == p.get_nombre()
        assert restaurado.get_precio_base() == p.get_precio_base()

    def test_str_contiene_datos(self):
        p = Producto("Widget", 9.99, 7)
        texto = str(p)
        assert "Widget" in texto
        assert "9.99" in texto


# ── Tests de ProductoFisico ──────────────────────────────────

class TestProductoFisico:

    def test_herencia(self, producto_fisico):
        assert isinstance(producto_fisico, Producto)

    def test_atributos_propios(self, producto_fisico):
        assert producto_fisico.get_peso_kg() == 0.8
        assert producto_fisico.get_costo_envio() == 5.0

    def test_precio_final_con_envio(self, producto_fisico):
        assert producto_fisico.calcular_precio_final() == 55.0

    def test_setters_propios(self, producto_fisico):
        producto_fisico.set_peso_kg(1.2)
        producto_fisico.set_costo_envio(7.5)
        assert producto_fisico.get_peso_kg() == 1.2
        assert producto_fisico.get_costo_envio() == 7.5

    def test_peso_negativo_error(self, producto_fisico):
        with pytest.raises(ValueError):
            producto_fisico.set_peso_kg(-1)

    def test_to_dict_incluye_peso(self, producto_fisico):
        d = producto_fisico.to_dict()
        assert "peso_kg" in d
        assert "costo_envio" in d
        assert d["tipo"] == "ProductoFisico"

    def test_from_dict_restaura(self, producto_fisico):
        d = producto_fisico.to_dict()
        restaurado = ProductoFisico.from_dict(d)
        assert restaurado.get_peso_kg() == producto_fisico.get_peso_kg()
        assert restaurado.get_costo_envio() == producto_fisico.get_costo_envio()


# ── Tests de ProductoDigital ─────────────────────────────────

class TestProductoDigital:

    def test_herencia(self, producto_digital):
        assert isinstance(producto_digital, Producto)

    def test_atributos_propios(self, producto_digital):
        assert producto_digital.get_tamano_mb() == 200.0
        assert producto_digital.get_enlace_descarga() == "https://example.com/av"

    def test_precio_final_con_iva(self, producto_digital):
        esperado = 30.0 * 1.21  # IVA 21 %
        assert abs(producto_digital.calcular_precio_final() - esperado) < 0.01

    def test_setters_propios(self, producto_digital):
        producto_digital.set_tamano_mb(500.0)
        producto_digital.set_enlace_descarga("https://new.url")
        assert producto_digital.get_tamano_mb() == 500.0
        assert producto_digital.get_enlace_descarga() == "https://new.url"

    def test_tamano_negativo_error(self, producto_digital):
        with pytest.raises(ValueError):
            producto_digital.set_tamano_mb(-10)

    def test_to_dict_incluye_enlace(self, producto_digital):
        d = producto_digital.to_dict()
        assert "tamano_mb" in d
        assert "enlace_descarga" in d
        assert d["tipo"] == "ProductoDigital"

    def test_from_dict_restaura(self, producto_digital):
        d = producto_digital.to_dict()
        restaurado = ProductoDigital.from_dict(d)
        assert restaurado.get_tamano_mb() == producto_digital.get_tamano_mb()


# ── Tests de persistencia ────────────────────────────────────

class TestPersistencia:

    def test_guardar_y_cargar_inventario(self, tmp_dir):
        ruta = os.path.join(tmp_dir, "test.db")
        productos = [
            ProductoFisico("Mesa", 100.0, 10, 15.0, 20.0),
            ProductoDigital("Ebook", 9.99, 999, 5.0, "https://example.com/ebook"),
        ]
        guardar_inventario(productos, ruta)
        assert os.path.exists(ruta)

        cargados = cargar_inventario(ruta)
        assert len(cargados) == 2
        assert isinstance(cargados[0], ProductoFisico)
        assert isinstance(cargados[1], ProductoDigital)
        assert cargados[0].get_nombre() == "Mesa"

    def test_cargar_inventario_vacio(self, tmp_dir):
        ruta = os.path.join(tmp_dir, "no_existe.db")
        assert cargar_inventario(ruta) == []

    def test_registrar_venta(self, tmp_dir):
        ruta_bd = os.path.join(tmp_dir, "test.db")
        inicializar_bd(ruta_bd)
        p = ProductoFisico("Silla", 80.0, 10, 8.0, 10.0)
        registrar_venta(p, 2, ruta_bd)
        assert p.get_stock() == 8

        conn = sqlite3.connect(ruta_bd)
        conn.row_factory = sqlite3.Row
        ventas = conn.execute("SELECT * FROM ventas").fetchall()
        conn.close()
        assert len(ventas) == 1
        assert ventas[0]["cantidad"] == 2
        assert ventas[0]["nombre"] == "Silla"

    def test_registrar_venta_stock_insuficiente(self, tmp_dir):
        ruta_bd = os.path.join(tmp_dir, "test.db")
        inicializar_bd(ruta_bd)
        p = Producto("Agotado", 10.0, 1)
        with pytest.raises(ValueError):
            registrar_venta(p, 5, ruta_bd)


# ── Tests de polimorfismo ────────────────────────────────────

class TestPolimorfismo:

    def test_precios_distintos_mismo_base(self):
        fisico = ProductoFisico("F", 100.0, 1, costo_envio=15.0)
        digital = ProductoDigital("D", 100.0, 1)

        assert fisico.calcular_precio_final() == 115.0
        assert abs(digital.calcular_precio_final() - 121.0) < 0.01

    def test_lista_heterogenea(self):
        productos = [
            ProductoFisico("A", 50.0, 10, costo_envio=5.0),
            ProductoDigital("B", 50.0, 10),
            Producto("C", 50.0, 10),
        ]
        precios = [p.calcular_precio_final() for p in productos]
        assert precios[0] == 55.0
        assert abs(precios[1] - 60.5) < 0.01
        assert precios[2] == 50.0
