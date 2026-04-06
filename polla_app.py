import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import json
import os

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
# CONSTANTES Y RUTAS DE ARCHIVOS (SIMULANDO BASE DE DATOS)
# ==========================================
DB_DIR = "db_polla"
USERS_FILE = os.path.join(DB_DIR, "users.json")
PREDICTIONS_FILE = os.path.join(DB_DIR, "predictions.json")
MATCHES_FILE = os.path.join(DB_DIR, "matches.json")
SETTINGS_FILE = os.path.join(DB_DIR, "settings.json")
SPECIAL_PREDS_FILE = os.path.join(DB_DIR, "special_preds.json")

# Fechas límite (quemadas para el ejemplo, pero editables por admin)
DEADLINE_FASE_GRUPOS = datetime(2026, 6, 10, 23, 59)
DEADLINE_OCTAVOS = datetime(2026, 6, 27, 23, 59)

# ==========================================
# FUNCIONES DE BASE DE DATOS LOCAL (JSON)
# ==========================================
def init_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    
    # Usuarios
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            admin_pwd = hash_password("admin123")
            json.dump({"admin@polla.com": {"nombre": "Xavier Admin", "pwd": admin_pwd, "grupo": "Admin", "pais": "Ecuador", "rol": "admin"}}, f)
    
    # Pronósticos y Especiales
    if not os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, 'w') as f: json.dump({}, f)

    if not os.path.exists(SPECIAL_PREDS_FILE):
        with open(SPECIAL_PREDS_FILE, 'w') as f: json.dump({}, f)
            
    # Partidos (Estructura expandida con todos los grupos)
    if not os.path.exists(MATCHES_FILE):
        with open(MATCHES_FILE, 'w') as f:
            initial_matches = {
                "fase_grupos": [
                    {"id": "G1", "grupo": "Grupo A", "equipo1": "Ecuador", "equipo2": "Qatar", "fecha": "2026-06-11 10:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G2", "grupo": "Grupo A", "equipo1": "Países Bajos", "equipo2": "Senegal", "fecha": "2026-06-11 15:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G3", "grupo": "Grupo B", "equipo1": "EEUU", "equipo2": "Gales", "fecha": "2026-06-12 10:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G4", "grupo": "Grupo B", "equipo1": "Inglaterra", "equipo2": "Irán", "fecha": "2026-06-12 15:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G5", "grupo": "Grupo C", "equipo1": "Argentina", "equipo2": "Arabia Saudita", "fecha": "2026-06-13 10:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G6", "grupo": "Grupo C", "equipo1": "México", "equipo2": "Polonia", "fecha": "2026-06-13 15:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G7", "grupo": "Grupo D", "equipo1": "Francia", "equipo2": "Australia", "fecha": "2026-06-14 10:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G8", "grupo": "Grupo E", "equipo1": "España", "equipo2": "Costa Rica", "fecha": "2026-06-15 10:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G9", "grupo": "Grupo F", "equipo1": "Bélgica", "equipo2": "Canadá", "fecha": "2026-06-16 10:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G10", "grupo": "Grupo G", "equipo1": "Brasil", "equipo2": "Serbia", "fecha": "2026-06-17 10:00", "goles1": None, "goles2": None, "jugado": False},
                    {"id": "G11", "grupo": "Grupo H", "equipo1": "Portugal", "equipo2": "Uruguay", "fecha": "2026-06-18 10:00", "goles1": None, "goles2": None, "jugado": False}
                ],
                "octavos": [
                    {"id": "O1", "grupo": "Octavos", "equipo1": "Por Definir A1", "equipo2": "Por Definir B2", "fecha": "2026-06-28 15:00", "goles1": None, "goles2": None, "jugado": False, "clasifica": None}
                ]
            }
            json.dump(initial_matches, f)

    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({"fase_actual": "fase_grupos", "campeon_oficial": None, "vice_oficial": None}, f)

def load_data(file_path):
    with open(file_path, 'r') as f: return json.load(f)

def save_data(data, file_path):
    with open(file_path, 'w') as f: json.dump(data, f, indent=4)

