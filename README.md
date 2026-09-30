# AUTO REPORTS AMISR-14

Automatización para actualizar reportes de operación del radar AMISR-14 a partir del archivo `REPORTE_DIGDT_2026.csv` publicado en GitHub.

El proyecto contempla dos mecanismos:

1. `actualizar_google_sheets.py`: actualiza celdas específicas de un documento nativo de Google Sheets mediante `gspread`.
2. `actualizar_google_drive.py`: descarga un archivo `.xlsx` desde Google Drive, modifica únicamente las celdas necesarias con `openpyxl` y vuelve a subir el mismo archivo `.xlsx` a Drive.

---

## 1. Estructura recomendada del proyecto

```text
AUTO_REPORTS_AMISR_14/
├── actualizar_google_sheets.py
├── actualizar_google_drive.py
├── README.md
├── .gitignore
└── requirements.txt
```

Las credenciales deben estar **fuera del repositorio**:

```text
/home/soporte/.google/
└── amisr-service-account.json
```

No se recomienda guardar `credentials.json` dentro de `AUTO_REPORTS_AMISR_14`.

---

# 2. ¿Cómo evitar subir `credentials.json` a GitHub?

La mejor práctica es combinar dos medidas:

1. Guardar las credenciales fuera del repositorio.
2. Añadirlas al `.gitignore` como protección adicional.

Crear el archivo:

```bash
cd /home/soporte/AUTO_REPORTS_AMISR_14
nano .gitignore
```

Contenido recomendado:

```gitignore
# Credenciales Google
credentials.json
*.json

# Python
__pycache__/
*.py[cod]
*.so

# Entornos virtuales
venv/
.venv/
env/

# Logs
*.log

# Archivos temporales
*.tmp
*.bak
~$

# Archivos Excel locales
*.xlsx
```

### Nota sobre `*.json`

Si el repositorio necesita almacenar otros archivos JSON que no sean secretos, es preferible no bloquear todos los JSON. En ese caso utilizar solamente:

```gitignore
credentials.json
```

o el nombre específico:

```gitignore
amisr-service-account.json
```

---

# 3. Si `credentials.json` ya fue agregado a Git

Agregar el archivo a `.gitignore` no elimina un archivo que Git ya está siguiendo.

Si todavía no se hizo un commit, puede retirarse del seguimiento con:

```bash
git rm --cached credentials.json
```

Después:

```bash
git add .gitignore
git commit -m "Protege credenciales de Google"
```

## Si la credencial ya fue subida a GitHub

Si el JSON con la clave privada ya llegó al repositorio remoto, se debe considerar la credencial comprometida.

El procedimiento recomendado es:

1. Revocar/eliminar la clave de la cuenta de servicio desde Google Cloud.
2. Generar una nueva clave JSON.
3. Guardar la nueva clave fuera del repositorio.
4. Eliminar la credencial expuesta del historial si corresponde.
5. Verificar nuevamente el repositorio antes de publicarlo.

No es suficiente con borrar `credentials.json` del último commit si la clave continúa en el historial de Git.

---

# 4. Ubicación recomendada de las credenciales

En el servidor `IGP-168` se recomienda:

```bash
mkdir -p /home/soporte/.google
```

Guardar allí el archivo JSON, por ejemplo:

```text
/home/soporte/.google/amisr-service-account.json
```

Protegerlo:

```bash
chmod 600 /home/soporte/.google/amisr-service-account.json
```

La estructura queda:

```text
/home/soporte/
├── AUTO_REPORTS_AMISR_14/
│   ├── actualizar_google_sheets.py
│   ├── actualizar_google_drive.py
│   ├── README.md
│   ├── .gitignore
│   └── requirements.txt
│
└── .google/
    └── amisr-service-account.json
```

De esta manera, el repositorio contiene el código, pero no contiene la clave privada.

---

# 5. Configuración de las credenciales

Los scripts pueden utilizar una ruta absoluta:

```python
CREDENTIALS = "/home/soporte/.google/amisr-service-account.json"
```

Otra opción es utilizar una variable de entorno:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/soporte/.google/amisr-service-account.json"
```

Y en Python:

```python
import os

CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
```

Para una automatización mediante `cron`, es recomendable utilizar rutas absolutas y no depender del directorio de trabajo actual.

---

# 6. Dependencias

Instalar las librerías necesarias:

```bash
pip install pandas openpyxl gspread google-auth google-api-python-client
```

También se puede crear `requirements.txt`:

```text
pandas
openpyxl
gspread
google-auth
google-api-python-client
```

Instalar todo con:

```bash
pip install -r requirements.txt
```

---

# 7. Fuente de datos

Los scripts utilizan el siguiente CSV publicado en GitHub:

```text
https://raw.githubusercontent.com/sebastianVP/DATASETS_CLASE/refs/heads/main/REPORTE_DIGDT_2026.csv
```

El reporte contiene, entre otras, las columnas:

```text
MES,TIPO,GB,HORAS
```

El script normaliza `MES` y `TIPO`, convierte `HORAS` a numérico y obtiene las horas mediante filtros por mes y tipo de experimento.

---

# 8. Datos utilizados para la actualización

Actualmente se calculan:

```text
AGOSTO_ISR
AGOSTO_ESF
SEPTIEMBRE_ISR
SEPTIEMBRE_ESF
OCTUBRE_ISR
```

Por ejemplo:

```text
AGOSTO_ISR       : 142.40 horas
AGOSTO_ESF       : 216.12 horas
SEPTIEMBRE_ISR   : 160.26 horas
SEPTIEMBRE_ESF   : 218.42 horas
OCTUBRE_ISR      : 0.00 horas
```

Los valores no deben escribirse manualmente: se obtienen automáticamente del CSV de GitHub.

---

# 9. `actualizar_google_sheets.py`

Este script está diseñado para trabajar con un documento **nativo de Google Sheets**.

Utiliza principalmente:

```text
gspread
google-auth
Google Sheets API
```

## Flujo

```text
GitHub
   │
   ▼
REPORTE_DIGDT_2026.csv
   │
   ▼
pandas
   │
   ▼
cálculo de horas
   │
   ▼
Google Sheets API / gspread
   │
   ▼
actualización de celdas
```

## Hoja `Datos geofísicos válidos - DCG`

| Celda | Valor |
|---|---|
| `J14` | AGOSTO ISR |
| `K14` | SEPTIEMBRE ISR |
| `L14` | OCTUBRE ISR |
| `J15` | AGOSTO ESF |
| `K15` | SEPTIEMBRE ESF |

## Hoja de Instrumentación Ionosférica

| Celda | Valor |
|---|---|
| `J13` | AGOSTO ISR + ESF |
| `K13` | SEPTIEMBRE ISR + ESF |

`L15` no se modifica porque OCTUBRE ESF no fue definido como una celda de actualización.

## Configuración

El script debe tener configurados:

```python
URL_CSV = "https://raw.githubusercontent.com/sebastianVP/DATASETS_CLASE/refs/heads/main/REPORTE_DIGDT_2026.csv"
CREDENTIALS = "/home/soporte/.google/amisr-service-account.json"
SPREADSHEET_ID = "ID_DEL_GOOGLE_SHEET"
```

La cuenta de servicio debe tener permiso de edición sobre el documento.

## Importante

`gspread` requiere un documento nativo de Google Sheets. Si el archivo es un `.xlsx` almacenado en Drive, se debe utilizar `actualizar_google_drive.py` en lugar de este script.

## Ejecución

```bash
cd /home/soporte/AUTO_REPORTS_AMISR_14
python actualizar_google_sheets.py
```

---

# 10. `actualizar_google_drive.py`

Este es el script utilizado actualmente para modificar el archivo Excel almacenado en Google Drive:

```text
DONE_POI 2026 ROJ.xlsx
```

No convierte el archivo a Google Sheets.

Utiliza:

```text
Google Drive API
openpyxl
pandas
```

## Flujo

```text
GitHub
   │
   ▼
REPORTE_DIGDT_2026.csv
   │
   ▼
pandas
   │
   ▼
cálculo de horas
   │
   ▼
Google Drive API
   │
   ▼
descarga del XLSX
   │
   ▼
openpyxl
   │
   ▼
modificación de celdas
   │
   ▼
subida del mismo XLSX
```

---

# 11. Google Drive API

Para este script es necesario habilitar **Google Drive API** en el mismo proyecto de Google Cloud utilizado para la cuenta de servicio.

También se debe compartir el archivo Excel con el correo de la cuenta de servicio.

Ejemplo:

```text
xxxx@proyecto.iam.gserviceaccount.com
```

Permiso recomendado:

```text
Editor
```

No es necesario hacer público el archivo.

---

# 12. Configuración de `actualizar_google_drive.py`

La configuración principal es:

```python
URL_CSV = "https://raw.githubusercontent.com/sebastianVP/DATASETS_CLASE/refs/heads/main/REPORTE_DIGDT_2026.csv"

