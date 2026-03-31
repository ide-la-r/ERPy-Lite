# ERPy-Lite

Sistema ERP simplificado y web, centrado en **gestión de inventario**, **registro de ventas** y **análisis de datos**, desarrollado como proyecto final de Python bajo el Real Decreto 566/2024.

## ¿Qué es?

ERPy-Lite es una herramienta web ligera que permite a pequeños negocios controlar su inventario, registrar ventas y analizar el rendimiento de su negocio mediante gráficos, todo desde el navegador o como aplicación instalable (PWA).

## ¿Para quién?

Para **pequeños negocios y autónomos** — tiendas online, comercios locales, emprendedores — que venden tanto productos físicos (ropa, electrónica, muebles) como productos digitales (ebooks, software, cursos) y necesitan un sistema sencillo sin la complejidad de un SAP u Odoo.

## Módulos

| Módulo | Descripción |
|---|---|
| **Inventario** | Gestión de productos físicos (con peso y envío) y digitales (con descarga e IVA digital). Control de stock con alertas visuales. |
| **Ventas** | Registro de ventas con descuento automático de stock, historial por producto y cálculo de totales. |
| **Análisis** | Gráficos interactivos: barras agrupadas (ventas por tipo/trimestre) y líneas de tendencia (ingresos mensuales). Resumen estadístico. |

## Tecnologías

- **Backend**: Python 3 + Flask
- **Base de datos**: SQLite (sin servidor, archivo local `data/erpy.db`)
- **Análisis**: Pandas + Matplotlib
- **Frontend**: HTML5 + Bootstrap 5 + CSS personalizado
- **Testing**: Pytest
- **App instalable**: PWA (Progressive Web App)

## Arquitectura POO

```
Producto (clase base)
├── ProductoFisico  → precio + coste de envío
└── ProductoDigital → precio + IVA digital (21%)
```

Atributos privados con encapsulamiento, getters/setters, polimorfismo en `calcular_precio_final()` y persistencia en SQLite.

## Estructura del proyecto

```
ERPy-Lite/
├── data/
│   └── erpy.db              # Base de datos SQLite
├── src/
│   ├── app.py               # Aplicación Flask (rutas web)
│   ├── main.py              # Interfaz CLI alternativa
│   ├── models.py            # Clases POO + persistencia SQLite
│   ├── analytics.py         # Análisis de datos + gráficos
│   ├── templates/           # Plantillas HTML (Jinja2)
│   │   ├── base.html
│   │   ├── inventario.html
│   │   ├── producto_form.html
│   │   ├── registrar_venta.html
│   │   └── analytics.html
│   └── static/
│       ├── css/style.css
│       ├── js/
│       └── icons/
├── tests/
│   ├── test_models.py
│   └── test_analytics.py
├── requirements.txt
└── pytest.ini
```

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/ERPy-Lite.git
cd ERPy-Lite

# Crear entorno virtual
python -m venv .env
.env\Scripts\activate        # Windows
# source .env/bin/activate   # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Interfaz web (recomendada)
python src/app.py
# Abrir http://127.0.0.1:5000

# Interfaz CLI
python src/main.py

# Ejecutar tests
python -m pytest
```

## Licencia

MIT
