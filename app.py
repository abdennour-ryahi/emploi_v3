import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from scheduler import generate_schedule
from export_utils import generate_excel

st.set_page_config(page_title="Générateur de Planning Intelligent", layout="wide")

st.title("📅 Générateur de Planning Mensuel")
st.markdown("Système pour une planification équitable et flexible.")

# --- CONFIGURATION (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Paramètres Temporels")
    today = datetime.now()
    year = st.number_input("Année", min_value=2024, max_value=2030, value=today.year)
    month = st.selectbox("Mois", range(1, 13), index=today.month - 1, format_func=lambda x: calendar.month_name[x])
    num_days = calendar.monthrange(year, month)[1]
    
    st.divider()
    st.header("👥 Gestion de l'Équipe")
    num_agents = st.slider("Nombre d'agents", 3, 10, value=7)
    
    employees = []
    for i in range(num_agents):
        st.markdown(f"**Agent {i+1}**")
        # Use default values for initial setup
        def_name = f"Agent {chr(65+i)}" if i < 6 else "Mme Mliyani"
        def_sex = "M" if i < 6 else "F"
        
        c1, c2 = st.columns([2.2, 1])
        name = c1.text_input("Pseudo", value=def_name, key=f"side_name_{i}")
        sex = c2.selectbox("Sexe", ["M", "F"], index=0 if def_sex == "M" else 1, key=f"side_sex_{i}")
        employees.append({"name": name, "sex": sex})
    
    st.divider()
    # Jours fériés (Impacte Mme Mliyani)
    with st.expander("Jours Fériés (les femmes)", expanded=False):
        holidays = st.multiselect(
            "Sélectionner les jours fériés:",
            options=range(1, num_days + 1),
            default=[],
            help="Ces jours impactent uniquement les jours de travail de Mme Mliyani."
        )

# --- INTERFACE PRINCIPALE ---
col_c1, col_c2 = st.columns([2, 1])

personal_leaves = {}

with col_c1:
    st.header("📅 Congés")
    tabs = st.tabs([f"📍 {emp['name']}" for emp in employees])
    
    for i, emp in enumerate(employees):
        with tabs[i]:
            st.info(f"Configuration des absences pour **{emp['name']}** ({emp['sex']})")
            p_leaves = st.multiselect("Jours de repos / Congés :", range(1, num_days + 1), key=f"leaves_{i}")
            personal_leaves[emp['name']] = p_leaves

with col_c2:
    st.header("⏳ Continuité")
    # Historique de continuité
    history_input = {}
    with st.expander("Historique (3 derniers jours)", expanded=False):
        for emp in employees:
            st.markdown(f"**{emp['name']}**")
            h_cols = st.columns(3)
            h3 = h_cols[0].selectbox("J-3", ["REP", "DAY", "NIGHT"], key=f"h3_{emp['name']}")
            h2 = h_cols[1].selectbox("J-2", ["REP", "DAY", "NIGHT"], key=f"h2_{emp['name']}")
            h1 = h_cols[2].selectbox("J-1", ["REP", "DAY", "NIGHT"], key=f"h1_{emp['name']}")
            history_input[emp['name']] = [h3, h2, h1]

# Fusion des congés : Uniquement les congés personnels
leaves = personal_leaves.copy()

st.divider()

