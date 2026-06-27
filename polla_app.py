import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import json
import os
import time
import requests

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
st.set_page_config(page_title="Polla Mundialista 2026", page_icon="🏆", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# CONSTANTES
# ==========================================
SHEET_NAME = "Polla_DB_2026"
DB_DIR = "db_polla"
DB_USERS = "users"
DB_PREDICTIONS = "predictions"
DB_MATCHES = "matches"
DB_SETTINGS = "settings"
DB_SPECIALS = "special_preds"

# [MANTENEMOS TUS DEADLINES]
DEADLINES = {
    "fase_grupos": datetime(2026, 6, 10, 23, 59),
    "eliminatorias": datetime(2026, 6, 27, 23, 59) 
}

FASES_NOMBRES = {
    "fase_grupos": "Fase de Grupos",
    "dieciseisavos": "Dieciseisavos de Final",
    "octavos": "Octavos de Final",
    "cuartos": "Cuartos de Final",
    "semis": "Semifinales",
    "final": "Gran Final"
}

EQUIPOS_MUNDIAL = sorted(["Alemania", "Arabia Saudí", "Argelia", "Argentina", "Australia", "Austria", "Bélgica", "Bosnia y Herzegovina", "Brasil", "Cabo Verde", "Canadá", "Catar", "Colombia", "Costa de Marfil", "Croacia", "Curazao", "Ecuador", "Egipto", "Escocia", "España", "Estados Unidos", "Francia", "Ghana", "Haití", "Inglaterra", "Irak", "Japón", "Jordania", "Marruecos", "México", "Noruega", "Nueva Zelanda", "Países Bajos", "Panamá", "Paraguay", "Portugal", "RD Congo", "RI de Irán", "República Checa", "República de Corea", "Senegal", "Sudáfrica", "Suecia", "Suiza", "Turquía", "Túnez", "Uruguay", "Uzbekistán"])

# ==========================================
# FUNCIONES DE BASE DE DATOS (MISMAS)
# ==========================================
def load_data(key):
    # (Mantener tu lógica actual de load_data)
    filepath = os.path.join(DB_DIR, f"{key}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_data(data, key):
    # (Mantener tu lógica actual de save_data)
    if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
    filepath = os.path.join(DB_DIR, f"{key}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    load_data.clear()

def get_initial_matches():
    # Retorna la estructura de los 32 equipos (Dieciseisavos)
    # [AQUÍ VA TU ESTRUCTURA COMPLETA DE PARTIDOS]
    return {
        "fase_grupos": [...], # (Asegúrate de incluir todos los partidos de grupos aquí)
        "dieciseisavos": [...],
        "octavos": [...],
        "cuartos": [...],
        "semis": [...],
        "final": [...]
    }

# ==========================================
# LÓGICA DE SINCRONIZACIÓN Y CLASIFICADOS
# ==========================================
def sync_special_predictions(user_email, predictions, matches, mappings):
    user_preds = predictions.get(user_email, {})
    specials = load_data(DB_SPECIALS)
    if user_email not in specials: specials[user_email] = {}
    # (Tu lógica de sincronización aquí...)
    save_data(specials, DB_SPECIALS)

def resolve_user_team(m_id, slot, matches_dict, user_preds, mappings):
    # (Tu lógica resolve_user_team actualizada para priorizar manual)
    p = get_match_by_id(matches_dict, m_id)
    user_choice = user_preds.get(m_id, {}).get(f"equipo{slot}_user")
    if user_choice: return user_choice
    # ... resto de la lógica ...
    return p.get(f"equipo{slot}")

# ==========================================
# PANEL ADMIN CON EL BOTÓN DE RESTAURACIÓN
# ==========================================
def admin_gestion_fases():
    st.header("⚙️ Gestión de Fases y Clasificados")
    
    # BOTÓN OBLIGATORIO PARA MIGRAR EL FORMATO
    if st.button("⚠️ Restaurar Partidos de Prueba (OBLIGATORIO DESPUÉS DE ACTUALIZAR EL CÓDIGO)"):
        new_matches = get_initial_matches()
        save_data(new_matches, DB_MATCHES)
        st.success("Partidos reiniciados a formato de 48 equipos (32 clasificados). No se han borrado tus usuarios ni pronósticos previos.")
        
    # (Resto de tu configuración de fases...)

def main():
    # Inicialización estándar
    init_db()
    if 'user' not in st.session_state: render_login()
    else: 
        if st.session_state.get('rol') == 'admin': render_admin_panel()
        else: render_dashboard_usuario()

if __name__ == "__main__":
    main()
