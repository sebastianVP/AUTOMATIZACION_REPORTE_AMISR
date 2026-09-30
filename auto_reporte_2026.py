# -*- coding: utf-8 -*-
"""
Script: auto_reporte_2026.py
Autor: Alexander Valdez

Descripción:
    Lee REPORTE_AUTOMATIZADO_2026.csv y genera un resumen
    mensual de operación del radar AMISR-14.

    Agrupa por MES + TIPO y suma GB y HORAS.

    Entrada:
        REPORTE_AUTOMATIZADO_2026.csv

    Salida:
        REPORTE_DIGDT_2026.csv
"""

import os
import pandas as pd

ARCHIVO_ENTRADA = "REPORTE_AUTOMATIZADO_2026.csv"
ARCHIVO_SALIDA = "REPORTE_DIGDT_2026.csv"

MESES = {
    1: "ENERO",
    2: "FEBRERO",
    3: "MARZO",
    4: "ABRIL",
    5: "MAYO",
    6: "JUNIO",
    7: "JULIO",
    8: "AGOSTO",
    9: "SEPTIEMBRE",
    10: "OCTUBRE",
    11: "NOVIEMBRE",
    12: "DICIEMBRE"
}


def leer_archivo(archivo):
    if not os.path.exists(archivo):
        print(f"❌ No se encontró el archivo: {archivo}")
        return None

    try:
        df = pd.read_csv(archivo)
    except Exception as e:
        print(f"❌ Error leyendo {archivo}: {e}")
        return None

    columnas = {"FECHA", "TIPO", "SIZE (GB)", "HORAS"}

    if not columnas.issubset(df.columns):
        print("❌ El archivo CSV no contiene las columnas esperadas.")
        print(f"Columnas encontradas: {list(df.columns)}")
        return None

    return df


def preparar_datos(df):
    df["FECHA"] = df["FECHA"].astype(str).str.strip()
    df["TIPO"] = df["TIPO"].astype(str).str.strip().str.lower()
    df["SIZE (GB)"] = pd.to_numeric(df["SIZE (GB)"], errors="coerce").fillna(0)
    df["HORAS"] = pd.to_numeric(df["HORAS"], errors="coerce").fillna(0)
    df["MES_NUM"] = pd.to_numeric(df["FECHA"].str[4:6], errors="coerce")
    df["MES"] = df["MES_NUM"].map(MESES)

    return df.dropna(subset=["MES"])


def generar_resumen(df):
    resumen = df.groupby(
        ["MES_NUM", "MES", "TIPO"], as_index=False
    ).agg({
        "SIZE (GB)": "sum",
        "HORAS": "sum"
    })

    resumen["SIZE (GB)"] = resumen["SIZE (GB)"].round(2)
    resumen["HORAS"] = resumen["HORAS"].round(2)
    resumen = resumen.rename(columns={"SIZE (GB)": "GB"})
    resumen["TIPO"] = resumen["TIPO"].str.upper()
    resumen = resumen.sort_values(["MES_NUM", "TIPO"])

    return resumen[["MES", "TIPO", "GB", "HORAS"]]


def mostrar_resumen(resumen):
    print("\n")
    print("=" * 65)
    print("REPORTE MENSUAL AMISR-14")
    print("=" * 65)

    if resumen.empty:
        print("⚠️ No existen datos para mostrar.")
        return

    print(f"{'MES':<15}{'TIPO':<10}{'GB':>15}{'HORAS':>15}")
    print("-" * 65)

    for _, fila in resumen.iterrows():
        print(f"{fila['MES']:<15}{fila['TIPO']:<10}{fila['GB']:>15.2f}{fila['HORAS']:>15.2f}")

    print("-" * 65)


def guardar_reporte(resumen, archivo_salida):
    try:
        resumen.to_csv(archivo_salida, index=False, encoding="utf-8")
        print("\n✅ Reporte generado correctamente:")
        print(f"   {archivo_salida}")
    except Exception as e:
        print(f"❌ Error guardando el reporte: {e}")


def main():
    print("\n")
    print("=" * 65)
    print(" AUTO REPORTE AMISR-14 - 2026")
    print("=" * 65)

    df = leer_archivo(ARCHIVO_ENTRADA)

    if df is None:
        return

    print(f"\n📄 Archivo de entrada:\n   {ARCHIVO_ENTRADA}")
    print(f"📊 Registros encontrados: {len(df)}")

    df = preparar_datos(df)
    resumen = generar_resumen(df)

    mostrar_resumen(resumen)
    guardar_reporte(resumen, ARCHIVO_SALIDA)

    print("\n✅ Proceso terminado.")


if __name__ == "__main__":
    main()
