"""
analytics.py - Módulo de análisis de datos del ERP Lite.

Funcionalidades:
  1. Carga y limpieza de datos de ventas (NaNs, outliers).
  2. Gráfico de barras agrupadas: volumen de ventas por tipo de producto
     en el último trimestre.
  3. Gráfico de líneas: evolución de ingresos brutos mensuales.
"""

import io
import base64
import os
import sqlite3

import matplotlib
matplotlib.use("Agg")  # Backend no interactivo para evitar errores en CI
import matplotlib.pyplot as plt
import pandas as pd


# ── Carga de datos ───────────────────────────────────────────

def cargar_ventas(ruta_bd: str) -> pd.DataFrame:
    """Carga las ventas desde la base de datos SQLite y devuelve un DataFrame."""
    if not os.path.exists(ruta_bd):
        return pd.DataFrame()
    conn = sqlite3.connect(ruta_bd)
    df = pd.read_sql("SELECT * FROM ventas", conn)
    conn.close()
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df


# ── Limpieza técnica ─────────────────────────────────────────

def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Gestiona NaNs en descuentos y elimina outliers de cantidad."""
    if df.empty:
        return df

    # Rellenar descuentos nulos con 0
    if "descuento" in df.columns:
        df["descuento"] = df["descuento"].fillna(0.0)

    # Eliminar filas sin fecha válida
    df = df.dropna(subset=["fecha"])

    # Eliminar outliers: cantidades fuera de 3σ
    if "cantidad" in df.columns and len(df) > 2:
        media = df["cantidad"].mean()
        desv = df["cantidad"].std()
        if desv > 0:
            df = df[
                (df["cantidad"] >= media - 3 * desv)
                & (df["cantidad"] <= media + 3 * desv)
            ]

    return df.reset_index(drop=True)


# ── Gráfico 1: Barras agrupadas (último trimestre) ──────────

def grafico_barras_trimestre(df: pd.DataFrame, ruta_salida: str | None = None):
    """
    Genera un gráfico de barras agrupadas comparando el volumen
    de ventas de ProductoFisico vs ProductoDigital en los últimos
    3 meses del dataset.
    """
    if df.empty:
        print("⚠  No hay datos de ventas para generar el gráfico de barras.")
        return

    df = df.copy()
    df["mes"] = df["fecha"].dt.to_period("M")
    ultimos_3 = sorted(df["mes"].unique())[-3:]
    df_trim = df[df["mes"].isin(ultimos_3)]

    if df_trim.empty:
        print("⚠  No hay datos suficientes en el último trimestre.")
        return

    tabla = (
        df_trim.groupby(["mes", "tipo"])["cantidad"]
        .sum()
        .unstack(fill_value=0)
    )

    ax = tabla.plot(kind="bar", figsize=(10, 6), colormap="Set2",
                    edgecolor="black")
    ax.set_title("Volumen de ventas por tipo – Último trimestre",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Unidades vendidas")
    ax.legend(title="Tipo de producto")
    plt.xticks(rotation=0)
    plt.tight_layout()

    if ruta_salida:
        os.makedirs(os.path.dirname(ruta_salida) or ".", exist_ok=True)
        plt.savefig(ruta_salida, dpi=150)
        print(f"✔  Gráfico de barras guardado en: {ruta_salida}")
    else:
        plt.show()
    plt.close()


# ── Gráfico 2: Líneas de ingresos mensuales ─────────────────

def grafico_lineas_ingresos(df: pd.DataFrame, ruta_salida: str | None = None):
    """
    Genera un gráfico de líneas con la evolución de los ingresos
    brutos mensuales a lo largo del año.
    """
    if df.empty:
        print("⚠  No hay datos de ventas para generar el gráfico de líneas.")
        return

    df = df.copy()
    df["mes"] = df["fecha"].dt.to_period("M")
    ingresos = df.groupby("mes")["total"].sum()

    fig, ax = plt.subplots(figsize=(10, 6))
    ingresos.plot(ax=ax, marker="o", linewidth=2, color="steelblue")
    ax.fill_between(range(len(ingresos)), ingresos.values, alpha=0.15,
                    color="steelblue")
    ax.set_title("Evolución de ingresos brutos mensuales",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Ingresos (€)")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    plt.xticks(range(len(ingresos)),
               [str(m) for m in ingresos.index], rotation=45)
    plt.tight_layout()

    if ruta_salida:
        os.makedirs(os.path.dirname(ruta_salida) or ".", exist_ok=True)
        plt.savefig(ruta_salida, dpi=150)
        print(f"✔  Gráfico de líneas guardado en: {ruta_salida}")
    else:
        plt.show()
    plt.close()


# ── Resumen estadístico ─────────────────────────────────────

def resumen_ventas(df: pd.DataFrame):
    """Imprime un resumen rápido de las ventas cargadas."""
    if df.empty:
        print("⚠  No hay datos de ventas para resumir.")
        return

    print("\n" + "=" * 50)
    print("       RESUMEN DE VENTAS HISTÓRICAS")
    print("=" * 50)
    print(f"  Registros totales : {len(df)}")
    print(f"  Ingresos brutos   : {df['total'].sum():,.2f} €")
    print(f"  Venta media       : {df['total'].mean():,.2f} €")
    print(f"  Período           : {df['fecha'].min().date()} → "
          f"{df['fecha'].max().date()}")
    print("-" * 50)

    por_tipo = df.groupby("tipo").agg(
        unidades=("cantidad", "sum"),
        ingresos=("total", "sum"),
    )
    print(por_tipo.to_string())
    print("=" * 50 + "\n")


# ── Funciones auxiliares para la web ─────────────────────────

def _fig_to_base64(fig) -> str:
    """Convierte una figura Matplotlib a string base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#ffffff", edgecolor="none")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return img_b64


