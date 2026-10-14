# -*- coding: utf-8 -*-
"""
Script: auto_scanner_2026v2.py
Autor: Alexander Valdez

Descripción:
    Automatiza el reporte de horas de operación del radar AMISR-14
    y genera un diagnóstico de los archivos de adquisición.

Uso:
    python3 auto_scanner_2026v2.py
    python3 auto_scanner_2026v2.py /media/soporte/Expansion/AMISR/2026

Archivos de salida:
    1. REPORTE_AUTOMATIZADO_2026v2.csv
       FECHA,TIPO,SIZE (GB),HORAS

    2. REPORTE_DIAGNOSTICO_ARCHIVOS_2026v2.csv
       Métricas por carpeta de adquisición.

Notas:
    - MES (Mesosphera): cada archivo .dt0.h5 válido representa 4 minutos,
      según la métrica confirmada para este experimento.
    - Los archivos potencialmente parciales se identifican por tamaño
      (menores al 80 % de la mediana). Es una heurística, no una garantía
      de integridad del archivo.
    - ISR, ESF, LPD y MET conservan sus fórmulas históricas.
    - El intervalo entre mtimes es una estimación de periodicidad y no
      necesariamente equivale a la duración real de adquisición.
    - El CSV histórico conserva registros ausentes del disco y no reemplaza
      un registro existente por otro de menor tamaño.
"""

import os
import csv
import sys
import statistics
from datetime import datetime, timedelta


# ============================================================
# CONFIGURACIÓN
# ============================================================

DATA_DIR_DEFAULT = "/mnt/data_amisr"
OUTPUT_FILE = "REPORTE_AUTOMATIZADO_2026v2.csv"
DIAGNOSTIC_FILE = "REPORTE_DIAGNOSTICO_ARCHIVOS_2026v2.csv"
DIAS_REVISAR = 40

FIELDNAMES = ["FECHA", "TIPO", "SIZE (GB)", "HORAS"]

DIAGNOSTIC_FIELDNAMES = [
    "FECHA",
    "CARPETA",
    "EXPERIMENTO",
    "TIPO",
    "ARCHIVOS",
    "ARCHIVOS_VALIDOS",
    "SIZE_TOTAL_GB",
    "SIZE_MEDIANA_MB",
    "SIZE_PROMEDIO_MB",
    "INTERVALO_MIN",
    "VOLUMEN_24H_GB",
    "HORAS_ESTIMADAS",
    "ARCHIVOS_PARCIALES",
    "ESTADO_PERIODICIDAD",
]


# ============================================================
# DIRECTORIOS Y FECHAS
# ============================================================

def obtener_directorio():
    """Obtiene el directorio desde el argumento o usa el predeterminado."""
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        print(f"📁 Directorio proporcionado: {data_dir}")
        return data_dir

    print(f"📁 Utilizando directorio por defecto: {DATA_DIR_DEFAULT}")
    return DATA_DIR_DEFAULT


def obtener_fechas_a_revisar(dias=DIAS_REVISAR):
    """Genera las fechas de los últimos N días, incluyendo hoy."""
    hoy = datetime.now().date()
    return {
        (hoy - timedelta(days=i)).strftime("%Y%m%d")
        for i in range(dias)
    }


def es_carpeta_amisr(nombre):
    """Comprueba el formato de carpeta YYYYMMDD.xxx."""
    return (
        len(nombre) >= 12
        and nombre[:8].isdigit()
        and nombre[8] == "."
        and nombre[9:].isdigit()
    )


def listar_carpetas_recientes(base_dir, fechas):
    """Lista las carpetas de adquisición de las fechas seleccionadas."""
    try:
        elementos = os.listdir(base_dir)
    except OSError as e:
        print(f"❌ Error leyendo {base_dir}: {e}")
        return []

    carpetas = []
    for nombre in elementos:
        if not es_carpeta_amisr(nombre) or nombre[:8] not in fechas:
            continue

        ruta = os.path.join(base_dir, nombre)
        if os.path.isdir(ruta):
            carpetas.append(nombre)

    return sorted(carpetas)


# ============================================================
# IDENTIFICACIÓN DEL EXPERIMENTO
# ============================================================

