import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import json
import os
import time

# Intentar importar librerías de Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Polla Mundialista 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CONSTANTES DE BASE DE DATOS Y EQUIPOS
# ==========================================
SHEET_NAME = "Polla_DB_2026"
DB_DIR = "db_polla"

DB_USERS = "users"
DB_PREDICTIONS = "predictions"
DB_MATCHES = "matches"
DB_SETTINGS = "settings"
DB_SPECIALS = "special_preds"

DEADLINES = {
    "fase_grupos": datetime(2026, 6, 10, 23, 59),
    "eliminatorias": datetime(2026, 6, 27, 23, 59) 
}

FASES_NOMBRES = {
    "fase_grupos": "Fase de Grupos",
    "octavos": "Octavos de Final",
    "cuartos": "Cuartos de Final",
    "semis": "Semifinales",
    "final": "Gran Final"
}

EQUIPOS_MUNDIAL = sorted([
    "Alemania", "Arabia Saudí", "Argelia", "Argentina", "Australia", "Austria",
    "Bélgica", "Bosnia y Herzegovina", "Brasil", "Cabo Verde", "Canadá", "Catar",
    "Colombia", "Costa de Marfil", "Croacia", "Curazao", "Ecuador", "Egipto",
    "Escocia", "España", "Estados Unidos", "Francia", "Ghana", "Haití",
    "Inglaterra", "Irak", "Japón", "Jordania", "Marruecos", "México",
    "Noruega", "Nueva Zelanda", "Países Bajos", "Panamá", "Paraguay", "Portugal",
    "RD Congo", "RI de Irán", "República Checa", "República de Corea", "Senegal",
    "Sudáfrica", "Suecia", "Suiza", "Turquía", "Túnez", "Uruguay", "Uzbekistán"
])

# ==========================================
# ADAPTADOR DE BASE DE DATOS (GSHEETS / LOCAL)
# ==========================================
def is_gsheets_configured():
    return GSPREAD_AVAILABLE and "gcp_service_account" in st.secrets

@st.cache_resource
def get_gspread_client():
    if is_gsheets_configured():
        try:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            return gspread.authorize(credentials)
        except Exception as e:
            st.error(f"Error autenticando con Google: {e}")
            return None
    return None

@st.cache_resource(ttl=3600)
def get_sheet():
    client = get_gspread_client()
    if client:
        try:
            return client.open(SHEET_NAME).sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            st.error(f"⚠️ No se encontró el Google Sheet '{SHEET_NAME}'. Compártelo con el Service Account.")
            return None
        except gspread.exceptions.APIError as e:
            st.error(f"⚠️ La API de Google está saturada en este momento. La app está reintentando la conexión...")
            time.sleep(2)
            return None
    return None

