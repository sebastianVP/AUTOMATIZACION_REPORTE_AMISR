# -*- coding: utf-8 -*-
"""
Script: auto_scanner_2026.py
Autor: Alexander Valdez

Descripción:
    Automatiza el reporte de horas totales de operación
    del radar AMISR-14.

    Uso normal:
        python3 auto_scanner_2026.py

    Utiliza por defecto:
        /mnt/data_amisr

    Uso con directorio personalizado:
        python3 auto_scanner_2026.py /media/soporte/Expansion/AMISR/2026

    El script:
    - Escanea el directorio indicado.
    - Revisa los últimos 10 días.
    - Detecta carpetas YYYYMMDD.xxx.
    - Busca el archivo .exp dentro de Setup/.
    - Identifica el tipo mediante las 3 primeras letras.
    - Agrupa por FECHA + TIPO.
    - Suma el tamaño de todas las carpetas correspondientes.
    - Calcula las horas de operación.
    - Actualiza el CSV únicamente cuando el nuevo tamaño
      encontrado es mayor que el registrado.
    - Conserva información del CSV si el disco contiene
      menos información o si la fecha ya no está disponible.
"""

import os
import subprocess
import csv
import sys
from datetime import datetime, timedelta


# ============================================================
# CONFIGURACIÓN
# ============================================================

DATA_DIR_DEFAULT = "/mnt/data_amisr"

OUTPUT_FILE = "REPORTE_AUTOMATIZADO_2026.csv"

DIAS_REVISAR = 5

FIELDNAMES = ["FECHA", "TIPO", "SIZE (GB)", "HORAS"]


# ============================================================
# OBTENER DIRECTORIO DESDE LA LÍNEA DE COMANDOS
# ============================================================

def obtener_directorio():
    """
    Obtiene el directorio desde el argumento de línea de comandos.

    Sin argumento:
        /mnt/data_amisr

    Con argumento:
        python3 auto_scanner_2026.py /ruta/personalizada

    Si se proporcionan varios argumentos, se utiliza solamente
    el primero.
    """

    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        print(f"📁 Directorio proporcionado: {data_dir}")
        return data_dir

    print(f"📁 Utilizando directorio por defecto: {DATA_DIR_DEFAULT}")

    return DATA_DIR_DEFAULT


# ============================================================
# FECHAS A REVISAR
# ============================================================

def obtener_fechas_a_revisar(dias=10):
    """Obtiene las fechas de los últimos N días incluyendo hoy."""

    hoy = datetime.now().date()

    return {(hoy - timedelta(days=i)).strftime("%Y%m%d") for i in range(dias)}


# ============================================================
# VALIDAR CARPETAS AMISR
# ============================================================

def es_carpeta_amisr(nombre):
    """Verifica que una carpeta tenga formato YYYYMMDD.xxx."""

    return len(nombre) >= 12 and nombre[:8].isdigit() and nombre[8] == "." and nombre[9:].isdigit()


# ============================================================
# LISTAR CARPETAS RECIENTES
# ============================================================

def listar_carpetas_recientes(base_dir, fechas):
    """Lista carpetas AMISR correspondientes a las fechas indicadas."""

    try:
        elementos = os.listdir(base_dir)
    except OSError as e:
        print(f"❌ Error leyendo {base_dir}: {e}")
        return []

    carpetas = []

    for nombre in elementos:

        if not es_carpeta_amisr(nombre):
            continue

        fecha = nombre[:8]

        if fecha not in fechas:
            continue

        ruta = os.path.join(base_dir, nombre)

        if os.path.isdir(ruta):
            carpetas.append(nombre)

    return sorted(carpetas)


# ============================================================
# OBTENER TIPO DE EXPERIMENTO
# ============================================================

def obtener_tipo(carpeta_path):
    """
    Busca un archivo .exp dentro de Setup/.

    Ejemplo:
        ISR_1Beam_oblique_10ms_25.exp

    Resultado:
        isr
    """

    setup_dir = os.path.join(carpeta_path, "Setup")

    if not os.path.isdir(setup_dir):
        return "N/A"

    try:
        archivos = os.listdir(setup_dir)
    except OSError as e:
        print(f"⚠️ No se pudo leer {setup_dir}: {e}")
        return "N/A"

    archivos_exp = sorted([f for f in archivos if f.lower().endswith(".exp")])

    if not archivos_exp:
        return "N/A"

    return archivos_exp[0][:3].lower()