def obtener_archivo_exp(carpeta_path):
    """Obtiene el archivo .exp ubicado en Setup/."""
    setup_dir = os.path.join(carpeta_path, "Setup")
    if not os.path.isdir(setup_dir):
        return None

    try:
        archivos_exp = sorted(
            nombre for nombre in os.listdir(setup_dir)
            if nombre.lower().endswith(".exp")
            and os.path.isfile(os.path.join(setup_dir, nombre))
        )
    except OSError as e:
        print(f"⚠️ No se pudo leer {setup_dir}: {e}")
        return None

    if not archivos_exp:
        return None

    if len(archivos_exp) > 1:
        print(
            f"⚠️ Hay {len(archivos_exp)} archivos .exp en {setup_dir}. "
            f"Se utilizará {archivos_exp[0]}."
        )

    return archivos_exp[0]


def identificar_tipo(nombre_exp):
    """Identifica la categoría por el nombre del archivo .exp."""
    if not nombre_exp:
        return "n/a"

    nombre = os.path.basename(nombre_exp).lower()
    stem = os.path.splitext(nombre)[0]

    if "mesosphera" in nombre or "mesosphere" in nombre:
        return "mes"
    if "meteor" in nombre or stem.startswith("met"):
        return "met"
    if "esf" in nombre:
        return "esf"
    if "isr" in nombre:
        return "isr"
    if "lpd" in nombre:
        return "lpd"

    token = stem.replace("-", "_").split("_")[0].strip()
    if token and token.isalnum():
        return token[:12].lower()

    return "desconocido"


# ============================================================
# TAMAÑOS Y CÁLCULO DE HORAS
# ============================================================

def obtener_tamano_gb(carpeta_path):
    """Calcula el tamaño total recursivo de la carpeta en GB decimales."""
    total_bytes = 0
    try:
        for raiz, _, archivos in os.walk(carpeta_path):
            for archivo in archivos:
                ruta = os.path.join(raiz, archivo)
                try:
                    if os.path.isfile(ruta):
                        total_bytes += os.path.getsize(ruta)
                except OSError:
                    continue
        return total_bytes / 1_000_000_000
    except OSError as e:
        print(f"⚠️ No se pudo obtener tamaño de {carpeta_path}: {e}")
        return 0.0


def calcular_horas(tipo, size_gb, num_archivos=None):
    """
    Calcula horas de adquisición.

    MES: cada archivo válido representa 4 minutos, según la métrica
    confirmada para Mesosphera.
    Otras categorías: mantienen las fórmulas históricas.
    Devuelve None si no existe una fórmula o información suficiente.
    """
    tipo = (tipo or "").lower().strip()

    if tipo == "mes":
        if num_archivos is None or num_archivos <= 0:
            return None
        return round(num_archivos * 4 / 60, 2)

    if tipo == "isr":
        return round((11 * size_gb) / 59, 2)
    if tipo == "esf":
        return round((13 * size_gb) / 35, 2)
    if tipo == "lpd":
        return round((24 * size_gb) / 136.2, 2)
    if tipo == "met":
        return round((11 * size_gb) / 108.0, 2)

    return None


# ============================================================
# ARCHIVOS DE DATOS
# ============================================================

def obtener_archivos_datos(carpeta_path):
    """Obtiene archivos .dt0.h5 del nivel principal de la carpeta."""
    resultados = []
    try:
        for nombre in os.listdir(carpeta_path):
            ruta = os.path.join(carpeta_path, nombre)
            if not os.path.isfile(ruta) or not nombre.lower().endswith(".dt0.h5"):
                continue
            try:
                info = os.stat(ruta)
                resultados.append({
                    "nombre": nombre,
                    "ruta": ruta,
                    "mtime": info.st_mtime,
                    "size_bytes": info.st_size,
                })
            except OSError as e:
                print(f"⚠️ No se pudieron leer metadatos de {ruta}: {e}")
    except OSError as e:
        print(f"⚠️ No se pudo listar {carpeta_path}: {e}")

    return sorted(resultados, key=lambda a: (a["mtime"], a["nombre"]))


def obtener_archivos_validos_mes(archivos):
    """
    Excluye provisionalmente archivos cuyo tamaño sea menor al 80 %
    de la mediana. Es una heurística para detectar posibles archivos
    parciales; no garantiza la integridad real del HDF5.
    """
    if not archivos:
        return []

    tamanos = [a["size_bytes"] for a in archivos]
    mediana_bytes = statistics.median(tamanos)
    if mediana_bytes <= 0:
        return []

    umbral = mediana_bytes * 0.80
    return [a for a in archivos if a["size_bytes"] >= umbral]