@st.cache_data(ttl=60)
def load_data(key):
    if is_gsheets_configured():
        sheet = get_sheet()
        if sheet:
            try:
                rows = sheet.get_all_values()
                for row in rows:
                    if len(row) >= 2 and row[0] == key:
                        return json.loads(row[1])
                return {} 
            except Exception as e:
                pass
    
    filepath = os.path.join(DB_DIR, f"{key}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_data(data, key):
    if is_gsheets_configured():
        sheet = get_sheet()
        if sheet:
            try:
                rows = sheet.get_all_values()
                row_idx = -1
                for i, row in enumerate(rows):
                    if len(row) > 0 and row[0] == key:
                        row_idx = i + 1 
                        break
                
                json_str = json.dumps(data)
                if row_idx != -1:
                    sheet.update_cell(row_idx, 2, json_str)
                else:
                    sheet.append_row([key, json_str])
                
                load_data.clear() 
                
                if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
                with open(os.path.join(DB_DIR, f"{key}.json"), 'w') as f:
                    json.dump(data, f, indent=4)
                    
                return
            except Exception as e:
                st.error(f"Error guardando en GSheets: {e}")

    if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
    filepath = os.path.join(DB_DIR, f"{key}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    load_data.clear() 

# ==========================================
# INICIALIZACIÓN DE DATOS Y BRACKET
# ==========================================
def get_initial_matches():
    return {
        "fase_grupos": [
            {"id": "G1", "grupo": "Grupo A", "equipo1": "México", "equipo2": "Sudáfrica", "fecha": "2026-06-11 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G2", "grupo": "Grupo A", "equipo1": "República de Corea", "equipo2": "República Checa", "fecha": "2026-06-11 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G3", "grupo": "Grupo B", "equipo1": "Canadá", "equipo2": "Bosnia y Herzegovina", "fecha": "2026-06-12 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G4", "grupo": "Grupo D", "equipo1": "Estados Unidos", "equipo2": "Paraguay", "fecha": "2026-06-12 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G5", "grupo": "Grupo B", "equipo1": "Catar", "equipo2": "Suiza", "fecha": "2026-06-13 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G6", "grupo": "Grupo C", "equipo1": "Brasil", "equipo2": "Marruecos", "fecha": "2026-06-13 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G7", "grupo": "Grupo C", "equipo1": "Haití", "equipo2": "Escocia", "fecha": "2026-06-13 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G8", "grupo": "Grupo D", "equipo1": "Australia", "equipo2": "Turquía", "fecha": "2026-06-14 00:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G9", "grupo": "Grupo E", "equipo1": "Alemania", "equipo2": "Curazao", "fecha": "2026-06-14 13:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G10", "grupo": "Grupo F", "equipo1": "Países Bajos", "equipo2": "Japón", "fecha": "2026-06-14 16:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G11", "grupo": "Grupo E", "equipo1": "Costa de Marfil", "equipo2": "Ecuador", "fecha": "2026-06-14 19:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G12", "grupo": "Grupo F", "equipo1": "Suecia", "equipo2": "Túnez", "fecha": "2026-06-14 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G13", "grupo": "Grupo H", "equipo1": "España", "equipo2": "Cabo Verde", "fecha": "2026-06-15 12:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G14", "grupo": "Grupo G", "equipo1": "Bélgica", "equipo2": "Egipto", "fecha": "2026-06-15 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G15", "grupo": "Grupo H", "equipo1": "Arabia Saudí", "equipo2": "Uruguay", "fecha": "2026-06-15 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G16", "grupo": "Grupo G", "equipo1": "RI de Irán", "equipo2": "Nueva Zelanda", "fecha": "2026-06-15 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G17", "grupo": "Grupo I", "equipo1": "Francia", "equipo2": "Senegal", "fecha": "2026-06-16 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G18", "grupo": "Grupo I", "equipo1": "Irak", "equipo2": "Noruega", "fecha": "2026-06-16 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G19", "grupo": "Grupo J", "equipo1": "Argentina", "equipo2": "Argelia", "fecha": "2026-06-16 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G20", "grupo": "Grupo J", "equipo1": "Austria", "equipo2": "Jordania", "fecha": "2026-06-17 00:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G21", "grupo": "Grupo K", "equipo1": "Portugal", "equipo2": "RD Congo", "fecha": "2026-06-17 13:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G22", "grupo": "Grupo L", "equipo1": "Inglaterra", "equipo2": "Croacia", "fecha": "2026-06-17 16:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G23", "grupo": "Grupo L", "equipo1": "Ghana", "equipo2": "Panamá", "fecha": "2026-06-17 19:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G24", "grupo": "Grupo K", "equipo1": "Uzbekistán", "equipo2": "Colombia", "fecha": "2026-06-17 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G25", "grupo": "Grupo A", "equipo1": "República Checa", "equipo2": "Sudáfrica", "fecha": "2026-06-18 12:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G26", "grupo": "Grupo B", "equipo1": "Suiza", "equipo2": "Bosnia y Herzegovina", "fecha": "2026-06-18 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G27", "grupo": "Grupo B", "equipo1": "Canadá", "equipo2": "Catar", "fecha": "2026-06-18 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G28", "grupo": "Grupo A", "equipo1": "México", "equipo2": "República de Corea", "fecha": "2026-06-18 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G29", "grupo": "Grupo D", "equipo1": "Estados Unidos", "equipo2": "Australia", "fecha": "2026-06-19 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G30", "grupo": "Grupo C", "equipo1": "Escocia", "equipo2": "Marruecos", "fecha": "2026-06-19 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G31", "grupo": "Grupo C", "equipo1": "Brasil", "equipo2": "Haití", "fecha": "2026-06-19 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G32", "grupo": "Grupo D", "equipo1": "Turquía", "equipo2": "Paraguay", "fecha": "2026-06-20 00:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G33", "grupo": "Grupo F", "equipo1": "Países Bajos", "equipo2": "Suecia", "fecha": "2026-06-20 13:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G34", "grupo": "Grupo E", "equipo1": "Alemania", "equipo2": "Costa de Marfil", "fecha": "2026-06-20 16:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G35", "grupo": "Grupo E", "equipo1": "Ecuador", "equipo2": "Curazao", "fecha": "2026-06-20 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G36", "grupo": "Grupo F", "equipo1": "Túnez", "equipo2": "Japón", "fecha": "2026-06-21 00:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G37", "grupo": "Grupo H", "equipo1": "España", "equipo2": "Arabia Saudí", "fecha": "2026-06-21 12:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G38", "grupo": "Grupo G", "equipo1": "Bélgica", "equipo2": "Irán", "fecha": "2026-06-21 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G39", "grupo": "Grupo H", "equipo1": "Uruguay", "equipo2": "Cabo Verde", "fecha": "2026-06-21 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G40", "grupo": "Grupo G", "equipo1": "Nueva Zelanda", "equipo2": "Egipto", "fecha": "2026-06-21 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G41", "grupo": "Grupo J", "equipo1": "Argentina", "equipo2": "Austria", "fecha": "2026-06-22 13:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G42", "grupo": "Grupo I", "equipo1": "Francia", "equipo2": "Irak", "fecha": "2026-06-22 17:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G43", "grupo": "Grupo I", "equipo1": "Noruega", "equipo2": "Senegal", "fecha": "2026-06-22 20:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G44", "grupo": "Grupo J", "equipo1": "Jordania", "equipo2": "Argelia", "fecha": "2026-06-22 23:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G45", "grupo": "Grupo K", "equipo1": "Portugal", "equipo2": "Uzbekistán", "fecha": "2026-06-23 13:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G46", "grupo": "Grupo L", "equipo1": "Inglaterra", "equipo2": "Ghana", "fecha": "2026-06-23 16:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G47", "grupo": "Grupo L", "equipo1": "Panamá", "equipo2": "Croacia", "fecha": "2026-06-23 19:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G48", "grupo": "Grupo K", "equipo1": "Colombia", "equipo2": "RD Congo", "fecha": "2026-06-23 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G49", "grupo": "Grupo B", "equipo1": "Suiza", "equipo2": "Canadá", "fecha": "2026-06-24 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G50", "grupo": "Grupo B", "equipo1": "Bosnia y Herzegovina", "equipo2": "Catar", "fecha": "2026-06-24 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G51", "grupo": "Grupo C", "equipo1": "Escocia", "equipo2": "Brasil", "fecha": "2026-06-24 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G52", "grupo": "Grupo C", "equipo1": "Marruecos", "equipo2": "Haití", "fecha": "2026-06-24 18:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G53", "grupo": "Grupo A", "equipo1": "República Checa", "equipo2": "México", "fecha": "2026-06-24 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G54", "grupo": "Grupo A", "equipo1": "Sudáfrica", "equipo2": "República de Corea", "fecha": "2026-06-24 21:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G55", "grupo": "Grupo E", "equipo1": "Curazao", "equipo2": "Costa de Marfil", "fecha": "2026-06-25 16:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G56", "grupo": "Grupo E", "equipo1": "Ecuador", "equipo2": "Alemania", "fecha": "2026-06-25 16:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G57", "grupo": "Grupo F", "equipo1": "Japón", "equipo2": "Suecia", "fecha": "2026-06-25 19:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G58", "grupo": "Grupo F", "equipo1": "Túnez", "equipo2": "Países Bajos", "fecha": "2026-06-25 19:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G59", "grupo": "Grupo D", "equipo1": "Turquía", "equipo2": "Estados Unidos", "fecha": "2026-06-25 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G60", "grupo": "Grupo D", "equipo1": "Paraguay", "equipo2": "Australia", "fecha": "2026-06-25 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G61", "grupo": "Grupo I", "equipo1": "Noruega", "equipo2": "Francia", "fecha": "2026-06-26 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G62", "grupo": "Grupo I", "equipo1": "Senegal", "equipo2": "Irak", "fecha": "2026-06-26 15:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G63", "grupo": "Grupo H", "equipo1": "Cabo Verde", "equipo2": "Arabia Saudí", "fecha": "2026-06-26 20:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G64", "grupo": "Grupo H", "equipo1": "Uruguay", "equipo2": "España", "fecha": "2026-06-26 20:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G65", "grupo": "Grupo G", "equipo1": "Egipto", "equipo2": "Irán", "fecha": "2026-06-26 23:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G66", "grupo": "Grupo G", "equipo1": "Nueva Zelanda", "equipo2": "Bélgica", "fecha": "2026-06-26 23:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G67", "grupo": "Grupo L", "equipo1": "Panamá", "equipo2": "Inglaterra", "fecha": "2026-06-27 17:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G68", "grupo": "Grupo L", "equipo1": "Croacia", "equipo2": "Ghana", "fecha": "2026-06-27 17:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G69", "grupo": "Grupo K", "equipo1": "Colombia", "equipo2": "Portugal", "fecha": "2026-06-27 19:30", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G70", "grupo": "Grupo K", "equipo1": "RD Congo", "equipo2": "Uzbekistán", "fecha": "2026-06-27 19:30", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G71", "grupo": "Grupo J", "equipo1": "Argelia", "equipo2": "Austria", "fecha": "2026-06-27 22:00", "goles1": None, "goles2": None, "jugado": False},
            {"id": "G72", "grupo": "Grupo J", "equipo1": "Jordania", "equipo2": "Argentina", "fecha": "2026-06-27 22:00", "goles1": None, "goles2": None, "jugado": False}
        ],
        "octavos": [
            {"id": "O1", "grupo": "Octavos 1", "equipo1": "1ro Grupo A", "equipo2": "2do Grupo B", "fecha": "2026-06-28", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "O2", "grupo": "Octavos 2", "equipo1": "1ro Grupo C", "equipo2": "2do Grupo D", "fecha": "2026-06-28", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "O3", "grupo": "Octavos 3", "equipo1": "1ro Grupo E", "equipo2": "2do Grupo F", "fecha": "2026-06-29", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "O4", "grupo": "Octavos 4", "equipo1": "1ro Grupo G", "equipo2": "2do Grupo H", "fecha": "2026-06-29", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "O5", "grupo": "Octavos 5", "equipo1": "1ro Grupo I", "equipo2": "2do Grupo J", "fecha": "2026-06-30", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "O6", "grupo": "Octavos 6", "equipo1": "1ro Grupo K", "equipo2": "2do Grupo L", "fecha": "2026-06-30", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "O7", "grupo": "Octavos 7", "equipo1": "Mejor 3ro (1)", "equipo2": "Mejor 3ro (2)", "fecha": "2026-07-01", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "O8", "grupo": "Octavos 8", "equipo1": "Mejor 3ro (3)", "equipo2": "Mejor 3ro (4)", "fecha": "2026-07-01", "goles1": None, "goles2": None, "jugado": False, "clasifica": None}
        ],
        "cuartos": [
            {"id": "C1", "grupo": "Cuartos 1", "origen1": "O1", "origen2": "O2", "fecha": "2026-07-04", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "C2", "grupo": "Cuartos 2", "origen1": "O3", "origen2": "O4", "fecha": "2026-07-04", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "C3", "grupo": "Cuartos 3", "origen1": "O5", "origen2": "O6", "fecha": "2026-07-05", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "C4", "grupo": "Cuartos 4", "origen1": "O7", "origen2": "O8", "fecha": "2026-07-05", "goles1": None, "goles2": None, "jugado": False, "clasifica": None}
        ],
        "semis": [
            {"id": "S1", "grupo": "Semifinal 1", "origen1": "C1", "origen2": "C2", "fecha": "2026-07-09", "goles1": None, "goles2": None, "jugado": False, "clasifica": None},
            {"id": "S2", "grupo": "Semifinal 2", "origen1": "C3", "origen2": "C4", "fecha": "2026-07-10", "goles1": None, "goles2": None, "jugado": False, "clasifica": None}
        ],
        "final": [
            {"id": "F1", "grupo": "Final", "origen1": "S1", "origen2": "S2", "fecha": "2026-07-19", "goles1": None, "goles2": None, "jugado": False, "clasifica": None}
        ]
    }

def init_db():
    if not load_data(DB_USERS):
        admin_pwd = hash_password("admin123")
        save_data({"admin@polla.com": {"nombre": "Xavier Admin", "pwd": admin_pwd, "grupo": "Admin", "pais": "Ecuador", "rol": "admin"}}, DB_USERS)
    
    if not load_data(DB_PREDICTIONS): save_data({}, DB_PREDICTIONS)
    if not load_data(DB_SPECIALS): save_data({}, DB_SPECIALS)
    
    if not load_data(DB_SETTINGS):
        save_data({
            "fase_actual": "fase_grupos", 
            "campeon_oficial": None, 
            "vice_oficial": None,
            "octavos_oficial": [],
            "cuartos_oficial": [],
            "semis_oficial": []
        }, DB_SETTINGS)
            
    if not load_data(DB_MATCHES):
        save_data(get_initial_matches(), DB_MATCHES)

# ==========================================
# UTILIDADES Y ÁRBOL DINÁMICO
# ==========================================
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(password, hashed_password):
    return hash_password(password) == hashed_password

def determinar_ganador(goles1, goles2):
    if goles1 is None or goles2 is None: return None
    if goles1 > goles2: return "equipo1"
    elif goles2 > goles1: return "equipo2"
    else: return "empate"

def get_match_by_id(matches_dict, m_id):
    for phase, m_list in matches_dict.items():
        for m in m_list:
            if m["id"] == m_id: return m
    return None

# Resuelve el nombre del equipo en base al árbol del USUARIO
def resolve_user_team(m_id, slot, matches_dict, user_preds):
    p = get_match_by_id(matches_dict, m_id)
    if f"origen{slot}" in p:
        origen_id = p[f"origen{slot}"]
        clasifica = user_preds.get(origen_id, {}).get("clasifica")
        if clasifica == "equipo1": return resolve_user_team(origen_id, 1, matches_dict, user_preds)
        elif clasifica == "equipo2": return resolve_user_team(origen_id, 2, matches_dict, user_preds)
        else: return "Por Definir" 
    else:
        base_name = p.get(f"equipo{slot}")
        if m_id.startswith("O"): # Si es octavos, el usuario selecciona el equipo de la lista
            return user_preds.get(m_id, {}).get(f"equipo{slot}", base_name)
        return base_name

# Resuelve el nombre del equipo en base al árbol del ADMIN (La Realidad)
def resolve_admin_team(m_id, slot, matches_dict):
    p = get_match_by_id(matches_dict, m_id)
    if f"origen{slot}" in p:
        origen_id = p[f"origen{slot}"]
        origin_p = get_match_by_id(matches_dict, origen_id)
        clasifica = origin_p.get("clasifica")
        if clasifica == "equipo1": return resolve_admin_team(origen_id, 1, matches_dict)
        elif clasifica == "equipo2": return resolve_admin_team(origen_id, 2, matches_dict)
        else: return "Por Definir"
    else:
        base_name = p.get(f"equipo{slot}")
        if m_id.startswith("O"):
            return p.get(f"equipo{slot}_real", base_name)
        return base_name

def calcular_puntos_partido(pred_goles1, pred_goles2, pred_ganador, real_goles1, real_goles2, real_ganador):
    puntos = 0
    if real_goles1 is None or real_goles2 is None or real_ganador is None:
        return 0

    if pred_ganador == real_ganador: puntos += 1
    if pred_goles1 == real_goles1: puntos += 1
    if pred_goles2 == real_goles2: puntos += 1
    if pred_goles1 == real_goles1 and pred_goles2 == real_goles2 and pred_ganador == real_ganador:
        puntos += 2

    return puntos

# ==========================================
# COMPONENTES DE INTERFAZ (UI)
# ==========================================
def render_login():
    st.title("🏆 Polla Mundialista 2026")
    
    if is_gsheets_configured():
        st.success("✅ Conectado exitosamente a la Base de Datos en la nube (Google Sheets).")
    else:
        st.warning("⚠️ Ejecutando en Modo Local. Configura GSheets para entorno de producción.")
        
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        st.subheader("Acceso a tu cuenta")
        email = st.text_input("Correo electrónico", key="login_email").strip().lower()
        pwd = st.text_input("Contraseña", type="password", key="login_pwd")
        
        if st.button("Entrar", type="primary"):
            users = load_data(DB_USERS)
            if email in users and verify_password(pwd, users[email]["pwd"]):
                st.session_state['user'] = email
                st.session_state['nombre'] = users[email]["nombre"]
                st.session_state['grupo'] = users[email]["grupo"]
                st.session_state['rol'] = users[email].get("rol", "user")
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")

    with tab2:
        st.subheader("Crear nueva cuenta")
        new_name = st.text_input("Nombre completo", key="reg_name")
        new_email = st.text_input("Correo electrónico", key="reg_email").strip().lower()
        new_pwd = st.text_input("Contraseña", type="password", key="reg_pwd")
        new_group = st.selectbox("Selecciona tu Grupo", ["Familia", "Amigos", "Trabajo"])
        new_country = st.selectbox("País de Residencia", ["Ecuador", "Colombia", "España", "EEUU", "Otro"])
        
        if st.button("Registrarme", type="primary"):
            users = load_data(DB_USERS)
            if new_email in users:
                st.error("El correo ya está registrado.")
            elif new_name and new_email and new_pwd:
                users[new_email] = {
                    "nombre": new_name, "pwd": hash_password(new_pwd),
                    "grupo": new_group, "pais": new_country, "rol": "user"
                }
                save_data(users, DB_USERS)
                st.success("¡Registro exitoso! Por favor inicia sesión.")
            else:
                st.warning("Completa todos los campos.")

def render_dashboard_usuario():
    st.sidebar.title(f"Hola, {st.session_state['nombre']}")
    st.sidebar.write(f"**Grupo:** {st.session_state['grupo']}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("Navegación", ["Mis Pronósticos (Partidos)", "Predicciones Especiales (Clasificados)", "Tabla de Posiciones"])

    if menu == "Mis Pronósticos (Partidos)": mostrar_pantalla_pronosticos()
    elif menu == "Predicciones Especiales (Clasificados)": mostrar_predicciones_especiales()
    elif menu == "Tabla de Posiciones": mostrar_tabla_posiciones()

def mostrar_pantalla_pronosticos():
    st.header("Mis Pronósticos (Árbol de Partidos)")
    st.write("Acierta los goles exactos y el ganador para sumar puntos base.")
    
    matches = load_data(DB_MATCHES)
    settings = load_data(DB_SETTINGS)
    predictions = load_data(DB_PREDICTIONS)
    user_email = st.session_state['user']
    
    if user_email not in predictions: predictions[user_email] = {}

    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        fase_por_defecto = settings.get("fase_actual", "fase_grupos")
        idx_fase = list(FASES_NOMBRES.keys()).index(fase_por_defecto) if fase_por_defecto in FASES_NOMBRES else 0
        fase_sel = st.selectbox("Fase del Torneo", list(FASES_NOMBRES.keys()), index=idx_fase, format_func=lambda x: FASES_NOMBRES[x])
    
    with col_filtro2:
        if fase_sel == "fase_grupos":
            lista_grupos = ["Todos"] + [f"Grupo {chr(i)}" for i in range(65, 77)] 
            grupo_filtro = st.selectbox("Sub-filtro: Grupo", lista_grupos)
        else:
            grupo_filtro = "Todos"
            st.selectbox("Sub-filtro: Grupo", ["Único"], disabled=True)

    ahora = datetime.now()
    deadline_key = "fase_grupos" if fase_sel == "fase_grupos" else "eliminatorias"
    deadline = DEADLINES.get(deadline_key, ahora + timedelta(days=1))
    puede_editar = ahora <= deadline
    
    if puede_editar:
        mensaje_cierre = f"Se cierra el: {deadline.strftime('%Y-%m-%d %H:%M')}"
    else:
        mensaje_cierre = f"La fase {FASES_NOMBRES[fase_sel]} está CERRADA para edición."

    st.info(f"Viendo: {FASES_NOMBRES[fase_sel]} | {mensaje_cierre}")

    with st.form("form_pronosticos"):
        st.subheader(f"Partidos")
        
        partidos_fase = matches.get(fase_sel, [])
        if grupo_filtro != "Todos":
            partidos_fase = [p for p in partidos_fase if p.get("grupo") == grupo_filtro]
            
        nuevos_pronosticos = {}
        
        if not partidos_fase: st.write("No hay partidos en este grupo o fase.")
            
        for p in partidos_fase:
            m_id = p["id"]
            st.markdown(f"**{p.get('grupo', '')}** | Fecha: {p['fecha']}")
            
            pred_prev = predictions[user_email].get(m_id, {"goles1": 0, "goles2": 0, "ganador": "empate"})
            
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
            
            # EL USUARIO ELIGE LOS PAISES EN OCTAVOS
            if fase_sel == "octavos":
                base_eq1 = p['equipo1']
                base_eq2 = p['equipo2']
                
                idx1 = EQUIPOS_MUNDIAL.index(pred_prev.get("equipo1")) + 1 if pred_prev.get("equipo1") in EQUIPOS_MUNDIAL else 0
                idx2 = EQUIPOS_MUNDIAL.index(pred_prev.get("equipo2")) + 1 if pred_prev.get("equipo2") in EQUIPOS_MUNDIAL else 0
                
                with col1: eq1_name = st.selectbox(base_eq1, [base_eq1] + EQUIPOS_MUNDIAL, index=idx1, key=f"sel1_{m_id}", disabled=not puede_editar)
                with col5: eq2_name = st.selectbox(base_eq2, [base_eq2] + EQUIPOS_MUNDIAL, index=idx2, key=f"sel2_{m_id}", disabled=not puede_editar)
                
                nuevos_pronosticos[m_id] = {"equipo1": eq1_name, "equipo2": eq2_name}
            else:
                # Las demas fases arrastran el nombre de la fase anterior automaticamente
                eq1_name = resolve_user_team(m_id, 1, matches, predictions[user_email]) if fase_sel != "fase_grupos" else p['equipo1']
                eq2_name = resolve_user_team(m_id, 2, matches, predictions[user_email]) if fase_sel != "fase_grupos" else p['equipo2']
                
                with col1: st.write(f"<h5 style='text-align: right; color:#00ff87;'>{eq1_name}</h5>", unsafe_allow_html=True)
                with col5: st.write(f"<h5 style='color:#00ff87;'>{eq2_name}</h5>", unsafe_allow_html=True)
                nuevos_pronosticos[m_id] = {}

            with col2: g1 = st.number_input("Goles", min_value=0, max_value=15, value=pred_prev.get("goles1", 0), key=f"g1_{m_id}", disabled=not puede_editar, label_visibility="collapsed")
            with col3: st.markdown("<h4 style='text-align: center;'>vs</h4>", unsafe_allow_html=True)
            with col4: g2 = st.number_input("Goles", min_value=0, max_value=15, value=pred_prev.get("goles2", 0), key=f"g2_{m_id}", disabled=not puede_editar, label_visibility="collapsed")
            
            opciones_txt = [f"Gana {eq1_name}", "Empate", f"Gana {eq2_name}"]
            opciones_val = ["equipo1", "empate", "equipo2"]
            
            prev_ganador = pred_prev.get("ganador", determinar_ganador(pred_prev.get("goles1",0), pred_prev.get("goles2",0)))
            idx_ganador = opciones_val.index(prev_ganador) if prev_ganador in opciones_val else 1
            
            ganador_ui = st.radio("Tendencia en 90/120 min:", opciones_txt, index=idx_ganador, key=f"rad_{m_id}", horizontal=True, disabled=not puede_editar)
            ganador_final = opciones_val[opciones_txt.index(ganador_ui)]

            clasifica_final = None
            if fase_sel != "fase_grupos":
                opciones_clasif_txt = ["- Selecciona quién avanza -", eq1_name, eq2_name]
                opciones_clasif_val = [None, "equipo1", "equipo2"]
                
                prev_clasif = pred_prev.get("clasifica")
                idx_clasif = opciones_clasif_val.index(prev_clasif) if prev_clasif in opciones_clasif_val else 0
                
                clasif_ui = st.selectbox("Clasifica a la siguiente ronda:", opciones_clasif_txt, index=idx_clasif, key=f"clasif_{m_id}", disabled=not puede_editar)
                clasifica_final = opciones_clasif_val[opciones_clasif_txt.index(clasif_ui)]

            st.divider()
            nuevos_pronosticos[m_id].update({"goles1": g1, "goles2": g2, "ganador": ganador_final, "clasifica": clasifica_final})

        if puede_editar:
            if st.form_submit_button("Guardar Pronósticos de Partidos", type="primary"):
                predictions[user_email].update(nuevos_pronosticos)
                save_data(predictions, DB_PREDICTIONS)
                st.success("¡Pronósticos guardados correctamente!")
        else:
             st.form_submit_button("Guardar Pronósticos", disabled=True)

def mostrar_predicciones_especiales():
    st.header("Mis Equipos Clasificados (Bonos)")
    st.write("Selecciona explícitamente qué países crees que llegarán a cada fase del torneo. ¡Mientras más lejos lleguen tus elegidos, más puntos ganas!")
    
    ahora = datetime.now()
    puede_editar = ahora <= DEADLINES["eliminatorias"]
    
    if puede_editar:
        st.info(f"Podrás editar estas listas hasta el: {DEADLINES['eliminatorias'].strftime('%Y-%m-%d %H:%M')}")
    else:
        st.warning("Esta sección ya está CERRADA para edición.")
    
    specials = load_data(DB_SPECIALS)
    user_email = st.session_state['user']
    
    if user_email not in specials: 
        specials[user_email] = {"octavos": [], "cuartos": [], "semis": [], "campeon": "", "vicecampeon": ""}
    
    mis_specials = specials[user_email]

    with st.form("form_specials"):
        st.subheader("Clasificados por Etapa")
        
        col1, col2 = st.columns(2)
        with col1:
            octavos_sel = st.multiselect("⚽ Clasificados a OCTAVOS (Máx 16) | +5 pts c/u", EQUIPOS_MUNDIAL, default=mis_specials.get("octavos", []), max_selections=16, disabled=not puede_editar)
            cuartos_sel = st.multiselect("🔥 Clasificados a CUARTOS (Máx 8) | +7 pts c/u", EQUIPOS_MUNDIAL, default=mis_specials.get("cuartos", []), max_selections=8, disabled=not puede_editar)
        with col2:
            semis_sel = st.multiselect("🌟 Clasificados a SEMIS (Máx 4) | +10 pts c/u", EQUIPOS_MUNDIAL, default=mis_specials.get("semis", []), max_selections=4, disabled=not puede_editar)
            
            st.divider()
            
            idx_campeon = EQUIPOS_MUNDIAL.index(mis_specials.get("campeon")) if mis_specials.get("campeon") in EQUIPOS_MUNDIAL else 0
            idx_vice = EQUIPOS_MUNDIAL.index(mis_specials.get("vicecampeon")) if mis_specials.get("vicecampeon") in EQUIPOS_MUNDIAL else 0
            
            campeon_sel = st.selectbox("🏆 CAMPEÓN del Mundo | +20 pts", [""] + EQUIPOS_MUNDIAL, index=idx_campeon+1 if mis_specials.get("campeon") else 0, disabled=not puede_editar)
            vice_sel = st.selectbox("🥈 VICECAMPEÓN | +15 pts", [""] + EQUIPOS_MUNDIAL, index=idx_vice+1 if mis_specials.get("vicecampeon") else 0, disabled=not puede_editar)

        if puede_editar:
            if st.form_submit_button("Guardar Equipos Clasificados", type="primary"):
                specials[user_email] = {
                    "octavos": octavos_sel,
                    "cuartos": cuartos_sel,
                    "semis": semis_sel,
                    "campeon": campeon_sel,
                    "vicecampeon": vice_sel
                }
                save_data(specials, DB_SPECIALS)
                st.success("¡Equipos clasificados guardados con éxito!")
        else:
             st.form_submit_button("Guardar Equipos", disabled=True)

def mostrar_tabla_posiciones():
    st.header("Tabla de Posiciones")
    
    users = load_data(DB_USERS)
    matches = load_data(DB_MATCHES)
    predictions = load_data(DB_PREDICTIONS)
    specials = load_data(DB_SPECIALS)
    settings = load_data(DB_SETTINGS)

    grupo_sel = st.selectbox("Ver tabla de:", ["Mi Grupo (" + st.session_state['grupo'] + ")", "Familia", "Amigos", "Trabajo"])
    grupo_filtro = st.session_state['grupo'] if grupo_sel.startswith("Mi Grupo") else grupo_sel

    tabla_data = []

    oficial_octavos = settings.get("octavos_oficial", [])
    oficial_cuartos = settings.get("cuartos_oficial", [])
    oficial_semis = settings.get("semis_oficial", [])
    oficial_campeon = settings.get("campeon_oficial")
    oficial_vice = settings.get("vice_oficial")

    for email, u_data in users.items():
        if u_data.get("rol") == "admin": continue
        if u_data["grupo"] == grupo_filtro:
            puntos_totales = 0
            user_preds = predictions.get(email, {})
            user_specials = specials.get(email, {})
            
            # 1. Puntos por Partidos
            for fase, partidos in matches.items():
                for p in partidos:
                    if p["jugado"]:
                        m_id = p["id"]
                        if m_id in user_preds:
                            # Verificamos si el usuario le atinó a los equipos exactos del cruce
                            if fase != "fase_grupos":
                                user_eq1 = resolve_user_team(m_id, 1, matches, user_preds)
                                user_eq2 = resolve_user_team(m_id, 2, matches, user_preds)
                                real_eq1 = resolve_admin_team(m_id, 1, matches)
                                real_eq2 = resolve_admin_team(m_id, 2, matches)
                                
                                # Si el usuario no predijo el mismo cruce que ocurrió en la realidad, no gana puntos de goles en este partido.
                                if user_eq1 != real_eq1 or user_eq2 != real_eq2:
                                    continue 

                            pred_g = user_preds[m_id].get("ganador", determinar_ganador(user_preds[m_id]["goles1"], user_preds[m_id]["goles2"]))
                            real_g = p.get("ganador_real", determinar_ganador(p["goles1"], p["goles2"]))
                            
                            pts = calcular_puntos_partido(
                                user_preds[m_id]["goles1"], user_preds[m_id]["goles2"], pred_g,
                                p["goles1"], p["goles2"], real_g
                            )
                            puntos_totales += pts
            
            # 2. Puntos por Equipos Clasificados (Listas Especiales)
            for equipo in user_specials.get("octavos", []):
                if equipo in oficial_octavos: puntos_totales += 5
            for equipo in user_specials.get("cuartos", []):
                if equipo in oficial_cuartos: puntos_totales += 7
            for equipo in user_specials.get("semis", []):
                if equipo in oficial_semis: puntos_totales += 10
                
            if oficial_campeon and user_specials.get("campeon") == oficial_campeon: puntos_totales += 20
            if oficial_vice and user_specials.get("vicecampeon") == oficial_vice: puntos_totales += 15

            tabla_data.append({"Nombre": u_data["nombre"], "Puntos": puntos_totales})

    if tabla_data:
        df = pd.DataFrame(tabla_data).sort_values(by="Puntos", ascending=False).reset_index(drop=True)
        df.index += 1
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Aún no hay participantes en este grupo o no hay puntos calculados.")

# ==========================================
# PANEL DE ADMINISTRADOR Y SANDBOX
# ==========================================
def render_admin_panel():
    st.sidebar.title("⚙️ Panel de Control")
    st.sidebar.write("Modo Administrador")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("Opciones", [
        "Ver Tablas de Posiciones", 
        "Sandbox: Ingreso de Resultados", 
        "Gestión de Fases y Clasificados", 
        "Sincronizar API (Botón Maestro)",
        "🔍 Diagnóstico de Conexión"
    ])

    if menu == "Ver Tablas de Posiciones": admin_ver_tablas()
    elif menu == "Sandbox: Ingreso de Resultados": admin_sandbox_resultados()
    elif menu == "Gestión de Fases y Clasificados": admin_gestion_fases()
    elif menu == "Sincronizar API (Botón Maestro)": admin_sincronizar_api()
    elif menu == "🔍 Diagnóstico de Conexión": admin_diagnostico()

def admin_diagnostico():
    st.header("🔍 Diagnóstico de Conexión a Google Sheets")
    st.write("Ejecutando pruebas paso a paso para encontrar el problema exacto...")
    
    if not GSPREAD_AVAILABLE:
        st.error("❌ ERROR 1: La librería `gspread` no se instaló. Revisa tu archivo requirements.txt en GitHub.")
        return
    st.success("✅ Paso 1: Librería gspread instalada correctamente.")

    if "gcp_service_account" not in st.secrets:
        st.error("❌ ERROR 2: Streamlit no detecta los Secretos. Revisa que el texto TOML esté pegado correctamente en App Settings > Secrets.")
        return
    st.success("✅ Paso 2: Las contraseñas (Secretos) fueron detectadas en Streamlit.")

    try:
        client = get_gspread_client()
        if not client:
            st.error("❌ ERROR 3: Las credenciales son inválidas. Verifica que copiaste toda la private_key incluyendo BEGIN y END.")
            return
        st.success("✅ Paso 3: Autenticación con Google Cloud exitosa. ¡La contraseña es correcta!")
        
        try:
            sheet = client.open(SHEET_NAME)
            st.success(f"✅ Paso 4: Excel '{SHEET_NAME}' encontrado en tu Google Drive.")
            
            try:
                worksheet = sheet.sheet1
                st.success("✅ Paso 5: Pestaña del Excel leída correctamente. ¡Todo debería estar funcionando!")
                st.info("Si llegaste hasta aquí y el Excel sigue en blanco, intenta guardar un pronóstico nuevo ahora.")
            except Exception as e:
                st.error(f"❌ ERROR 5: Problema leyendo la pestaña del Excel. Detalle: {e}")
                
        except gspread.exceptions.SpreadsheetNotFound:
            correo_bot = st.secrets["gcp_service_account"].get("client_email", "desconocido")
            st.error(f"❌ ERROR 4: No se encontró el archivo '{SHEET_NAME}'. Entra a tu Google Drive y asegúrate de compartir el archivo con rol de EDITOR exactamente a este correo: {correo_bot}")
        except gspread.exceptions.APIError as api_error:
            st.error(f"❌ ERROR DE API (Muy común): No has activado las APIs. Ve a Google Cloud Console, busca 'Google Sheets API' y 'Google Drive API' y dales clic en HABILITAR. Detalle técnico: {api_error}")
            
    except Exception as e:
        st.error(f"❌ ERROR DE CREDENCIALES: Hay un error de formato en el texto que pegaste en los Secretos. Asegúrate de no haber borrado comillas. Detalle: {str(e)}")

def admin_ver_tablas():
    st.header("📊 Tablas de Posiciones (Vista Admin)")
    st.write("Aquí puedes ver las puntuaciones de todos los grupos y auditar el sistema.")
    
    users = load_data(DB_USERS)
    matches = load_data(DB_MATCHES)
    predictions = load_data(DB_PREDICTIONS)
    specials = load_data(DB_SPECIALS)
    settings = load_data(DB_SETTINGS)

    grupo_sel = st.selectbox("Seleccionar Grupo a visualizar:", ["Todos", "Familia", "Amigos", "Trabajo"])

    tabla_data = []
    
    oficial_octavos = settings.get("octavos_oficial", [])
    oficial_cuartos = settings.get("cuartos_oficial", [])
    oficial_semis = settings.get("semis_oficial", [])
    oficial_campeon = settings.get("campeon_oficial")
    oficial_vice = settings.get("vice_oficial")

    for email, u_data in users.items():
        if u_data.get("rol") == "admin": continue
        
        if grupo_sel == "Todos" or u_data["grupo"] == grupo_sel:
            puntos_totales = 0
            user_preds = predictions.get(email, {})
            user_specials = specials.get(email, {})
            
            for fase, partidos in matches.items():
                for p in partidos:
                    if p["jugado"]:
                        m_id = p["id"]
                        if m_id in user_preds:
                            if fase != "fase_grupos":
                                user_eq1 = resolve_user_team(m_id, 1, matches, user_preds)
                                user_eq2 = resolve_user_team(m_id, 2, matches, user_preds)
                                real_eq1 = resolve_admin_team(m_id, 1, matches)
                                real_eq2 = resolve_admin_team(m_id, 2, matches)
                                
                                if user_eq1 != real_eq1 or user_eq2 != real_eq2:
                                    continue 

                            pred_g = user_preds[m_id].get("ganador", determinar_ganador(user_preds[m_id]["goles1"], user_preds[m_id]["goles2"]))
                            real_g = p.get("ganador_real", determinar_ganador(p["goles1"], p["goles2"]))
                            
                            pts = calcular_puntos_partido(
                                user_preds[m_id]["goles1"], user_preds[m_id]["goles2"], pred_g,
                                p["goles1"], p["goles2"], real_g
                            )
                            puntos_totales += pts
            
            for equipo in user_specials.get("octavos", []):
                if equipo in oficial_octavos: puntos_totales += 5
            for equipo in user_specials.get("cuartos", []):
                if equipo in oficial_cuartos: puntos_totales += 7
            for equipo in user_specials.get("semis", []):
                if equipo in oficial_semis: puntos_totales += 10
                
            if oficial_campeon and user_specials.get("campeon") == oficial_campeon: puntos_totales += 20
            if oficial_vice and user_specials.get("vicecampeon") == oficial_vice: puntos_totales += 15

            tabla_data.append({
                "Nombre": u_data["nombre"], 
                "Grupo": u_data["grupo"], 
                "Puntos": puntos_totales
            })

    if tabla_data:
        df = pd.DataFrame(tabla_data).sort_values(by="Puntos", ascending=False).reset_index(drop=True)
        df.index += 1
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No hay datos o participantes para mostrar.")

def admin_sandbox_resultados():
    st.header("🛠️ Sandbox: Ingresar Resultados Reales")
    st.write("Ingresa los marcadores OFICIALES para que la app calcule los puntos base por partido.")
    
    matches = load_data(DB_MATCHES)
    
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        fase_sel = st.selectbox("Fase del Torneo", list(FASES_NOMBRES.keys()), format_func=lambda x: FASES_NOMBRES[x])
    with col_filtro2:
        if fase_sel == "fase_grupos":
            lista_grupos = ["Todos"] + [f"Grupo {chr(i)}" for i in range(65, 77)]
            grupo_filtro = st.selectbox("Sub-filtro: Grupo", lista_grupos)
        else:
            grupo_filtro = "Todos"
            st.selectbox("Sub-filtro: Grupo", ["Único"], disabled=True)

    partidos_fase = matches.get(fase_sel, [])
    if grupo_filtro != "Todos":
        partidos_fase = [p for p in partidos_fase if p.get("grupo") == grupo_filtro]
    
    if not partidos_fase:
        st.write("No hay partidos para mostrar en este filtro.")

    with st.form("form_sandbox"):
        for p in partidos_fase:
            m_id = p["id"]
            
            col1, col2, col3, col4 = st.columns(4)
            
            if fase_sel == "octavos":
                base_eq1 = p['equipo1']
                base_eq2 = p['equipo2']
                idx1 = EQUIPOS_MUNDIAL.index(p.get("equipo1_real")) + 1 if p.get("equipo1_real") in EQUIPOS_MUNDIAL else 0
                idx2 = EQUIPOS_MUNDIAL.index(p.get("equipo2_real")) + 1 if p.get("equipo2_real") in EQUIPOS_MUNDIAL else 0
                
                with col1: eq1_name = st.selectbox(f"REAL: {base_eq1}", [base_eq1] + EQUIPOS_MUNDIAL, index=idx1, key=f"rsel1_{m_id}")
                with col2: eq2_name = st.selectbox(f"REAL: {base_eq2}", [base_eq2] + EQUIPOS_MUNDIAL, index=idx2, key=f"rsel2_{m_id}")
                
                p["equipo1_real"] = eq1_name
                p["equipo2_real"] = eq2_name
            else:
                eq1_name = resolve_admin_team(m_id, 1, matches) if fase_sel != "fase_grupos" else p['equipo1']
                eq2_name = resolve_admin_team(m_id, 2, matches) if fase_sel != "fase_grupos" else p['equipo2']
                st.markdown(f"**{p.get('grupo', '')}**: {eq1_name} vs {eq2_name}")
            
            with col1: g1 = st.number_input(f"Goles Eq 1", min_value=0, max_value=15, value=p.get("goles1") if p.get("goles1") is not None else 0, key=f"real_g1_{m_id}")
            with col2: g2 = st.number_input(f"Goles Eq 2", min_value=0, max_value=15, value=p.get("goles2") if p.get("goles2") is not None else 0, key=f"real_g2_{m_id}")
            with col3: jugado = st.checkbox("Partido Finalizado", value=p.get("jugado", False), key=f"jugado_{m_id}")
            with col4: 
                if fase_sel != "fase_grupos":
                    opc_clas_txt = ["- Selecciona para Árbol Visual -", eq1_name, eq2_name]
                    opc_clas_val = [None, "equipo1", "equipo2"]
                    prev_clasif = p.get("clasifica")
                    idx_cl = opc_clas_val.index(prev_clasif) if prev_clasif in opc_clas_val else 0
                    clas_ui = st.selectbox("Avanza a siguiente ronda:", opc_clas_txt, index=idx_cl, key=f"clasif_{m_id}")
                    p["clasifica"] = opc_clas_val[opc_clas_txt.index(clas_ui)]

            opciones_txt = [f"Gana {eq1_name}", "Empate", f"Gana {eq2_name}"]
            opciones_val = ["equipo1", "empate", "equipo2"]
            
            default_real = determinar_ganador(p.get("goles1"), p.get("goles2")) if p.get("goles1") is not None else "empate"
            prev_ganador_real = p.get("ganador_real", default_real)
            idx_ganador = opciones_val.index(prev_ganador_real) if prev_ganador_real in opciones_val else 1
            
            ganador_ui = st.radio("Tendencia en 90/120 min OFICIAL:", opciones_txt, index=idx_ganador, key=f"real_rad_{m_id}", horizontal=True)
            ganador_real = opciones_val[opciones_txt.index(ganador_ui)]

            p["goles1"] = g1 if jugado else None
            p["goles2"] = g2 if jugado else None
            p["jugado"] = jugado
            p["ganador_real"] = ganador_real
            st.divider()

        if st.form_submit_button("Guardar Resultados de Partidos", type="primary"):
            save_data(matches, DB_MATCHES)
            st.success("Resultados guardados exitosamente.")

def admin_gestion_fases():
    st.header("⚙️ Gestión de Fases y Clasificados")
    st.write("En esta sección declaras oficialmente qué equipos avanzaron en la realidad. Esto es lo que la app usará para darle puntos de clasificación a los usuarios.")
    
    settings = load_data(DB_SETTINGS)
    
    with st.form("form_fases"):
        st.subheader("Configuración Visual")
        nueva_fase = st.selectbox("Fase Activa Inicial por Defecto (Al abrir la app)", 
                                 list(FASES_NOMBRES.keys()),
                                 index=list(FASES_NOMBRES.keys()).index(settings.get("fase_actual", "fase_grupos")),
                                 format_func=lambda x: FASES_NOMBRES[x])
        
        st.divider()
        st.subheader("Declaración Oficial de Clasificados (Para cálculo de puntos)")
        
        col1, col2 = st.columns(2)
        with col1:
            oct_oficial = st.multiselect("⚽ 16 Equipos Oficiales en OCTAVOS", EQUIPOS_MUNDIAL, default=settings.get("octavos_oficial", []), max_selections=16)
            cua_oficial = st.multiselect("🔥 8 Equipos Oficiales en CUARTOS", EQUIPOS_MUNDIAL, default=settings.get("cuartos_oficial", []), max_selections=8)
        with col2:
            sem_oficial = st.multiselect("🌟 4 Equipos Oficiales en SEMIS", EQUIPOS_MUNDIAL, default=settings.get("semis_oficial", []), max_selections=4)
            
            idx_c = EQUIPOS_MUNDIAL.index(settings.get("campeon_oficial")) if settings.get("campeon_oficial") in EQUIPOS_MUNDIAL else -1
            idx_v = EQUIPOS_MUNDIAL.index(settings.get("vice_oficial")) if settings.get("vice_oficial") in EQUIPOS_MUNDIAL else -1
            
            c_oficial = st.selectbox("🏆 Campeón Oficial", [""] + EQUIPOS_MUNDIAL, index=idx_c+1)
            v_oficial = st.selectbox("🥈 Vicecampeón Oficial", [""] + EQUIPOS_MUNDIAL, index=idx_v+1)

        if st.form_submit_button("Guardar Clasificados Oficiales", type="primary"):
            settings["fase_actual"] = nueva_fase
            settings["octavos_oficial"] = oct_oficial
            settings["cuartos_oficial"] = cua_oficial
            settings["semis_oficial"] = sem_oficial
            settings["campeon_oficial"] = c_oficial if c_oficial != "" else None
            settings["vice_oficial"] = v_oficial if v_oficial != "" else None
            save_data(settings, DB_SETTINGS)
            st.success("Configuración actualizada. La tabla de posiciones ha repartido los puntos.")
    
    st.divider()
    st.subheader("Zona de Peligro")
    if st.button("⚠️ Restaurar Partidos de Prueba (OBLIGATORIO DESPUÉS DE ACTUALIZAR EL CÓDIGO)"):
        save_data(get_initial_matches(), DB_MATCHES) 
        st.success("¡Base de datos de partidos restaurada!.")
        st.rerun()

def admin_sincronizar_api():
    st.header("🔄 Sincronización Maestra (API)")
    st.write("Este es el botón maestro para conectar con una API externa en el futuro.")
    st.info("Actualmente en modo de simulación. Al hacer clic, actualizaría los resultados automáticamente.")
    
    if st.button("🔥 Sincronizar Resultados FIFA AHORA", type="primary"):
        with st.spinner('Conectando a la API de Fútbol...'):
            st.success("¡Sincronización exitosa! Se descargaron 4 nuevos resultados.")
            st.write("La base de datos central ha sido actualizada y los puntos recalculados en cascada para todos los grupos.")

# ==========================================
# RUTEO PRINCIPAL (APP START)
# ==========================================
def main():
    init_db()
    
    if 'user' not in st.session_state:
        render_login()
    else:
        if st.session_state.get('rol') == 'admin':
            render_admin_panel()
        else:
            render_dashboard_usuario()

if __name__ == "__main__":
    main()