CREDENTIALS = "/home/soporte/.google/amisr-service-account.json"

FILE_ID = "1NQfdeLyCrD97uTQYo3BttK26JYXuaRzi"
```

El `FILE_ID` identifica actualmente:

```text
DONE_POI 2026 ROJ.xlsx
```

No debe confundirse con el ID de otro archivo o de un Google Sheet diferente.

---

# 13. Obtención del `FILE_ID`

Si el enlace tiene una estructura como:

```text
https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view
```

el ID es:

```text
1AbCdEfGhIjKlMnOpQrStUvWxYz
```

Ese valor se coloca en:

```python
FILE_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz"
```

---

# 14. Hojas del archivo Excel

El archivo actual contiene, entre otras, hojas como:

```text
Operatividad
Instrumentación Ionosférica ...
Datos geofísicos válidos - DCG
Hoja 3
ISR+JULIA
OTROS RADARES
RADARES HF
```

El script utiliza una búsqueda flexible para encontrar las hojas, especialmente la hoja de Instrumentación Ionosférica, evitando depender de que el nombre completo coincida exactamente.

---

# 15. Celdas modificadas en el Excel

## `Datos geofísicos válidos - DCG`

```text
J14 → AGOSTO ISR
K14 → SEPTIEMBRE ISR
L14 → OCTUBRE ISR

J15 → AGOSTO ESF
K15 → SEPTIEMBRE ESF
```

## Hoja de Instrumentación Ionosférica

```text
J13 → AGOSTO ISR + AGOSTO ESF
K13 → SEPTIEMBRE ISR + SEPTIEMBRE ESF
```

El script **no reemplaza las hojas completas**. Descarga el Excel, modifica únicamente esas celdas y vuelve a subir el mismo archivo.

---

# 16. Ejecución de `actualizar_google_drive.py`

Desde:

```bash
cd /home/soporte/AUTO_REPORTS_AMISR_14
```

ejecutar:

```bash
python actualizar_google_drive.py
```

Una ejecución correcta debe mostrar una secuencia similar a:

```text
======================================================================
 ACTUALIZACIÓN REPORTE AMISR-14 - GOOGLE DRIVE
======================================================================

📥 Leyendo reporte desde GitHub...

📊 DATOS OBTENIDOS
   AGOSTO_ISR          : ...
   AGOSTO_ESF          : ...
   SEPTIEMBRE_ISR      : ...
   SEPTIEMBRE_ESF      : ...
   OCTUBRE_ISR         : ...

☁️ Conectando con Google Drive...
📄 Archivo: DONE_POI 2026 ROJ.xlsx

📥 Descargando archivo XLSX...

📝 Modificando celdas...

📤 Subiendo archivo actualizado a Google Drive...

======================================================================
 ✅ ARCHIVO ACTUALIZADO CORRECTAMENTE
======================================================================
```

---

# 17. Qué ocurre durante la actualización

El script realiza estas operaciones:

1. Descarga `REPORTE_DIGDT_2026.csv` desde GitHub.
2. Procesa los datos con `pandas`.
3. Calcula las horas ISR y ESF requeridas.
4. Se autentica en Google Drive mediante la cuenta de servicio.
5. Busca el archivo mediante `FILE_ID`.
6. Descarga temporalmente el `.xlsx`.
7. Abre el Excel con `openpyxl`.
8. Busca las hojas requeridas.
9. Modifica las celdas definidas.
10. Guarda el Excel en memoria.
11. Reemplaza el contenido del mismo archivo en Google Drive.

El archivo continúa siendo:

```text
DONE_POI 2026 ROJ.xlsx
```

---

# 18. Recomendación de respaldo

Antes de la primera ejecución sobre el archivo oficial, es recomendable crear una copia de seguridad del `.xlsx` en Google Drive.

Esto permite recuperar el archivo si posteriormente se realizan cambios adicionales en la estructura del Excel.

---

# 19. Crear el repositorio Git

Desde el servidor:

```bash
cd /home/soporte/AUTO_REPORTS_AMISR_14
git init
```

Verificar:

```bash
git status
```

Agregar los archivos del proyecto:

```bash
git add actualizar_google_sheets.py