# ============================================================
# ESTIMACIÓN DE PERIODICIDAD
# ============================================================

def estimar_periodicidad(archivos):
    """Estima el intervalo típico entre mtimes consecutivos."""
    if len(archivos) < 3:
        return None, "INSUFICIENTES_DATOS"

    intervalos = []
    for anterior, actual in zip(archivos, archivos[1:]):
        delta = actual["mtime"] - anterior["mtime"]
        if delta > 0:
            intervalos.append(delta)

    if len(intervalos) < 2:
        return None, "INSUFICIENTES_INTERVALOS"

    mediana = statistics.median(intervalos)
    tolerancia = max(30.0, mediana * 0.20)
    cercanos = [d for d in intervalos if abs(d - mediana) <= tolerancia]
    estado = "ESTABLE" if len(cercanos) / len(intervalos) >= 0.70 else "IRREGULAR_REVISAR"
    return mediana, estado


# ============================================================
# DIAGNÓSTICO POR CARPETA
# ============================================================

def diagnosticar_carpeta(base_dir, carpeta):
    """Calcula métricas de adquisición para una carpeta."""
    carpeta_path = os.path.join(base_dir, carpeta)
    nombre_exp = obtener_archivo_exp(carpeta_path)
    tipo = identificar_tipo(nombre_exp)
    archivos = obtener_archivos_datos(carpeta_path)

    total_bytes = sum(a["size_bytes"] for a in archivos)
    tamanos = [a["size_bytes"] for a in archivos]
    mediana_bytes = statistics.median(tamanos) if tamanos else 0
    promedio_bytes = total_bytes / len(archivos) if archivos else 0

    intervalo_seg, estado = estimar_periodicidad(archivos)
    intervalo_min = round(intervalo_seg / 60.0, 2) if intervalo_seg is not None else ""

    parciales = []
    if mediana_bytes > 0:
        umbral_parcial = mediana_bytes * 0.80
        parciales = [
            a["nombre"] for a in archivos
            if a["size_bytes"] < umbral_parcial
        ]

    volumen_24h_gb = ""
    horas_estimadas = ""
    archivos_validos = archivos

    if tipo == "mes":
        archivos_validos = obtener_archivos_validos_mes(archivos)
        horas_estimadas = calcular_horas(
            tipo="mes",
            size_gb=total_bytes / 1_000_000_000,
            num_archivos=len(archivos_validos),
        )
        if horas_estimadas is None:
            horas_estimadas = ""

    if intervalo_seg is not None and intervalo_seg > 0 and mediana_bytes > 0:
        archivos_24h = 86400.0 / intervalo_seg
        volumen_24h_gb = round(archivos_24h * mediana_bytes / 1_000_000_000, 3)

        # Para MES se usa la duración validada por archivo; para otras
        # categorías, esta es una estimación basada en la periodicidad.
        if tipo != "mes":
            horas_estimadas = round(len(archivos) * intervalo_seg / 3600.0, 2)

    registro = {
        "FECHA": carpeta[:8],
        "CARPETA": carpeta,
        "EXPERIMENTO": nombre_exp or "N/A",
        "TIPO": tipo,
        "ARCHIVOS": len(archivos),
        "ARCHIVOS_VALIDOS": len(archivos_validos) if tipo == "mes" else "",
        "SIZE_TOTAL_GB": round(total_bytes / 1_000_000_000, 3),
        "SIZE_MEDIANA_MB": round(mediana_bytes / 1_000_000, 2),
        "SIZE_PROMEDIO_MB": round(promedio_bytes / 1_000_000, 2),
        "INTERVALO_MIN": intervalo_min,
        "VOLUMEN_24H_GB": volumen_24h_gb,
        "HORAS_ESTIMADAS": horas_estimadas,
        "ARCHIVOS_PARCIALES": ";".join(parciales),
        "ESTADO_PERIODICIDAD": estado,
    }

    print(
        f"{carpeta} | {tipo.upper()} | archivos={len(archivos)} | "
        f"válidos_mes={len(archivos_validos) if tipo == 'mes' else 'N/A'} | "
        f"{registro['SIZE_TOTAL_GB']:.3f} GB | "
        f"intervalo={intervalo_min if intervalo_min != '' else 'N/D'} min | "
        f"horas={horas_estimadas if horas_estimadas != '' else 'N/D'} | "
        f"estado={estado}"
    )
    if parciales:
        print("   ⚠️ Posibles archivos parciales: " + ", ".join(parciales))

    return registro


