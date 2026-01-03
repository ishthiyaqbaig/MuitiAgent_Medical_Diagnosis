# app.py
import streamlit as st
from agent import orchestrator_run_full, ask_followup
from fpdf import FPDF
import datetime
import os

st.set_page_config(page_title="MedAgent Multi-Agent Assistant", layout="wide")

# ---- CSS (ensure readable text on cards) ----
st.markdown("""
<style>
body { background: linear-gradient(135deg, #f3f8ff 0%, #ffffff 100%); color: #012233; font-family: 'Segoe UI', sans-serif; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0066cc, #66ccff); color:white; font-weight:700; font-size:1.15em; }
.sidebar-title { font-size:1.7em; padding-bottom:10px; }
.card { background: #ffffff; color: #012233; border-radius:12px; padding:18px; box-shadow: 0 4px 18px rgba(0,0,0,0.08); margin-bottom:12px; }
.card-alt { background: #f0f8ff; color: #012233; border-radius:12px; padding:18px; box-shadow: 0 4px 18px rgba(0,0,0,0.06); margin-bottom:12px; }
.final { background: #e6f0ff; color: #001f3f; border-radius:12px; padding:18px; box-shadow: 0 5px 20px rgba(0,0,0,0.09); margin-bottom:12px; font-weight:600; }
.small { font-size:0.9rem; color:#334455; }
</style>
""", unsafe_allow_html=True)

# ---- Sidebar and navigation ----
st.sidebar.markdown("<div class='sidebar-title'>🏥 MedAgent Multi-Agent</div>", unsafe_allow_html=True)
st.sidebar.markdown("Multi-agent medical diagnosis — General Physician + Cardiologist + Pulmonologist + Psychologist + Neurologist + Multidisciplinary team")

page = st.sidebar.radio("Navigation", ["Report & Analyze", "Follow-up Questions", "Download Report", "Recent Logs"])

# ---- Session state ----
if "last_result" not in st.session_state:
    st.session_state.last_result = None  # store dict returned from orchestrator
if "recent_sessions" not in st.session_state:
    st.session_state.recent_sessions = []  # list of session dicts (session_id, timestamp, json_path, text_path)

# ---- Page: Report & Analyze ----
if page == "Report & Analyze":
    st.title("Multi-Agent Medical Diagnosis")
    st.markdown("Enter patient details and symptoms. The system will run multiple specialist agents and return a synthesized diagnosis.")

    col1, col2 = st.columns([2,1])
    with col1:
        patient_name = st.text_input("Patient name")
        patient_age = st.number_input("Age", min_value=0, max_value=120, value=30)
        patient_gender = st.selectbox("Gender", ["Select","Male","Female","Other"])
        symptoms = st.text_area("Symptoms / History", height=160, placeholder="Describe symptoms, onset, duration, severity, red flags...")
    with col2:
        st.markdown("**Quick tips**")
        st.markdown("- Be concise but include onset, progression, and red flags.")
        st.markdown("- Example: chest pain radiating to left arm, worse on exertion, 2 days.")
        st.markdown("- Use the Follow-up page to ask more questions about results.")

    if st.button("Run Multi-Agent Analysis"):
        if not patient_name or patient_gender == "Select" or not symptoms.strip():
            st.warning("Please complete the form (name, gender, and symptoms).")
        else:
            report_text = f"Patient: {patient_name}, Age: {patient_age}, Gender: {patient_gender}. Symptoms: {symptoms}"
            st.info("🧠 Running multi-agent analysis — this may take a few seconds.")
            try:
                result = orchestrator_run_full(report_text)
                # result includes gp, cardio, pulmo, psych, neuro, final, session ids and log paths
                st.session_state.last_result = result
                st.session_state.recent_sessions.insert(0, {
                    "session_id": result["session_id"],
                    "timestamp": result["timestamp"],
                    "json": result["log_json"],
                    "txt": result["log_txt"]
                })
                st.success("Analysis complete — results below.")
            except Exception as e:
                st.error(f"Error running agents: {e}")

    # show result cards
    if st.session_state.last_result:
        res = st.session_state.last_result
        st.markdown(f"<div class='card'><strong>Patient Report</strong><div class='small'>{res.get('session_id')} • {res.get('timestamp')}</div><p>{res.get('report_text','')}</p></div>", unsafe_allow_html=True)
        st.markdown("<h4>General Physician</h4>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>{res['gp']}</div>", unsafe_allow_html=True)

        st.markdown("<h4>Cardiologist</h4>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>{res['cardio']}</div>", unsafe_allow_html=True)

        st.markdown("<h4>Pulmonologist</h4>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>{res['pulmo']}</div>", unsafe_allow_html=True)

        st.markdown("<h4>Psychologist</h4>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>{res['psych']}</div>", unsafe_allow_html=True)

        st.markdown("<h4>Neurologist</h4>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'>{res['neuro']}</div>", unsafe_allow_html=True)

        st.markdown("<h4>Final Multidisciplinary Diagnosis</h4>", unsafe_allow_html=True)
        st.markdown(f"<div class='final'>{res['final']}</div>", unsafe_allow_html=True)

