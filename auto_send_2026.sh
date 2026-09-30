#!/bin/bash

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Directorio donde se encuentran los archivos originales
ORIGEN="/home/soporte/Documents"

# Directorio del repositorio Git
REPO_DIR="/home/soporte/Documents/DATASETS_CLASE"

# Archivos que se copiarán
ARCHIVO_1="REPORTE_AUTOMATIZADO_2026.csv"
ARCHIVO_2="REPORTE_DIGDT_2026.csv"

# Mensaje del commit
COMMIT_MSG="Actualizacion de reportes 2026"

# Archivo de log
LOG_FILE="$REPO_DIR/subida_2026.log"


# ============================================================
# FUNCIÓN PARA REGISTRAR LOG
# ============================================================

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}


# ============================================================
# INICIO
# ============================================================

log "============================================================"
log "INICIO DE ENVIO DE REPORTES 2026"
log "============================================================"

log "Origen: $ORIGEN"
log "Repositorio: $REPO_DIR"


# ============================================================
# VERIFICAR REPOSITORIO
# ============================================================

if [ ! -d "$REPO_DIR" ]; then
    log "ERROR: No existe el directorio del repositorio."
    exit 1
fi

if [ ! -d "$REPO_DIR/.git" ]; then
    log "ERROR: El directorio no es un repositorio Git."
    exit 1
fi


# ============================================================
# VERIFICAR ARCHIVOS DE ORIGEN
# ============================================================

log "Verificando archivos de origen..."

if [ ! -f "$ORIGEN/$ARCHIVO_1" ]; then
    log "ERROR: No se encontró $ORIGEN/$ARCHIVO_1"
    exit 1
fi

if [ ! -f "$ORIGEN/$ARCHIVO_2" ]; then
    log "ERROR: No se encontró $ORIGEN/$ARCHIVO_2"
    exit 1
fi

log "OK: Ambos archivos existen."


# ============================================================
# COPIAR ARCHIVOS AL REPOSITORIO
# ============================================================

log "Copiando archivos al repositorio..."

if cp "$ORIGEN/$ARCHIVO_1" "$REPO_DIR/" &&
   cp "$ORIGEN/$ARCHIVO_2" "$REPO_DIR/"; then

    log "OK: Archivos copiados correctamente."

else

    log "ERROR: No se pudieron copiar los archivos."
    exit 1

fi


# ============================================================
# VERIFICAR ARCHIVOS COPIADOS
# ============================================================

if [ ! -f "$REPO_DIR/$ARCHIVO_1" ]; then
    log "ERROR: $ARCHIVO_1 no fue copiado correctamente."
    exit 1
fi

if [ ! -f "$REPO_DIR/$ARCHIVO_2" ]; then
    log "ERROR: $ARCHIVO_2 no fue copiado correctamente."
    exit 1
fi

log "OK: Archivos verificados en el repositorio."


# ============================================================
# ENTRAR AL REPOSITORIO
# ============================================================

cd "$REPO_DIR" || {
    log "ERROR: No se pudo acceder al repositorio."
    exit 1
}


# ============================================================
# MOSTRAR ESTADO DE GIT
# ============================================================

log "Estado actual del repositorio:"

git status --short | tee -a "$LOG_FILE"


# ============================================================
# AGREGAR SOLO LOS DOS ARCHIVOS
# ============================================================

log "Agregando archivos al repositorio..."

if git add "$ARCHIVO_1" "$ARCHIVO_2"; then

    log "OK: Archivos agregados a Git."

else

    log "ERROR: No se pudieron agregar los archivos."
    exit 1

fi


# ============================================================
# VERIFICAR SI HAY CAMBIOS
# ============================================================

if git diff --cached --quiet; then

    log "No existen cambios nuevos para subir."
    log "Los archivos ya están actualizados en GitHub."

    exit 0

fi


# ============================================================
# COMMIT
# ============================================================

log "Creando commit..."

if git commit -m "$COMMIT_MSG"; then

    log "OK: Commit creado correctamente."

else

    log "ERROR: No se pudo crear el commit."
    exit 1

fi


# ============================================================
# PUSH
# ============================================================

log "Enviando archivos a GitHub..."

if git push; then

    log "OK: Archivos enviados correctamente a GitHub."

else

    log "ERROR: No se pudieron enviar los archivos a GitHub."
    exit 1

fi


# ============================================================
# FINAL
# ============================================================

log "============================================================"
log "ENVIO COMPLETADO CORRECTAMENTE"
log "============================================================"

