# AUTO_REPORTS_AMISR_14

Automatización de reportes de operación del radar **AMISR-14** del Radio Observatorio de Jicamarca (ROJ) – IGP.

## 1. Flujo del proyecto

```text
Datos AMISR-14
      │
      ▼
auto_scanner_2026.py
      │
      ▼
REPORTE_AUTOMATIZADO_2026.csv
      │
      ▼
auto_reporte_2026.py
      │
      ▼
REPORTE_DIGDT_2026.csv
      │
      ▼
auto_send_2026.py
      │
      ▼
GitHub
      │
      ▼
actualiza_google_drive_final.py
      │
      ▼
Google Drive
      │
      ▼
DONE_POI 2026 ROJ.xlsx
```

---

## 2. Archivos principales

```text
AUTO_REPORTS_AMISR_14/
├── actualiza_google_drive_final.py
├── requirements.txt
├── README.md
├── .gitignore
├── cron_github.log
└── cron_google_drive.log
```

Credenciales:

```text
/home/soporte/.google/amisr-service-account.json
```

Las credenciales no deben estar dentro del repositorio.

---

# 3. Dependencias

`requirements.txt`:

```text
pandas
openpyxl
google-auth
google-api-python-client
```

Instalar:

```bash
/home/soporte/anaconda3/bin/pip install -r requirements.txt
```

Validar:

```bash
/home/soporte/anaconda3/bin/python -c "import pandas, openpyxl, google.auth, googleapiclient; print('OK - todas las dependencias están instaladas')"
```

Resultado esperado:

```text
OK - todas las dependencias están instaladas
```

---

# 4. `auto_scanner_2026.py`

Escanea los datos AMISR-14 y genera:

```text
REPORTE_AUTOMATIZADO_2026.csv
```

Directorio predeterminado:

```text
/mnt/data_amisr/
```

Ejecutar:

```bash
/home/soporte/anaconda3/bin/python auto_scanner_2026.py
```

También permite indicar otro directorio:

```bash
/home/soporte/anaconda3/bin/python auto_scanner_2026.py /media/soporte/Expansion/AMISR/2026
```

Tipos reconocidos:

```text
ISR
ESF
LPD
MET
```

El scanner protege la información histórica: si encuentra menos datos en disco que los registrados previamente en el CSV, no reduce los valores existentes.

---

# 5. `auto_reporte_2026.py`

Lee:

```text
REPORTE_AUTOMATIZADO_2026.csv
```

y genera:

```text
REPORTE_DIGDT_2026.csv
```

Agrupa por:

```text
MES + TIPO
```

y suma:

```text
GB
HORAS
```

Ejecutar:

```bash
/home/soporte/anaconda3/bin/python auto_reporte_2026.py
```

El resultado tiene la estructura:

```csv
MES,TIPO,GB,HORAS
AGOSTO,ISR,...
AGOSTO,ESF,...
SEPTIEMBRE,ISR,...
SEPTIEMBRE,ESF,...
```

---

# 6. `auto_send_2026.py`

Este script publica/actualiza los archivos CSV generados por el proceso en el repositorio de GitHub.

Archivos principales:

```text
REPORTE_AUTOMATIZADO_2026.csv
REPORTE_DIGDT_2026.csv
```

Flujo:

```text
auto_scanner_2026.py
        │
        ▼
REPORTE_AUTOMATIZADO_2026.csv
        │
        ▼
auto_reporte_2026.py
        │
        ▼
REPORTE_DIGDT_2026.csv
        │
        ▼
auto_send_2026.py
        │
        ▼
GitHub
```

Ejecutar:

```bash
cd /home/soporte/AUTO_REPORTS_AMISR_14
/home/soporte/anaconda3/bin/python auto_send_2026.py
```

No almacenar tokens de GitHub directamente en el código fuente ni subirlos al repositorio.

---

# 7. `actualiza_google_drive_final.py`

Este script toma el archivo:

```text
REPORTE_DIGDT_2026.csv
```

publicado en GitHub y utiliza sus valores para actualizar el archivo:

```text
DONE_POI 2026 ROJ.xlsx
```

almacenado en Google Drive.

Archivo:

```text
DONE_POI 2026 ROJ.xlsx
```