# ============================================================
# OBTENER TAMAÑO
# ============================================================

def obtener_tamano_gb(carpeta_path):
    """
    Obtiene el tamaño de una carpeta en GB utilizando du -sb.
    """

    try:

        salida = subprocess.check_output(["du", "-sb", carpeta_path], text=True, stderr=subprocess.DEVNULL)

        bytes_totales = int(salida.split()[0])

        return bytes_totales / (1024 ** 3)

    except (subprocess.CalledProcessError, ValueError, OSError) as e:

        print(f"⚠️ No se pudo obtener tamaño de {carpeta_path}: {e}")

        return 0.0


# ============================================================
# CALCULAR HORAS
# ============================================================

def calcular_horas(tipo, size_gb):
    """
    Calcula las horas de operación según el tipo
    de experimento.
    """

    tipo = tipo.lower()

    if tipo == "isr":
        return round((11 * size_gb) / 59, 2)

    elif tipo == "esf":
        return round((13 * size_gb) / 35, 2)

    elif tipo == "lpd":
        return round((24 * size_gb) / 136.2, 2)

    elif tipo == "met":
        return round((11 * size_gb) / 108.0, 2)

    return 0.0


# ============================================================
# ESCANEAR RADAR
# ============================================================

def escanear_radar(base_dir, fechas):
    """
    Escanea las carpetas recientes y agrupa los datos por
    FECHA + TIPO.
    """

    carpetas = listar_carpetas_recientes(base_dir, fechas)

    if not carpetas:
        print("⚠️ No se encontraron carpetas recientes.")
        return []

    acumulado = {}

    print("\n=== ESCANEO AMISR-14 ===")

    for carpeta in carpetas:

        fecha = carpeta[:8]

        carpeta_path = os.path.join(base_dir, carpeta)

        tipo = obtener_tipo(carpeta_path)

        size_gb = obtener_tamano_gb(carpeta_path)

        print(f"{carpeta} | {tipo.upper()} | {size_gb:.2f} GB")

        if tipo == "N/A":

            print(
                f"   ⚠️ No se encontró archivo .exp en {carpeta}"
            )

            continue

        clave = (fecha, tipo)

        if clave not in acumulado:
            acumulado[clave] = 0.0

        acumulado[clave] += size_gb

    registros = []

    for (fecha, tipo), size_gb in sorted(acumulado.items()):

        horas = calcular_horas(tipo, size_gb)

        registros.append({
            "FECHA": fecha,
            "TIPO": tipo,
            "SIZE (GB)": round(size_gb, 2),
            "HORAS": horas
        })

    return registros


# ============================================================
# CARGAR CSV EXISTENTE
# ============================================================

def cargar_csv_existente(output_file):
    """Lee el CSV existente."""

    if not os.path.exists(output_file):
        return []

    try:

        with open(output_file, "r", encoding="utf-8") as f:

            return list(csv.DictReader(f))

    except (OSError, csv.Error) as e:

        print(f"⚠️ Error leyendo {output_file}: {e}")

        return []


# ============================================================
# ACTUALIZAR CSV
# ============================================================