# ==========================================
# UTILIDADES Y LÓGICA DE NEGOCIO
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

# Modificado para recibir pred_ganador de forma explícita
def calcular_puntos_partido(pred_goles1, pred_goles2, pred_ganador, real_goles1, real_goles2):
    puntos = 0
    if real_goles1 is None or real_goles2 is None:
        return 0

    # El ganador real SIEMPRE se basa en los goles oficiales
    real_ganador = determinar_ganador(real_goles1, real_goles2)

    # 1. Acierto de Ganador/Empate explícito (1 punto)
    if pred_ganador == real_ganador:
        puntos += 1

    # 2. Acierto de Goles exactos por equipo (1 punto cada uno)
    if pred_goles1 == real_goles1: puntos += 1
    if pred_goles2 == real_goles2: puntos += 1

    # 3. Marcador Exacto (Bono de 2 puntos si acertó todo)
    if pred_goles1 == real_goles1 and pred_goles2 == real_goles2:
        puntos += 2

    return puntos

# ==========================================
# COMPONENTES DE INTERFAZ (UI)
# ==========================================
def render_login():
    st.title("🏆 Polla Mundialista 2026")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        st.subheader("Acceso a tu cuenta")
        email = st.text_input("Correo electrónico", key="login_email").strip().lower()
        pwd = st.text_input("Contraseña", type="password", key="login_pwd")
        
        if st.button("Entrar", type="primary"):
            users = load_data(USERS_FILE)
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
            users = load_data(USERS_FILE)
            if new_email in users:
                st.error("El correo ya está registrado.")
            elif new_name and new_email and new_pwd:
                users[new_email] = {
                    "nombre": new_name, "pwd": hash_password(new_pwd),
                    "grupo": new_group, "pais": new_country, "rol": "user"
                }
                save_data(users, USERS_FILE)
                st.success("¡Registro exitoso! Por favor inicia sesión.")
            else:
                st.warning("Completa todos los campos.")

