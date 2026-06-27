# ... (código previo se mantiene igual)

def admin_sandbox_resultados():
    # ... (código previo)
    
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