def grafico_barras_base64(df: pd.DataFrame) -> str | None:
    """Genera gráfico de barras del último trimestre y lo devuelve como base64."""
    if df.empty:
        return None

    df = df.copy()
    df["mes"] = df["fecha"].dt.to_period("M")
    ultimos_3 = sorted(df["mes"].unique())[-3:]
    df_trim = df[df["mes"].isin(ultimos_3)]

    if df_trim.empty:
        return None

    tabla = (
        df_trim.groupby(["mes", "tipo"])["cantidad"]
        .sum()
        .unstack(fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    colores = {"ProductoFisico": "#6366f1", "ProductoDigital": "#a78bfa"}
    tabla.plot(kind="bar", ax=ax, color=[colores.get(c, "#94a3b8") for c in tabla.columns],
               edgecolor="white", linewidth=0.8, width=0.7)
    ax.set_title("Volumen de ventas por tipo – Último trimestre",
                 fontsize=13, fontweight="bold", color="#1e293b", pad=15)
    ax.set_xlabel("Mes", fontsize=10, color="#64748b")
    ax.set_ylabel("Unidades vendidas", fontsize=10, color="#64748b")
    ax.legend(title="Tipo", frameon=False, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e2e8f0")
    ax.spines["bottom"].set_color("#e2e8f0")
    ax.tick_params(colors="#64748b", labelsize=9)
    ax.set_xticklabels([str(m) for m in tabla.index], rotation=0)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.patch.set_facecolor("#ffffff")

    return _fig_to_base64(fig)


def grafico_lineas_base64(df: pd.DataFrame) -> str | None:
    """Genera gráfico de ingresos mensuales y lo devuelve como base64."""
    if df.empty:
        return None

    df = df.copy()
    df["mes"] = df["fecha"].dt.to_period("M")
    ingresos = df.groupby("mes")["total"].sum()

    if ingresos.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(ingresos))
    ax.plot(x, ingresos.values, marker="o", linewidth=2.5,
            color="#6366f1", markersize=7, markerfacecolor="#ffffff",
            markeredgewidth=2, markeredgecolor="#6366f1", zorder=3)
    ax.fill_between(x, ingresos.values, alpha=0.08, color="#6366f1")
    ax.set_title("Evolución de ingresos brutos mensuales",
                 fontsize=13, fontweight="bold", color="#1e293b", pad=15)
    ax.set_xlabel("Mes", fontsize=10, color="#64748b")
    ax.set_ylabel("Ingresos (€)", fontsize=10, color="#64748b")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e2e8f0")
    ax.spines["bottom"].set_color("#e2e8f0")
    ax.tick_params(colors="#64748b", labelsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([str(m) for m in ingresos.index], rotation=45, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.patch.set_facecolor("#ffffff")

    return _fig_to_base64(fig)


def resumen_ventas_dict(df: pd.DataFrame) -> dict | None:
    """Devuelve un diccionario con las estadísticas clave de ventas."""
    if df.empty:
        return None

    por_tipo = df.groupby("tipo").agg(
        unidades=("cantidad", "sum"),
        ingresos=("total", "sum"),
    ).to_dict("index")

    return {
        "total_registros": len(df),
        "ingresos_brutos": df["total"].sum(),
        "venta_media": df["total"].mean(),
        "fecha_inicio": df["fecha"].min().strftime("%d/%m/%Y"),
        "fecha_fin": df["fecha"].max().strftime("%d/%m/%Y"),
        "por_tipo": por_tipo,
    }