def render_dashboard_usuario():
    st.sidebar.title(f"Hola, {st.session_state['nombre']}")
    st.sidebar.write(f"**Grupo:** {st.session_state['grupo']}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("Navegación", ["Mis Pronósticos", "Tabla de Posiciones", "Predicciones Especiales"])

    if menu == "Mis Pronósticos": mostrar_pantalla_pronosticos()
    elif menu == "Tabla de Posiciones": mostrar_tabla_posiciones()
    elif menu == "Predicciones Especiales": mostrar_predicciones_especiales()

def mostrar_pantalla_pronosticos():
    st.header("Mis Pronósticos")
    
    matches = load_data(MATCHES_FILE)
    settings = load_data(SETTINGS_FILE)
    predictions = load_data(PREDICTIONS_FILE)
    user_email = st.session_state['user']
    
    if user_email not in predictions: predictions[user_email] = {}

    fase_activa = settings["fase_actual"]
    ahora = datetime.now()
    puede_editar = True
    mensaje_cierre = ""
    
    if fase_activa == "fase_grupos":
        if ahora > DEADLINE_FASE_GRUPOS:
            puede_editar = False
            mensaje_cierre = "La fase de grupos está CERRADA para edición."
        else:
            mensaje_cierre = f"Se cierra el: {DEADLINE_FASE_GRUPOS.strftime('%Y-%m-%d %H:%M')}"
    elif fase_activa == "octavos":
         if ahora > DEADLINE_OCTAVOS:
             puede_editar = False
             mensaje_cierre = "La fase de Octavos está CERRADA para edición."
         else:
             mensaje_cierre = f"Se cierra el: {DEADLINE_OCTAVOS.strftime('%Y-%m-%d %H:%M')}"

    st.info(f"Fase actual: {fase_activa.replace('_', ' ').title()} | {mensaje_cierre}")

    with st.form("form_pronosticos"):
        st.subheader(f"Partidos - {fase_activa.replace('_', ' ').title()}")
        
        partidos_fase = matches.get(fase_activa, [])
        nuevos_pronosticos = {}
        
        for p in partidos_fase:
            m_id = p["id"]
            st.markdown(f"**{p.get('grupo', '')}** | Fecha: {p['fecha']}")
            
            # Obtener pronóstico previo
            pred_prev = predictions[user_email].get(m_id, {"goles1": 0, "goles2": 0, "ganador": "empate"})
            
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
            with col1: st.write(f"<h5 style='text-align: right;'>{p['equipo1']}</h5>", unsafe_allow_html=True)
            with col2: g1 = st.number_input("Goles", min_value=0, max_value=15, value=pred_prev.get("goles1", 0), key=f"g1_{m_id}", disabled=not puede_editar, label_visibility="collapsed")
            with col3: st.markdown("<h4 style='text-align: center;'>vs</h4>", unsafe_allow_html=True)
            with col4: g2 = st.number_input("Goles", min_value=0, max_value=15, value=pred_prev.get("goles2", 0), key=f"g2_{m_id}", disabled=not puede_editar, label_visibility="collapsed")
            with col5: st.write(f"<h5>{p['equipo2']}</h5>", unsafe_allow_html=True)
            
            # SELECCIÓN EXPLICITA DE GANADOR
            opciones_txt = [f"Gana {p['equipo1']}", "Empate", f"Gana {p['equipo2']}"]
            opciones_val = ["equipo1", "empate", "equipo2"]
            
            # Buscar indice previo (default: empate si no hay, o calcular base a goles si era app vieja)
            prev_ganador = pred_prev.get("ganador", determinar_ganador(pred_prev.get("goles1",0), pred_prev.get("goles2",0)))
            idx_ganador = opciones_val.index(prev_ganador) if prev_ganador in opciones_val else 1
            
            ganador_ui = st.radio("Tendencia final:", opciones_txt, index=idx_ganador, key=f"rad_{m_id}", horizontal=True, disabled=not puede_editar)
            ganador_final = opciones_val[opciones_txt.index(ganador_ui)]

            st.divider()
            nuevos_pronosticos[m_id] = {"goles1": g1, "goles2": g2, "ganador": ganador_final}

        if puede_editar:
            if st.form_submit_button("Guardar Pronósticos", type="primary"):
                predictions[user_email].update(nuevos_pronosticos)
                save_data(predictions, PREDICTIONS_FILE)
                st.success("¡Pronósticos guardados correctamente!")
        else:
             st.form_submit_button("Guardar Pronósticos", disabled=True)

def mostrar_predicciones_especiales():
    st.header("Predicciones Especiales (Bonos)")
    st.write("Si aciertas al Campeón y Vicecampeón desde la Fase de Grupos, obtienes +5 pts por cada uno.")
    
    ahora = datetime.now()
    puede_editar = ahora <= DEADLINE_FASE_GRUPOS
    
    specials = load_data(SPECIAL_PREDS_FILE)
    user_email = st.session_state['user']
    
    if user_email not in specials: specials[user_email] = {"campeon": "", "vicecampeon": ""}
    mis_specials = specials[user_email]

    equipos_probables = ["Argentina", "Brasil", "Francia", "Inglaterra", "España", "Alemania", "Ecuador", "EEUU", "Portugal", "Otro"]

    with st.form("form_specials"):
        idx_campeon = equipos_probables.index(mis_specials["campeon"]) if mis_specials["campeon"] in equipos_probables else 0
        idx_vice = equipos_probables.index(mis_specials["vicecampeon"]) if mis_specials["vicecampeon"] in equipos_probables else 0

        campeon = st.selectbox("🏆 Campeón del Mundo", equipos_probables, index=idx_campeon, disabled=not puede_editar)
        vice = st.selectbox("🥈 Vicecampeón", equipos_probables, index=idx_vice, disabled=not puede_editar)
        
        if puede_editar:
            if st.form_submit_button("Guardar Predicciones Especiales"):
                specials[user_email] = {"campeon": campeon, "vicecampeon": vice}
                save_data(specials, SPECIAL_PREDS_FILE)
                st.success("Predicciones especiales guardadas.")
        else:
             st.form_submit_button("Guardar Predicciones Especiales", disabled=True)

def mostrar_tabla_posiciones():
    st.header("Tabla de Posiciones")
    
    users = load_data(USERS_FILE)
    matches = load_data(MATCHES_FILE)
    predictions = load_data(PREDICTIONS_FILE)
    specials = load_data(SPECIAL_PREDS_FILE)
    settings = load_data(SETTINGS_FILE)

    grupo_sel = st.selectbox("Ver tabla de:", ["Mi Grupo (" + st.session_state['grupo'] + ")", "Familia", "Amigos", "Trabajo"])
    grupo_filtro = st.session_state['grupo'] if grupo_sel.startswith("Mi Grupo") else grupo_sel

    tabla_data = []

    for email, u_data in users.items():
        if u_data.get("rol") == "admin": continue
        if u_data["grupo"] == grupo_filtro:
            puntos_totales = 0
            user_preds = predictions.get(email, {})
            
            for fase, partidos in matches.items():
                for p in partidos:
                    if p["jugado"]:
                        m_id = p["id"]
                        if m_id in user_preds:
                            # Soporte para app vieja (si no tiene ganador explícito guardado, lo calcula)
                            pred_g = user_preds[m_id].get("ganador", determinar_ganador(user_preds[m_id]["goles1"], user_preds[m_id]["goles2"]))
                            pts = calcular_puntos_partido(
                                user_preds[m_id]["goles1"], user_preds[m_id]["goles2"], pred_g,
                                p["goles1"], p["goles2"]
                            )
                            puntos_totales += pts
            
            # Bonos Especiales
            campeon_oficial = settings.get("campeon_oficial")
            vice_oficial = settings.get("vice_oficial")
            user_specials = specials.get(email, {})
            
            if campeon_oficial and user_specials.get("campeon") == campeon_oficial: puntos_totales += 25
            if vice_oficial and user_specials.get("vicecampeon") == vice_oficial: puntos_totales += 20

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
        "Gestión de Fases", 
        "Sincronizar API (Botón Maestro)"
    ])

    if menu == "Ver Tablas de Posiciones": admin_ver_tablas()
    elif menu == "Sandbox: Ingreso de Resultados": admin_sandbox_resultados()
    elif menu == "Gestión de Fases": admin_gestion_fases()
    elif menu == "Sincronizar API (Botón Maestro)": admin_sincronizar_api()