# ---- Page: Follow-up Questions ----
elif page == "Follow-up Questions":
    st.title("Follow-up Questions")
    if not st.session_state.last_result:
        st.info("Run an analysis first on the 'Report & Analyze' page.")
    else:
        res = st.session_state.last_result
        agent_choice = st.selectbox("Ask which agent?", ["final","gp","cardio","pulmo","psych","neuro"], format_func=lambda x: {"final":"Multidisciplinary (final)","gp":"General Physician","cardio":"Cardiologist","pulmo":"Pulmonologist","psych":"Psychologist","neuro":"Neurologist"}[x])
        question = st.text_input("Type your follow-up question")
        if st.button("Ask"):
            if not question.strip():
                st.warning("Please type a question.")
            else:
                st.info("🧠 Agent answering...")
                context = res['final'] if agent_choice == "final" else res[{"gp":"gp","cardio":"cardio","pulmo":"pulmo","psych":"psych","neuro":"neuro"}[agent_choice]]
                try:
                    ans = ask_followup(agent_choice, question, context)
                    st.markdown(f"<div class='card-alt'><strong>Answer from {agent_choice.upper()}</strong><p>{ans}</p></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Follow-up error: {e}")

# ---- Page: Download Report ----
elif page == "Download Report":
    st.title("Download Multi-Agent Report")
    if not st.session_state.last_result:
        st.info("No result to download yet.")
    else:
        res = st.session_state.last_result
        if st.button("Generate & Download PDF"):
            # Create PDF (strip emojis for safety)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, txt="MedAgent Multi-Agent Diagnosis Report", ln=True, align="C")
            pdf.ln(6)
            pdf.set_font("Arial", size=11)

            # safe strings
            def safe(s):
                return s.encode('latin-1', 'ignore').decode('latin-1')

            pdf.multi_cell(0, 8, safe(f"Session: {res['session_id']}  |  {res['timestamp']}"))
            pdf.ln(4)
            pdf.multi_cell(0, 8, safe("Patient Report:\n" + res.get("report_text", "")))
            pdf.ln(3)
            pdf.multi_cell(0, 8, safe("=== General Physician ===\n" + res['gp']))
            pdf.ln(2)
            pdf.multi_cell(0, 8, safe("=== Cardiologist ===\n" + res['cardio']))
            pdf.ln(2)
            pdf.multi_cell(0, 8, safe("=== Pulmonologist ===\n" + res['pulmo']))
            pdf.ln(2)
            pdf.multi_cell(0, 8, safe("=== Psychologist ===\n" + res['psych']))
            pdf.ln(2)
            pdf.multi_cell(0, 8, safe("=== Neurologist ===\n" + res['neuro']))
            pdf.ln(3)
            pdf.multi_cell(0, 8, safe("=== Final Diagnosis ===\n" + res['final']))

            filename = f"MedAgent_{res['session_id']}.pdf"
            pdf.output(filename)
            with open(filename, "rb") as f:
                st.download_button("Download PDF", data=f, file_name=filename, mime="application/pdf")

# ---- Page: Recent Logs ----
# ---- Page: Recent Logs ----
elif page == "Recent Logs":
    st.title("Recent Diagnosis Logs")

    if not st.session_state.recent_sessions:
        st.info("No previous sessions in this browser session.")
        st.warning("Please run an analysis first to generate reports before downloading.")
    else:
        for s in st.session_state.recent_sessions:
            st.markdown(f"**Session ID:** {s['session_id']}  |  **Timestamp:** {s['timestamp']}")
            st.info("TXT and PDF are recommended for easy reading. JSON is for developer use.")
            
            col1, col2, col3 = st.columns([1,1,1])
            
            # TXT download
            with col1:
                if os.path.exists(s['txt']):
                    with open(s['txt'], "rb") as ftxt:
                        st.download_button(
                            label="Download TXT (readable)",
                            data=ftxt,
                            file_name=f"{s['session_id']}.txt",
                            mime="text/plain"
                        )
                else:
                    st.markdown("TXT not available.")

            # JSON download
            with col2:
                if os.path.exists(s['json']):
                    with open(s['json'], "rb") as fjson:
                        st.download_button(
                            label="Download JSON (developer)",
                            data=fjson,
                            file_name=f"{s['session_id']}.json",
                            mime="application/json"
                        )
                else:
                    st.markdown("JSON not available.")

            # PDF download
            pdf_filename = f"MedAgent_{s['session_id']}.pdf"
            with col3:
                if os.path.exists(pdf_filename):
                    with open(pdf_filename, "rb") as fpdf:
                        st.download_button(
                            label="Download PDF (formatted)",
                            data=fpdf,
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )
                else:
                    st.markdown("PDF not available.")

            st.markdown("---")  # separator between sessions