git add actualizar_google_drive.py

git add README.md

git add .gitignore

git add requirements.txt
```

Crear el primer commit:

```bash
git commit -m "Agrega automatizacion de reportes AMISR-14"
```

---

# 20. Verificar que las credenciales NO estén en Git

Antes de hacer `push`, ejecutar:

```bash
git status
```

y:

```bash
git ls-files
```

Debe aparecer algo parecido a:

```text
.gitignore
README.md
actualizar_google_drive.py
actualizar_google_sheets.py
requirements.txt
```

No debe aparecer:

```text
credentials.json
amisr-service-account.json
```

También se puede revisar el contenido del proyecto:

```bash
grep -R "private_key" . --exclude-dir=.git
```

Si aparece una clave privada real, detener el proceso y retirarla antes de publicar el repositorio.

---

# 21. Crear repositorio remoto en GitHub

Después de crear el repositorio vacío en GitHub, configurar el remoto:

```bash
git remote add origin https://github.com/USUARIO/AUTO_REPORTS_AMISR_14.git
```

Verificar:

```bash
git remote -v
```

Renombrar la rama principal, si corresponde:

```bash
git branch -M main
```

Finalmente:

```bash
git push -u origin main
```

El repositorio contendrá el código y la documentación, pero las credenciales permanecerán fuera del repositorio.

---

# 22. Seguridad para producción

No colocar nunca en el código:

```python
private_key = "..."
```

ni la clave privada completa de la cuenta de servicio.

Tampoco publicar:

```text
credentials.json
*.pem
*.key
```

La separación recomendada es:

```text
GitHub
   │
   ├── código Python
   ├── README.md
   ├── requirements.txt
   └── .gitignore

Servidor
   │
   └── /home/soporte/.google/
       └── amisr-service-account.json
```

---

# 23. Automatización mediante cron

Si posteriormente se desea ejecutar automáticamente el proceso, se puede utilizar `cron`.

Ejemplo para ejecutar diariamente a las 12:00:

```cron
0 12 * * * cd /home/soporte/AUTO_REPORTS_AMISR_14 && /home/soporte/anaconda3/bin/python actualizar_google_drive.py >> /home/soporte/AUTO_REPORTS_AMISR_14/cron_google_drive.log 2>&1
```

Para comprobar el `cron`:

```bash
crontab -l
```

Se recomienda utilizar rutas absolutas porque `cron` puede ejecutarse con un entorno diferente al de una terminal interactiva.

---

# 24. Comparación de los dos scripts

| Característica | `actualizar_google_sheets.py` | `actualizar_google_drive.py` |
|---|---|---|
| Destino | Google Sheets nativo | Excel `.xlsx` en Drive |
| `gspread` | Sí | No |
| Google Sheets API | Sí | No |
| Google Drive API | No | Sí |
| `openpyxl` | No | Sí |
| Conserva formato Excel | No aplica | Sí |
| Convierte XLSX | No | No |
| Modifica celdas específicas | Sí | Sí |

---

# 25. Arquitectura final

```text
                         GITHUB
                            │
                            ▼
                REPORTE_DIGDT_2026.csv
                            │
                            ▼
                         pandas
                            │
                            ▼
                    horas AMISR-14
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
     Google Sheets                    Google Drive
              │                           │
              │                           ▼
              │                    DONE_POI 2026 ROJ.xlsx
              │                           │
              │                           ▼
              │                       openpyxl
              │                           │
              │                           ▼
              │                   modificar 7 celdas
              │                           │
              ▼                           ▼
       Sheet actualizado             XLSX actualizado
```

---

# 26. Resultado

El sistema permite mantener el proceso automatizado de actualización de reportes AMISR-14 sin exponer las credenciales de Google en GitHub.

La información pública del proyecto queda limitada al código y documentación, mientras que la cuenta de servicio permanece protegida en el servidor.

Para el escenario actual, `actualizar_google_drive.py` es el script adecuado cuando el documento oficial continúa siendo:

```text
DONE_POI 2026 ROJ.xlsx
```

y se desea conservarlo como archivo Excel en Google Drive.

---

## Autor

**Alexander Valdez**  
Especialista de Radar – Ingeniero Electrónico  
Radio Observatorio de Jicamarca – IGP