# ============================================================
# ESCANEO GENERAL
# ============================================================

def escanear_radar(base_dir, fechas):
    """Escanea carpetas y agrupa el reporte por FECHA + TIPO."""
    carpetas = listar_carpetas_recientes(base_dir, fechas)
    if not carpetas:
        print("⚠️ No se encontraron carpetas recientes.")
        return [], []

    acumulado = {}
    horas_mes = {}
    diagnosticos = []

    print("\n=== ESCANEO AMISR-14 ===")
    for carpeta in carpetas:
        carpeta_path = os.path.join(base_dir, carpeta)
        nombre_exp = obtener_archivo_exp(carpeta_path)
        tipo = identificar_tipo(nombre_exp)
        size_gb = obtener_tamano_gb(carpeta_path)

        print(f"{carpeta} | {tipo.upper()} | {size_gb:.3f} GB")
        if tipo in ("n/a", "desconocido"):
            print(f"   ⚠️ No se identificó la categoría: {nombre_exp or 'no existe archivo .exp'}")

        clave = (carpeta[:8], tipo)
        acumulado[clave] = acumulado.get(clave, 0.0) + size_gb

        diagnostico = diagnosticar_carpeta(base_dir, carpeta)
        diagnosticos.append(diagnostico)

        if tipo == "mes":
            horas = diagnostico["HORAS_ESTIMADAS"]
            if horas != "":
                horas_mes[clave] = horas_mes.get(clave, 0.0) + float(horas)

    registros = []
    for (fecha, tipo), size_gb in sorted(acumulado.items()):
        if tipo == "mes":
            horas = round(horas_mes[(fecha, tipo)], 2) if (fecha, tipo) in horas_mes else None
        else:
            horas = calcular_horas(tipo, size_gb)

        registros.append({
            "FECHA": fecha,
            "TIPO": tipo,
            "SIZE (GB)": round(size_gb, 2),
            "HORAS": "" if horas is None else horas,
        })

    return registros, diagnosticos


# ============================================================
# CSV HISTÓRICO
# ============================================================

def cargar_csv_existente(output_file):
    """Lee el CSV histórico si existe."""
    if not os.path.exists(output_file):
        return []
    try:
        with open(output_file, "r", encoding="utf-8", newline="") as archivo:
            return list(csv.DictReader(archivo))
    except (OSError, csv.Error) as e:
        print(f"⚠️ Error leyendo {output_file}: {e}")
        return []


