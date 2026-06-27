# ... (código previo se mantiene igual)

def admin_sandbox_resultados():
    st.header("🛠️ Sandbox: Ingresar Resultados Reales")
    st.write("Gestiona marcadores. La asignación manual de equipos es solo para los 'Mejores Terceros'.")
    
    matches = load_data(DB_MATCHES)
    # Re-calculamos mappings actuales por si hubo cambios en la API
    mappings = calcular_posiciones_grupos(matches)
    
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
        return

    # 1. Lógica Exclusiva para Terceros (Dropdowns de Exclusión Mutua)
    if fase_sel == "dieciseisavos":
        st.subheader("🧩 Asignación de Mejores Terceros")
        
        slots_terceros = []
        for p in partidos_fase:
            if "Tercero" in p['equipo1']: slots_terceros.append((p["id"], "equipo1", "dyn1_"))
            if "Tercero" in p['equipo2']: slots_terceros.append((p["id"], "equipo2", "dyn2_"))
            
        equipos_usados = set()
        for m_id, slot_key, prefix in slots_terceros:
            val = st.session_state.get(f"{prefix}{m_id}", p.get(f"{slot_key}_real", "No asignado"))
            if val and val != "No asignado": equipos_usados.add(val)

        for m_id, slot_key, prefix in slots_terceros:
            p = next(match for match in partidos_fase if match["id"] == m_id)
            current_val = st.session_state.get(f"{prefix}{m_id}", p.get(f"{slot_key}_real", "No asignado"))
            
            opciones = ["No asignado"] + [eq for eq in EQUIPOS_MUNDIAL if eq not in equipos_usados or eq == current_val]
            
            seleccion = st.selectbox(f"Asignar {p[slot_key]} (Match {m_id}):", opciones, 
                                     index=opciones.index(current_val) if current_val in opciones else 0, 
                                     key=f"{prefix}{m_id}")
            
            if seleccion != current_val:
                p[f"{slot_key}_real"] = seleccion if seleccion != "No asignado" else None
                save_data(matches, DB_MATCHES)
                st.rerun()

    # 2. Formulario estándar para goles (Aplica a TODOS los partidos)
    with st.form("form_sandbox"):
        for p in partidos_fase:
            m_id = p["id"]
            
            # Determinamos equipos (Reales vs Automáticos)
            if "Tercero" in p['equipo1'] or "Tercero" in p['equipo2']:
                eq1_display = p.get("equipo1_real") or p['equipo1']
                eq2_display = p.get("equipo2_real") or p['equipo2']
            else:
                eq1_display = resolve_admin_team(m_id, 1, matches, mappings) if fase_sel != "fase_grupos" else p['equipo1']
                eq2_display = resolve_admin_team(m_id, 2, matches, mappings) if fase_sel != "fase_grupos" else p['equipo2']
            
            st.markdown(f"**{eq1_display} vs {eq2_display}**")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: g1 = st.number_input(f"Goles {eq1_display}", min_value=0, max_value=15, value=p.get("goles1") or 0, key=f"g1_{m_id}")
            with c2: g2 = st.number_input(f"Goles {eq2_display}", min_value=0, max_value=15, value=p.get("goles2") or 0, key=f"g2_{m_id}")
            with c3: jugado = st.checkbox("Finalizado", value=p.get("jugado", False), key=f"j_{m_id}")
            
            # Lógica de ganador (Solo para fases KO)
            if fase_sel != "fase_grupos":
                with c4:
                    prev_clasif = p.get("clasifica")
                    opc_clas_txt = ["- Clasifica -", eq1_display, eq2_display]
                    opc_clas_val = [None, "equipo1", "equipo2"]
                    idx_cl = opc_clas_val.index(prev_clasif) if prev_clasif in opc_clas_val else 0
                    clas_ui = st.selectbox("¿Quién avanza?", opc_clas_txt, index=idx_cl, key=f"clasif_{m_id}")
                    if g1 > g2: p["clasifica"] = "equipo1"
                    elif g2 > g1: p["clasifica"] = "equipo2"
                    else: p["clasifica"] = opc_clas_val[opc_clas_txt.index(clas_ui)]

            p["goles1"] = g1 if jugado else None
            p["goles2"] = g2 if jugado else None
            p["jugado"] = jugado
            p["ganador_real"] = determinar_ganador(g1, g2) if jugado else None
            st.divider()

        if st.form_submit_button("Guardar Cambios de Goles", type="primary"):
            save_data(matches, DB_MATCHES)
            st.success("Resultados actualizados.")

    
    # LÓGICA DE EXCLUSIÓN MUTUA PARA MEJORES TERCEROS
    if fase_sel == "dieciseisavos":
        st.subheader("🧩 Asignación de Mejores Terceros")
        
        # 1. Identificar todos los slots de "Mejor Tercero" en los partidos
        # Supongamos que los terceros se identifican porque el nombre del equipo contiene "Tercero"
        slots_terceros = []
        for p in partidos_fase:
            if "Tercero" in p['equipo1']: slots_terceros.append((p["id"], "equipo1", "dyn1_"))
            if "Tercero" in p['equipo2']: slots_terceros.append((p["id"], "equipo2", "dyn2_"))
            
        # Obtener los equipos que ya han sido asignados manualmente a estos slots
        equipos_usados = set()
        for m_id, slot_key, prefix in slots_terceros:
            val = st.session_state.get(f"{prefix}{m_id}")
            if val and val != "No asignado":
                equipos_usados.add(val)

        # 2. Renderizar solo los Dropdowns para estos casos específicos
        for m_id, slot_key, prefix in slots_terceros:
            p = next(match for match in partidos_fase if match["id"] == m_id)
            current_val = st.session_state.get(f"{prefix}{m_id}", p.get(f"{slot_key}_real", "No asignado"))
            
            # Filtrar opciones: lista de terceros disponibles + el que ya está seleccionado
            opciones = ["No asignado"] + [eq for eq in EQUIPOS_TERCEROS if eq not in equipos_usados or eq == current_val]
            
            seleccion = st.selectbox(f"Asignar {p[slot_key]} (Match {m_id}):", opciones, 
                                     index=opciones.index(current_val) if current_val in opciones else 0, 
                                     key=f"{prefix}{m_id}")
            
            if seleccion != current_val:
                p[f"{slot_key}_real"] = seleccion if seleccion != "No asignado" else None
                save_data(matches, DB_MATCHES)
                st.rerun() # Actualizar vista para reflejar cambios en otros dropdowns

    # 3. Resto del formulario (Automático para equipos normales)
    with st.form("form_sandbox"):
        for p in partidos_fase:
            # Si tiene un *_real asignado manualmente, lo usamos; si no, el original
            eq1 = p.get("equipo1_real") or p['equipo1']
            eq2 = p.get("equipo2_real") or p['equipo2']
            
            st.write(f"**{eq1} vs {eq2}**")
            # ... (inputs de goles siguen igual)