ID:

```text
1NQfdeLyCrD97uTQYo3BttK26JYXuaRzi
```

Fuente CSV:

```text
https://raw.githubusercontent.com/sebastianVP/DATASETS_CLASE/refs/heads/main/REPORTE_DIGDT_2026.csv
```

Ejecutar:

```bash
cd /home/soporte/AUTO_REPORTS_AMISR_14
/home/soporte/anaconda3/bin/python actualiza_google_drive_final.py
```

---

# 8. Paso a paso: cómo se generan los valores

El proceso de actualización del Excel sigue esta secuencia:

```text
1. Datos AMISR-14
        │
        ▼
2. Scanner
        │
        ▼
3. HORAS por FECHA y TIPO
        │
        ▼
4. Resumen mensual
        │
        ▼
5. REPORTE_DIGDT_2026.csv
        │
        ▼
6. Publicación en GitHub
        │
        ▼
7. Lectura del CSV desde GitHub
        │
        ▼
8. Separación MES + TIPO
        │
        ▼
9. Obtención de ISR y ESF
        │
        ▼
10. Actualización de celdas del Excel
        │
        ▼
11. Guardado del XLSX
        │
        ▼
12. Subida a Google Drive
```

---

# 9. Paso 1 — Datos de AMISR-14

El scanner analiza los directorios de datos:

```text
/mnt/data_amisr/
```

Por ejemplo:

```text
20260929.001
20260929.002
20260930.001
```

Dentro de cada adquisición se identifican los experimentos mediante los archivos `.exp`.

Los principales tipos utilizados para este reporte son:

```text
ISR
ESF
```

---

# 10. Paso 2 — Generación de `REPORTE_AUTOMATIZADO_2026.csv`

El scanner genera registros con:

```text
FECHA
TIPO
SIZE (GB)
HORAS
```

Ejemplo conceptual:

```csv
FECHA,TIPO,SIZE (GB),HORAS
20260801,ISR,120.50,22.46
20260801,ESF,85.30,31.68
20260802,ISR,115.20,21.50
```

Estos datos representan la operación detectada para cada fecha y tipo de experimento.

---

# 11. Paso 3 — Generación de `REPORTE_DIGDT_2026.csv`

`auto_reporte_2026.py` agrupa los registros por:

```text
MES + TIPO
```

Por ejemplo:

```text
AGOSTO + ISR
AGOSTO + ESF
SEPTIEMBRE + ISR
SEPTIEMBRE + ESF
```

Luego suma las horas de todos los registros correspondientes.

Resultado:

```csv
MES,TIPO,GB,HORAS
AGOSTO,ISR,XXXX,XX.XX
AGOSTO,ESF,XXXX,XX.XX
SEPTIEMBRE,ISR,XXXX,XX.XX
SEPTIEMBRE,ESF,XXXX,XX.XX
```

---

# 12. Paso 4 — Publicación en GitHub

`auto_send_2026.py` publica los archivos actualizados:

```text
REPORTE_AUTOMATIZADO_2026.csv
REPORTE_DIGDT_2026.csv
```

El archivo utilizado posteriormente por Google Drive es:

```text
REPORTE_DIGDT_2026.csv
```

Fuente:

```text
GitHub
```

Esto permite que el script de actualización de Google Drive siempre consuma el reporte publicado más recientemente.

---

# 13. Paso 5 — Lectura del CSV desde GitHub

`actualiza_google_drive_final.py` descarga:

```text
REPORTE_DIGDT_2026.csv
```

y normaliza los campos:

```python
df["MES"] = df["MES"].astype(str).str.strip().str.upper()
df["TIPO"] = df["TIPO"].astype(str).str.strip().str.upper()
df["HORAS"] = pd.to_numeric(df["HORAS"], errors="coerce").fillna(0)
```

Esto garantiza que:

```text
agosto
Agosto
AGOSTO
```

sean tratados como:

```text
AGOSTO
```

---

# 14. Paso 6 — Obtención de horas

Para cada combinación:

```text
MES + TIPO
```

se obtiene la suma de horas.

La función utilizada conceptualmente es:

```python
obtener_horas(df, mes, tipo)
```

Ejemplo:

```text
obtener_horas(df, "AGOSTO", "ISR")
```

devuelve:

```text
AGOSTO_ISR
```

Y:

```text
obtener_horas(df, "AGOSTO", "ESF")
```

devuelve:

```text
AGOSTO_ESF
```

---

# 15. Paso 7 — Generación dinámica de `horas`

El script no define cada mes manualmente.

Utiliza:

```python
MESES_COLUMNAS = {
    "AGOSTO": "J",
    "SEPTIEMBRE": "K",
    "OCTUBRE": "L",
    "NOVIEMBRE": "M",
    "DICIEMBRE": "N"
}
```

y genera automáticamente:

```python
horas = {
    f"{mes}_{tipo}": obtener_horas(df, mes, tipo)
    for mes in MESES_COLUMNAS
    for tipo in ["ISR", "ESF"]
}
```

Se generan:

```text
AGOSTO_ISR
AGOSTO_ESF

SEPTIEMBRE_ISR
SEPTIEMBRE_ESF

OCTUBRE_ISR
OCTUBRE_ESF

NOVIEMBRE_ISR
NOVIEMBRE_ESF

DICIEMBRE_ISR
DICIEMBRE_ESF
```

---

# 16. Paso 8 — Actualización de la hoja DCG

La hoja:

```text
Datos geofísicos válidos - DCG
```

recibe directamente las horas de ISR y ESF.

## ISR — fila 14

```text
AGOSTO      → J14
SEPTIEMBRE  → K14
OCTUBRE     → L14
NOVIEMBRE   → M14
DICIEMBRE   → N14
```

Equivalente:

```text
J14 = AGOSTO_ISR
K14 = SEPTIEMBRE_ISR
L14 = OCTUBRE_ISR
M14 = NOVIEMBRE_ISR
N14 = DICIEMBRE_ISR
```

## ESF — fila 15

```text
AGOSTO      → J15
SEPTIEMBRE  → K15
OCTUBRE     → L15
NOVIEMBRE   → M15
DICIEMBRE   → N15
```

Equivalente:

```text
J15 = AGOSTO_ESF
K15 = SEPTIEMBRE_ESF
L15 = OCTUBRE_ESF
M15 = NOVIEMBRE_ESF
N15 = DICIEMBRE_ESF
```

---

# 17. Paso 9 — Actualización de la hoja DIGDT

La hoja:

```text
Instrumentación Ionosférica
```

recibe el total mensual de operación.

El total se calcula:

```text
TOTAL = ISR + ESF
```

## Fila 13

```text
J13 = AGOSTO_ISR + AGOSTO_ESF
K13 = SEPTIEMBRE_ISR + SEPTIEMBRE_ESF
L13 = OCTUBRE_ISR + OCTUBRE_ESF
M13 = NOVIEMBRE_ISR + NOVIEMBRE_ESF
N13 = DICIEMBRE_ISR + DICIEMBRE_ESF
```

Ejemplo:

```text
AGOSTO_ISR = 100.50
AGOSTO_ESF = 200.25

J13 = 300.75
```

El resultado se redondea a dos decimales.

---

# 18. Resumen de celdas actualizadas

## `Datos geofísicos válidos - DCG`

| Celda | Valor          |
| ----- | -------------- |
| `J14` | AGOSTO_ISR     |
| `K14` | SEPTIEMBRE_ISR |
| `L14` | OCTUBRE_ISR    |
| `M14` | NOVIEMBRE_ISR  |
| `N14` | DICIEMBRE_ISR  |
| `J15` | AGOSTO_ESF     |
| `K15` | SEPTIEMBRE_ESF |
| `L15` | OCTUBRE_ESF    |
| `M15` | NOVIEMBRE_ESF  |
| `N15` | DICIEMBRE_ESF  |

## `Instrumentación Ionosférica`

| Celda | Fórmula                         |
| ----- | ------------------------------- |
| `J13` | AGOSTO_ISR + AGOSTO_ESF         |
| `K13` | SEPTIEMBRE_ISR + SEPTIEMBRE_ESF |
| `L13` | OCTUBRE_ISR + OCTUBRE_ESF       |
| `M13` | NOVIEMBRE_ISR + NOVIEMBRE_ESF   |
| `N13` | DICIEMBRE_ISR + DICIEMBRE_ESF   |

