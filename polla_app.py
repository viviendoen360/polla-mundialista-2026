<!-- ... existing code ... -->
def resolve_user_team(m_id, slot, matches_dict, user_preds, mappings):
    p = get_match_by_id(matches_dict, m_id)
    if f"origen{slot}" in p:
        origen_id = p[f"origen{slot}"]
        clasifica = user_preds.get(origen_id, {}).get("clasifica")
        if clasifica == "equipo1": return resolve_user_team(origen_id, 1, matches_dict, user_preds, mappings)
        elif clasifica == "equipo2": return resolve_user_team(origen_id, 2, matches_dict, user_preds, mappings)
        else: return "Por Definir" 
    else:
        base_name = p.get(f"equipo{slot}")
        # Si el cupo le pertenece a un Tercero, intentamos buscar la selección manual del usuario
        if "3ro" in base_name:
            user_choice = user_preds.get(m_id, {}).get(f"equipo{slot}_user")
            if user_choice and user_choice != "No asignado":
                return user_choice
                
        # De lo contrario (ej. 1ro de grupo), priorizamos Sandbox y luego cálculos
        real_name = p.get(f"equipo{slot}_real")
<!-- ... existing code ... -->
        for phase in ["dieciseisavos", "octavos", "cuartos", "semis"]:
            for p in matches.get(phase, []):
                e1 = resolve_user_team(p["id"], 1, matches, user_preds, mappings)
                e2 = resolve_user_team(p["id"], 2, matches, user_preds, mappings)
                
                if e1 and e1 not in invalidos and "Grupo" not in e1 and "3ro" not in e1:
                    if phase == "dieciseisavos": dieciseisavos.add(e1)
                    if phase == "octavos": octavos.add(e1)
                    if phase == "cuartos": cuartos.add(e1)
                    if phase == "semis": semis.add(e1)
                    
                if e2 and e2 not in invalidos and "Grupo" not in e2 and "3ro" not in e2:
                    if phase == "dieciseisavos": dieciseisavos.add(e2)
                    if phase == "octavos": octavos.add(e2)
                    if phase == "cuartos": cuartos.add(e2)
                    if phase == "semis": semis.add(e2)

        for p in matches.get("final", []):
            m_id = p["id"]
            e1 = resolve_user_team(m_id, 1, matches, user_preds, mappings)
            e2 = resolve_user_team(m_id, 2, matches, user_preds, mappings)
            if e1 and e2 and e1 not in invalidos and e2 not in invalidos:
                clasifica = user_preds.get(m_id, {}).get("clasifica")
                ganador = user_preds.get(m_id, {}).get("ganador")
                
                if "Grupo" not in e1 and "3ro" not in e1 and "Grupo" not in e2 and "3ro" not in e2:
                    if clasifica == "equipo1" or ganador == "equipo1":
                        campeon, vicecampeon = e1, e2
<!-- ... existing code ... -->
    if not partidos_fase: 
        st.write("No hay partidos en este grupo o fase.")
        return

    # =================================================================
    # EXCLUSIÓN MUTUA PARA EL USUARIO (SOLO TERCEROS)
    # =================================================================
    if fase_sel == "dieciseisavos":
        slots_terceros_u = []
        for p in partidos_fase:
            if "3ro" in p['equipo1']: slots_terceros_u.append((p["id"], "equipo1", 1, "u_dyn1_"))
            if "3ro" in p['equipo2']: slots_terceros_u.append((p["id"], "equipo2", 2, "u_dyn2_"))
            
        if slots_terceros_u:
            st.subheader("🧩 Asigna a tus Mejores Terceros")
            st.write("Los equipos que escojas desaparecerán de las demás listas para evitar duplicados.")
            
            # Extraer solo los 8 mejores terceros calculados automáticamente
            lista_8_terceros = [mappings[f"Mejor 3ro ({i})"] for i in range(1, 9) if f"Mejor 3ro ({i})" in mappings]
            if len(lista_8_terceros) < 8: # Seguro por si la fase de grupos no ha terminado
                lista_8_terceros = EQUIPOS_MUNDIAL
            
            equipos_usados_u = set()
            for m_id, slot_key, slot_idx, prefix in slots_terceros_u:
                val = st.session_state.get(f"{prefix}{m_id}", predictions[user_email].get(m_id, {}).get(f"equipo{slot_idx}_user"))
                if val and val != "No asignado": equipos_usados_u.add(val)

            cambios_terceros = False
            cols_u = st.columns(4) 
            c_idx = 0
            
            for m_id, slot_key, slot_idx, prefix in slots_terceros_u:
                p = next(match for match in partidos_fase if match["id"] == m_id)
                current_val = st.session_state.get(f"{prefix}{m_id}", predictions[user_email].get(m_id, {}).get(f"equipo{slot_idx}_user", "No asignado"))
                
                opts = ["No asignado"] + [eq for eq in lista_8_terceros if eq not in equipos_usados_u or eq == current_val]
                
                with cols_u[c_idx % 4]:
                    seleccion = st.selectbox(f"{p[slot_key]} (Match {m_id}):", opts, 
                                             index=opts.index(current_val) if current_val in opts else 0, 
                                             key=f"{prefix}{m_id}", disabled=not puede_editar)
                c_idx += 1
<!-- ... existing code ... -->
    if not partidos_fase:
        st.write("No hay partidos para mostrar en este filtro.")
        return

    # =================================================================
    # EXCLUSIÓN MUTUA EXCLUSIVA PARA TERCEROS (ADMIN)
    # =================================================================
    if fase_sel == "dieciseisavos":
        slots_terceros = []
        for p in partidos_fase:
            if "3ro" in p['equipo1']: slots_terceros.append((p["id"], "equipo1", "dyn1_"))
            if "3ro" in p['equipo2']: slots_terceros.append((p["id"], "equipo2", "dyn2_"))
            
        if slots_terceros:
            st.subheader("🧩 Asignación Oficial de Mejores Terceros")
            
            # Extraer solo los 8 mejores terceros calculados automáticamente
            lista_8_terceros = [mappings[f"Mejor 3ro ({i})"] for i in range(1, 9) if f"Mejor 3ro ({i})" in mappings]
            if len(lista_8_terceros) < 8:
                lista_8_terceros = EQUIPOS_MUNDIAL
            
            equipos_usados = set()
            for m_id, slot_key, prefix in slots_terceros:
                val = st.session_state.get(f"{prefix}{m_id}")
                if val and val != "No asignado": equipos_usados.add(val)

            cambios_terceros = False
            cols = st.columns(4) 
            c_idx = 0
            
            for m_id, slot_key, prefix in slots_terceros:
                p = next(match for match in partidos_fase if match["id"] == m_id)
                current_val = st.session_state.get(f"{prefix}{m_id}", p.get(f"{slot_key}_real", "No asignado"))
                
                opts = ["No asignado"] + [eq for eq in lista_8_terceros if eq not in equipos_usados or eq == current_val]
                
                with cols[c_idx % 4]:
                    seleccion = st.selectbox(f"{p[slot_key]} (Match {m_id}):", opts, 
                                             index=opts.index(current_val) if current_val in opts else 0, 
                                             key=f"{prefix}{m_id}")
                c_idx += 1
<!-- ... existing code ... -->