def actualizar_csv(registros_nuevos, output_file, fechas):
    """
    Actualiza el CSV aplicando las siguientes reglas:

    - Registro no existente -> AGREGAR.
    - Nuevo tamaño > CSV -> ACTUALIZAR.
    - Nuevo tamaño = CSV -> CONSERVAR.
    - Nuevo tamaño < CSV -> CONSERVAR.
    - Fecha existente en CSV pero ausente del disco -> CONSERVAR.
    """

    existentes = cargar_csv_existente(output_file)

    existentes_dict = {}

    for r in existentes:

        fecha = r.get("FECHA", "")

        tipo = r.get("TIPO", "").lower()

        clave = (fecha, tipo)

        existentes_dict[clave] = r

    actualizados = 0

    agregados = 0

    conservados = 0

    for nuevo in registros_nuevos:

        fecha = nuevo["FECHA"]

        tipo = nuevo["TIPO"].lower()

        clave = (fecha, tipo)

        nuevo_size = float(nuevo["SIZE (GB)"])

        if clave not in existentes_dict:

            existentes_dict[clave] = nuevo

            agregados += 1

            print(
                f"➕ NUEVO: {fecha} | "
                f"{tipo.upper()} | "
                f"{nuevo_size:.2f} GB"
            )

            continue

        anterior = existentes_dict[clave]

        anterior_size = float(
            anterior["SIZE (GB)"]
        )

        if nuevo_size > anterior_size:

            existentes_dict[clave] = nuevo

            actualizados += 1

            print(
                f"🔄 ACTUALIZADO: {fecha} | "
                f"{tipo.upper()} | "
                f"{anterior_size:.2f} → "
                f"{nuevo_size:.2f} GB"
            )

        elif nuevo_size == anterior_size:

            conservados += 1

            print(
                f"✓ SIN CAMBIOS: {fecha} | "
                f"{tipo.upper()} | "
                f"{anterior_size:.2f} GB"
            )

        else:

            conservados += 1

            print(
                f"⚠️ MENOR EN DISCO: {fecha} | "
                f"{tipo.upper()} | "
                f"CSV={anterior_size:.2f} GB | "
                f"DISCO={nuevo_size:.2f} GB | "
                f"SE CONSERVA CSV"
            )

    todos = list(existentes_dict.values())

    todos.sort(key=lambda r: (r.get("FECHA", ""), r.get("TIPO", "")))

    with open(output_file, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDNAMES
        )

        writer.writeheader()

        writer.writerows(todos)

    print("\n" + "=" * 70)
    print("ACTUALIZACIÓN DEL REPORTE")
    print("=" * 70)

    print(f"➕ Registros nuevos       : {agregados}")

    print(f"🔄 Registros actualizados : {actualizados}")

    print(f"✓ Registros conservados  : {conservados}")

    print(f"📊 Total registros        : {len(todos)}")

    print(f"📄 Archivo                : {output_file}")


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

def mostrar_resultados(registros):
    """Muestra los registros encontrados durante el escaneo."""

    print("\n" + "=" * 65)

    print(f"REPORTE AMISR-14 - ÚLTIMOS {DIAS_REVISAR} DÍAS")

    print("=" * 65)

    if not registros:

        print("No hay registros.")

        return

    print(f"{'FECHA':<12}{'TIPO':<8}{'SIZE (GB)':>12}{'HORAS':>12}")

    print("-" * 65)

    for r in registros:

        print(f"{r['FECHA']:<12}{r['TIPO'].upper():<8}{float(r['SIZE (GB)']):>12.2f}{float(r['HORAS']):>12.2f}")

    print("-" * 65)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")

    print("=" * 70)

    print(" AUTO SCANNER AMISR-14 - 2026")

    print("=" * 70)

    # --------------------------------------------------------
    # Obtener directorio
    # --------------------------------------------------------

    data_dir = obtener_directorio()

    print(f"\n📂 DIRECTORIO DE DATOS:")
    print(f"   {data_dir}")

    # --------------------------------------------------------
    # Verificar directorio
    # --------------------------------------------------------

    if not os.path.exists(data_dir):

        print(
            f"\n❌ No existe el directorio:"
            f"\n   {data_dir}"
        )

        return

    if not os.path.isdir(data_dir):

        print(
            f"\n❌ La ruta indicada no es un directorio:"
            f"\n   {data_dir}"
        )

        return

    # --------------------------------------------------------
    # Fechas
    # --------------------------------------------------------

    fechas = obtener_fechas_a_revisar(
        DIAS_REVISAR
    )

    print(
        f"\n📅 Revisando últimos "
        f"{DIAS_REVISAR} días:"
    )

    for fecha in sorted(fechas):

        print(f"   {fecha}")

    # --------------------------------------------------------
    # Escanear
    # --------------------------------------------------------

    registros = escanear_radar(
        data_dir,
        fechas
    )

    # --------------------------------------------------------
    # Mostrar
    # --------------------------------------------------------

    mostrar_resultados(
        registros
    )

    # --------------------------------------------------------
    # Actualizar CSV
    # --------------------------------------------------------

    actualizar_csv(
        registros,
        OUTPUT_FILE,
        fechas
    )

    print("\n✅ Proceso terminado.")


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()
