# -*- coding: utf-8 -*-

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

URL_CSV = "https://raw.githubusercontent.com/sebastianVP/DATASETS_CLASE/refs/heads/main/REPORTE_DIGDT_2026.csv"
CREDENTIALS = "/home/soporte/.google/amisr-service-account.json"
SPREADSHEET_ID = "1wGvIyvX5wDJFviOqoFR7uwliKSrX3vK5uBg3eFJBXDs"

MESES = {
    "AGOSTO": "AGOSTO",
    "SEPTIEMBRE": "SEPTIEMBRE",
    "OCTUBRE": "OCTUBRE"
}

def leer_reporte():
    df = pd.read_csv(URL_CSV)
    df["MES"] = df["MES"].astype(str).str.strip().str.upper()
    df["TIPO"] = df["TIPO"].astype(str).str.strip().str.upper()
    df["HORAS"] = pd.to_numeric(df["HORAS"], errors="coerce").fillna(0)
    return df

def obtener_horas(df, mes, tipo):
    datos = df[(df["MES"] == mes) & (df["TIPO"] == tipo)]
    return round(datos["HORAS"].sum(), 2)

def actualizar():
    df = leer_reporte()

    horas = {
        "AGOSTO_ISR": obtener_horas(df, "AGOSTO", "ISR"),
        "AGOSTO_ESF": obtener_horas(df, "AGOSTO", "ESF"),
        "SEPTIEMBRE_ISR": obtener_horas(df, "SEPTIEMBRE", "ISR"),
        "SEPTIEMBRE_ESF": obtener_horas(df, "SEPTIEMBRE", "ESF"),
        "OCTUBRE_ISR": obtener_horas(df, "OCTUBRE", "ISR"),
    }

    credenciales = Credentials.from_service_account_file(
        CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    cliente = gspread.authorize(credenciales)
    spreadsheet = cliente.open_by_key(SPREADSHEET_ID)

    dcg = spreadsheet.worksheet("Datos geofísicos válidos - DCG")
    digdt = spreadsheet.worksheet("Instrumentación Ionosférica (Geofísica) - DIGDT")

    dcg.update("J14", [[horas["AGOSTO_ISR"]]])
    dcg.update("J15", [[horas["AGOSTO_ESF"]]])

    dcg.update("K14", [[horas["SEPTIEMBRE_ISR"]]])
    dcg.update("K15", [[horas["SEPTIEMBRE_ESF"]]])

    dcg.update("L14", [[horas["OCTUBRE_ISR"]]])

    digdt.update(
        "J13",
        [[horas["AGOSTO_ISR"] + horas["AGOSTO_ESF"]]]
    )

    digdt.update(
        "K13",
        [[horas["SEPTIEMBRE_ISR"] + horas["SEPTIEMBRE_ESF"]]]
    )

    print("\n✅ Google Sheets actualizado correctamente.")
    print("\nDatos utilizados:")

    for clave, valor in horas.items():
        print(f"{clave:<20}: {valor:.2f} horas")


if __name__ == "__main__":
    actualizar()