def actualizar_csv(registros_nuevos, output_file):
    """Actualiza el histórico sin eliminar datos ni reducir tamaños registrados."""
    existentes = cargar_csv_existente(output_file)
    existentes_dict = {}

    for registro in existentes:
        clave = (registro.get("FECHA", ""), registro.get("TIPO", "").lower())
        existentes_dict[clave] = registro

    actualizados = agregados = conservados = 0

    for nuevo in registros_nuevos:
        fecha = nuevo["FECHA"]
        tipo = nuevo["TIPO"].lower()
        clave = (fecha, tipo)
        nuevo_size = float(nuevo["SIZE (GB)"])

        if clave not in existentes_dict:
            existentes_dict[clave] = nuevo
            agregados += 1
            print(f"➕ NUEVO: {fecha} | {tipo.upper()} | {nuevo_size:.2f} GB")
            continue

        anterior = existentes_dict[clave]
        try:
            anterior_size = float(anterior.get("SIZE (GB)", 0) or 0)
        except (TypeError, ValueError):
            anterior_size = 0.0

        try:
            anterior_horas = float(anterior.get("HORAS", "") or 0)
        except (TypeError, ValueError):
            anterior_horas = 0.0
        try:
            nuevas_horas = float(nuevo.get("HORAS", "") or 0)
        except (TypeError, ValueError):
            nuevas_horas = 0.0

        # Mantiene la protección histórica para tamaños menores. Si el tamaño
        # es igual, permite actualizar horas (por ejemplo, al entrar más archivos MES).
        debe_actualizar = (
            nuevo_size > anterior_size
            or (nuevo_size == anterior_size and nuevas_horas != anterior_horas)
        )

        if debe_actualizar:
            existentes_dict[clave] = nuevo
            actualizados += 1
            print(
                f"🔄 ACTUALIZADO: {fecha} | {tipo.upper()} | "
                f"{anterior_size:.2f} → {nuevo_size:.2f} GB | "
                f"HORAS: {anterior_horas:.2f} → {nuevas_horas:.2f}"
            )
        elif nuevo_size == anterior_size:
            conservados += 1
            print(f"✓ SIN CAMBIOS: {fecha} | {tipo.upper()} | {anterior_size:.2f} GB")
        else:
            conservados += 1
            print(
                f"⚠️ MENOR EN DISCO: {fecha} | {tipo.upper()} | "
                f"CSV={anterior_size:.2f} GB | DISCO={nuevo_size:.2f} GB | SE CONSERVA CSV"
            )

    todos = list(existentes_dict.values())
    todos.sort(key=lambda r: (r.get("FECHA", ""), r.get("TIPO", "")))

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            for registro in todos:
                writer.writerow({campo: registro.get(campo, "") for campo in FIELDNAMES})
    except OSError as e:
        print(f"❌ No se pudo escribir {output_file}: {e}")
        return

    print("\n" + "=" * 70)
    print("ACTUALIZACIÓN DEL REPORTE HISTÓRICO")
    print("=" * 70)
    print(f"➕ Registros nuevos       : {agregados}")
    print(f"🔄 Registros actualizados : {actualizados}")
    print(f"✓ Registros conservados  : {conservados}")
    print(f"📊 Total registros        : {len(todos)}")
    print(f"📄 Archivo                : {output_file}")


# ============================================================
# CSV DE DIAGNÓSTICO
# ============================================================

def guardar_diagnostico(registros, output_file):
    """Guarda el diagnóstico detallado de las carpetas escaneadas."""
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(
                archivo,
                fieldnames=DIAGNOSTIC_FIELDNAMES,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(registros)
    except OSError as e:
        print(f"❌ No se pudo escribir {output_file}: {e}")
        return

    print(f"📄 Diagnóstico             : {output_file}")
    print(f"📊 Carpetas diagnosticadas : {len(registros)}")


# ============================================================
# VISUALIZACIÓN EN CONSOLA
# ============================================================

def mostrar_resultados(registros):
    """Muestra los registros escaneados antes de la actualización histórica."""
    print("\n" + "=" * 75)
    print(f"REPORTE AMISR-14 - ÚLTIMOS {DIAS_REVISAR} DÍAS")
    print("=" * 75)

    if not registros:
        print("No hay registros.")
        return

    print(f"{'FECHA':<12}{'TIPO':<10}{'SIZE (GB)':>14}{'HORAS':>12}")
    print("-" * 75)
    for registro in registros:
        horas = registro["HORAS"]
        horas_texto = f"{float(horas):.2f}" if horas not in (None, "") else "N/D"
        print(
            f"{registro['FECHA']:<12}"
            f"{registro['TIPO'].upper():<10}"
            f"{float(registro['SIZE (GB)']):>14.2f}"
            f"{horas_texto:>12}"
        )
    print("-" * 75)


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("\n" + "=" * 70)
    print(" AUTO SCANNER AMISR-14 - 2026 v2")
    print("=" * 70)

    data_dir = obtener_directorio()
    print(f"\n📂 DIRECTORIO DE DATOS:\n   {data_dir}")

    if not os.path.exists(data_dir):
        print(f"\n❌ No existe el directorio:\n   {data_dir}")
        return
    if not os.path.isdir(data_dir):
        print(f"\n❌ La ruta indicada no es un directorio:\n   {data_dir}")
        return

    fechas = obtener_fechas_a_revisar(DIAS_REVISAR)
    print(f"\n📅 Revisando últimos {DIAS_REVISAR} días.")

    registros, diagnosticos = escanear_radar(data_dir, fechas)
    mostrar_resultados(registros)
    guardar_diagnostico(diagnosticos, DIAGNOSTIC_FILE)
    actualizar_csv(registros, OUTPUT_FILE)
    print("\n✅ Proceso terminado.")


if __name__ == "__main__":
    main()