def admin_ver_tablas():
    st.header("📊 Tablas de Posiciones (Vista Admin)")
    st.write("Aquí puedes ver las puntuaciones de todos los grupos y auditar el sistema.")
    
    users = load_data(USERS_FILE)
    matches = load_data(MATCHES_FILE)
    predictions = load_data(PREDICTIONS_FILE)
    specials = load_data(SPECIAL_PREDS_FILE)
    settings = load_data(SETTINGS_FILE)

    grupo_sel = st.selectbox("Seleccionar Grupo a visualizar:", ["Todos", "Familia", "Amigos", "Trabajo"])

    tabla_data = []

    for email, u_data in users.items():
        if u_data.get("rol") == "admin": continue
        
        if grupo_sel == "Todos" or u_data["grupo"] == grupo_sel:
            puntos_totales = 0
            user_preds = predictions.get(email, {})
            
            for fase, partidos in matches.items():
                for p in partidos:
                    if p["jugado"]:
                        m_id = p["id"]
                        if m_id in user_preds:
                            pred_g = user_preds[m_id].get("ganador", determinar_ganador(user_preds[m_id]["goles1"], user_preds[m_id]["goles2"]))
                            pts = calcular_puntos_partido(
                                user_preds[m_id]["goles1"], user_preds[m_id]["goles2"], pred_g,
                                p["goles1"], p["goles2"]
                            )
                            puntos_totales += pts
            
            campeon_oficial = settings.get("campeon_oficial")
            vice_oficial = settings.get("vice_oficial")
            user_specials = specials.get(email, {})
            
            if campeon_oficial and user_specials.get("campeon") == campeon_oficial: puntos_totales += 25
            if vice_oficial and user_specials.get("vicecampeon") == vice_oficial: puntos_totales += 20

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
    st.write("Ingresa los resultados oficiales para calcular los puntos de todos.")
    
    matches = load_data(MATCHES_FILE)
    fase_sel = st.selectbox("Seleccionar Fase", list(matches.keys()))
    partidos_fase = matches[fase_sel]
    
    with st.form("form_sandbox"):
        for p in partidos_fase:
            m_id = p["id"]
            st.markdown(f"**{p.get('grupo', '')}**: {p['equipo1']} vs {p['equipo2']}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: g1 = st.number_input(f"Goles {p['equipo1']}", min_value=0, max_value=15, value=p.get("goles1") if p.get("goles1") is not None else 0, key=f"real_g1_{m_id}")
            with col2: g2 = st.number_input(f"Goles {p['equipo2']}", min_value=0, max_value=15, value=p.get("goles2") if p.get("goles2") is not None else 0, key=f"real_g2_{m_id}")
            with col3: jugado = st.checkbox("Partido Finalizado", value=p.get("jugado", False), key=f"jugado_{m_id}")
            with col4:
                if fase_sel != "fase_grupos":
                    clasifica = st.selectbox("Clasifica", ["Ninguno", p['equipo1'], p['equipo2']], key=f"clasif_{m_id}")
                    p["clasifica"] = clasifica if clasifica != "Ninguno" else None
            
            p["goles1"] = g1 if jugado else None
            p["goles2"] = g2 if jugado else None
            p["jugado"] = jugado
            st.divider()

        if st.form_submit_button("Guardar Resultados Oficiales", type="primary"):
            save_data(matches, MATCHES_FILE)
            st.success("Resultados guardados en la Base de Datos. La tabla de posiciones se ha recalculado.")

def admin_gestion_fases():
    st.header("⚙️ Gestión de Fases del Torneo")
    settings = load_data(SETTINGS_FILE)
    
    with st.form("form_fases"):
        nueva_fase = st.selectbox("Fase Activa (La que los usuarios pueden ver y pronosticar)", 
                                 ["fase_grupos", "octavos", "cuartos", "semis", "final"],
                                 index=["fase_grupos", "octavos", "cuartos", "semis", "final"].index(settings.get("fase_actual", "fase_grupos")))
        
        st.subheader("Declaración de Campeones (Al finalizar el mundial)")
        equipos = ["", "Argentina", "Brasil", "Francia", "Inglaterra", "España", "Alemania", "Ecuador", "EEUU", "Portugal"]
        idx_c = equipos.index(settings.get("campeon_oficial")) if settings.get("campeon_oficial") in equipos else 0
        idx_v = equipos.index(settings.get("vice_oficial")) if settings.get("vice_oficial") in equipos else 0
        
        c_oficial = st.selectbox("Campeón Oficial", equipos, index=idx_c)
        v_oficial = st.selectbox("Vicecampeón Oficial", equipos, index=idx_v)

        if st.form_submit_button("Actualizar Configuración"):
            settings["fase_actual"] = nueva_fase
            settings["campeon_oficial"] = c_oficial if c_oficial != "" else None
            settings["vice_oficial"] = v_oficial if v_oficial != "" else None
            save_data(settings, SETTINGS_FILE)
            st.success("Configuración del torneo actualizada.")
    
    st.divider()
    st.subheader("Zona de Peligro")
    if st.button("⚠️ Restaurar Partidos de Prueba (Cargar Grupos A-H)"):
        if os.path.exists(MATCHES_FILE):
            os.remove(MATCHES_FILE)
        init_db() # Fuerza a crear el archivo con todos los partidos nuevos
        st.success("Partidos reiniciados exitosamente.")
        st.rerun()

def admin_sincronizar_api():
    st.header("🔄 Sincronización Maestra (API)")
    st.write("Este es el botón maestro para conectar con Football-Data.org o API-Football.")
    st.info("Actualmente en modo de simulación. Al hacer clic, actualizaría los resultados automáticamente sin ingresarlos a mano en el Sandbox.")
    
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