---

# 19. Actualización dinámica

Para agregar un nuevo mes, solamente se modifica:

```python
MESES_COLUMNAS = {
    "AGOSTO": "J",
    "SEPTIEMBRE": "K",
    "OCTUBRE": "L",
    "NOVIEMBRE": "M",
    "DICIEMBRE": "N",
    "ENERO": "O"
}
```

Automáticamente se generarían:

```text
ENERO_ISR
ENERO_ESF
```

y se actualizarían:

```text
O14
O15
O13
```

No es necesario modificar los bucles de actualización.

---

# 20. Cron

## Envío a GitHub

Si `auto_send_2026.py` se automatiza a las 15:00:

```cron
# Envío automático de reportes AMISR-14 a GitHub
0 15 * * * cd /home/soporte/AUTO_REPORTS_AMISR_14 && /home/soporte/anaconda3/bin/python auto_send_2026.py >> /home/soporte/AUTO_REPORTS_AMISR_14/cron_github.log 2>&1
```

## Actualización de Google Drive

A las 16:00:

```cron
# Actualización automática reporte AMISR-14 - Google Drive
0 16 * * * cd /home/soporte/AUTO_REPORTS_AMISR_14 && /home/soporte/anaconda3/bin/python actualiza_google_drive_final.py >> /home/soporte/AUTO_REPORTS_AMISR_14/cron_google_drive.log 2>&1
```

Esto permite que:

```text
15:00 → Generar/publicar CSV en GitHub
16:00 → Leer CSV desde GitHub y actualizar Excel
```

---

# 21. Logs

GitHub:

```text
/home/soporte/AUTO_REPORTS_AMISR_14/cron_github.log
```

Google Drive:

```text
/home/soporte/AUTO_REPORTS_AMISR_14/cron_google_drive.log
```

Consultar:

```bash
tail -n 50 /home/soporte/AUTO_REPORTS_AMISR_14/cron_github.log
```

```bash
tail -n 50 /home/soporte/AUTO_REPORTS_AMISR_14/cron_google_drive.log
```

---

# 22. Credenciales

Google:

```text
/home/soporte/.google/amisr-service-account.json
```

Permisos:

```bash
chmod 600 /home/soporte/.google/amisr-service-account.json
```

Las credenciales no deben estar dentro de Git.

El `.gitignore` debe contener:

```gitignore
credentials.json
__pycache__/
*.py[cod]
*.log
```

---

# 23. Prueba manual completa

```bash
cd /home/soporte/AUTO_REPORTS_AMISR_14
```

### 1. Escanear AMISR

```bash
/home/soporte/anaconda3/bin/python auto_scanner_2026.py
```

### 2. Generar resumen mensual

```bash
/home/soporte/anaconda3/bin/python auto_reporte_2026.py
```

### 3. Publicar en GitHub

```bash
/home/soporte/anaconda3/bin/python auto_send_2026.py
```

### 4. Actualizar Google Drive

```bash
/home/soporte/anaconda3/bin/python actualiza_google_drive_final.py
```

### 5. Verificar Cron

```bash
crontab -l
```

---

# 24. Resultado final

El proceso completo permite automatizar:

```text
AMISR-14
   │
   ▼
Scanner de datos
   │
   ▼
Reporte diario/acumulativo
   │
   ▼
Resumen mensual
   │
   ▼
Publicación GitHub
   │
   ▼
Lectura del CSV
   │
   ▼
Cálculo ISR + ESF
   │
   ▼
Actualización DCG
   │
   ├── J14:N14 → ISR
   ├── J15:N15 → ESF
   │
   ▼
Actualización DIGDT
   │
   └── J13:N13 → ISR + ESF
   │
   ▼
DONE_POI 2026 ROJ.xlsx
```

Las celdas no contempladas en este proceso permanecen sin modificación intencional.

---

# 25. Autor

**Alexander Valdez**
Especialista de Radar – Ingeniero Electrónico
Radio Observatorio de Jicamarca (ROJ)
Instituto Geofísico del Perú (IGP)

**Proyecto:** Automatización de reportes AMISR-14