# --- GÉNÉRATION ---
if st.button("🚀 Générer le Planning Optimisé", type="primary", width='stretch'):
    with st.spinner("L'application de Abdennour Ryahi calcule la meilleure solution..."):
        try:
            params = {"holidays": holidays, "history": history_input}
            df_result = generate_schedule(year, month, employees, leaves, params)
            
            if df_result is not None:
                st.success("✅ Planning généré avec succès !")
                
                # --- DASHBOARD ---
                st.header("📊 Équité & Statistiques")
                
                # Couleurs
                AGENT_COLORS = ["#E8F5E9", "#FFF3E0", "#E1F5FE", "#F3E5F5", "#FBE9E7", "#EFEBE9", "#F1F8E9", "#FFFDE7"]
                text_colors = ["#2E7D32", "#EF6C00", "#0277BD", "#7B1FA2", "#D84315", "#4E342E", "#558B2F", "#F9A825"]
                color_map = {emp['name']: (AGENT_COLORS[idx % 8], text_colors[idx % 8]) for idx, emp in enumerate(employees)}

                # Stats
                stats = []
                for emp in employees:
                    name = emp['name']
                    m_count = sum(1 for row in df_result["Matin"] if name in [n.strip() for n in str(row).split(",")])
                    n_count = sum(1 for row in df_result["Nuit"] if name in [n.strip() for n in str(row).split(",")])
                    total = m_count + n_count
                    avail = num_days - len(leaves.get(name, []))
                    charge = (total / avail * 100) if avail > 0 else 0
                    stats.append({
                        "Agent": name, "Matins": m_count, "Nuits": n_count, "Total": total, 
                        "Charge %": round(charge, 1)
                    })
                df_stats = pd.DataFrame(stats)
                
                st.dataframe(df_stats, hide_index=True, width='stretch')
                st.bar_chart(df_stats.set_index("Agent")[["Matins", "Nuits"]], color=["#ffaa00", "#5555ff"])

                # --- TABS FOR VIEWS ---
                st.header("📅 Planning")
                
                tab_global, tab_agent = st.tabs(["Vue Globale", "Vue par Agent"])
                
                with tab_global:
                    def colorize(cell):
                        if not isinstance(cell, str) or "," not in cell: return cell
                        names = [n.strip() for n in cell.split(",")]
                        spans = []
                        for n in names:
                            bg, fg = color_map.get(n, ("#ddd", "#333"))
                            spans.append(f'<span style="background-color:{bg}; color:{fg}; padding:2px 6px; border-radius:4px; font-weight:bold; margin-right:2px;">{n}</span>')
                        return " ".join(spans)

                    df_styled = df_result.copy()
                    df_styled["Matin"] = df_styled["Matin"].apply(colorize)
                    df_styled["Nuit"] = df_styled["Nuit"].apply(colorize)
                    st.write(df_styled.to_html(escape=False, index=False), unsafe_allow_html=True)
                    
                    st.divider()
                    excel_data = generate_excel(df_result)
                    st.download_button("📥 Télécharger Excel Global", excel_data, f"Planning_Global_{month}.xlsx", width='stretch')
                
                with tab_agent:
                    # Helper function for pivot view
                    def transform_schedule_to_pivot(df, emp_list):
                        days = sorted(df["Jour"].unique())
                        agent_names = [e["name"] for e in emp_list]
                        pivot_df = pd.DataFrame("", index=agent_names, columns=days)
                        for _, row in df.iterrows():
                            day = row["Jour"]
                            for agent in row["Matin"].split(","):
                                agent = agent.strip()
                                if agent in pivot_df.index: pivot_df.at[agent, day] = "J"
                            for agent in row["Nuit"].split(","):
                                agent = agent.strip()
                                if agent in pivot_df.index: pivot_df.at[agent, day] = "N"
                        return pivot_df

                    df_pivot = transform_schedule_to_pivot(df_result, employees)
                    
                    def style_pivot(val):
                        if val == "J": return 'background-color: #FFF9C4; color: #F57F17; font-weight: bold; text-align: center;'
                        elif val == "N": return 'background-color: #E8EAF6; color: #3F51B5; font-weight: bold; text-align: center;'
                        return 'text-align: center;'

                    st.dataframe(df_pivot.style.map(style_pivot), width='stretch')
                    
                    # Download Agent Pivot Excel
                    import io
                    towrap = io.BytesIO()
                    df_pivot.to_excel(towrap, index=True)
                    st.download_button("📥 Télécharger Excel par Agent", towrap.getvalue(), f"Planning_Agents_{month}.xlsx", width='stretch')
            else:
                st.error("⚠️ Aucune solution trouvée.")
        except Exception as e:
            st.error(f"Erreur: {e}")

