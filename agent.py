# agent.py
"""
Multi-agent orchestrator for MedAgent.
- Loads GOOGLE_API_KEY from .env
- Uses google.generativeai (Gemini) for agent responses
- Implements short-term memory per agent and persistent logs saved to diagnosis_logs/
- Agents: GeneralPhysician, Cardiologist, Pulmonologist, Psychologist, Neurologist, MultidisciplinaryTeam
"""

import os
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not set in .env")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# persistent logs directory
LOG_DIR = Path("diagnosis_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Small in-memory per-agent short-term memory implementation
class MedicalAgent:
    def __init__(self, name: str, role_prompt: str):
        self.name = name
        self.role_prompt = role_prompt.strip()
        self.memory = []  # short-term memory (list of strings)

    def _build_prompt(self, report_text: str):
        # Compose prompt including short-term memory (most recent items)
        memory_text = ""
        if self.memory:
            # include only last few entries to keep prompt short
            memory_text = "\n\nShort-term memory (latest):\n" + "\n".join(self.memory[-6:])
        prompt = (
            f"You are a medical specialist: {self.name}.\n"
            f"{self.role_prompt}\n\n"
            f"Patient report and context:\n{report_text}\n\n"
            f"{memory_text}\n\n"
            f"Provide a clear concise analysis, key findings, recommended next steps, tests (if any), and urgency level.\n"
        )
        return prompt

    def analyze(self, report_text: str) -> str:
        prompt = self._build_prompt(report_text)
        # Call Gemini
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Save into short-term memory (we store agent name + brief summary)
        # For memory, keep a one-line summary (first 240 chars) to avoid long contexts
        summary_line = f"[{datetime.datetime.now().isoformat()}] {self.name} summary: {text[:240].replace('\\n', ' ')}"
        self.memory.append(summary_line)
        # Cap memory to last 50 entries
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]
        return text

# Orchestrator class
class MedicalOrchestrator:
    def __init__(self):
        # Initialize agents with tailored role prompts
        self.agents = {
            "GeneralPhysician": MedicalAgent(
                "General Physician",
                "Perform triage: determine likely systems affected (cardiac, neuro, pulmonary, psychiatric, general). Recommend which specialists should review. Keep answer short and explicit."
            ),
            "Cardiologist": MedicalAgent(
                "Cardiologist",
                "Focus on cardiovascular causes: evaluate chest pain, palpitations, dyspnea, syncope. Recommend tests such as ECG, cardiac enzymes, echo."
            ),
            "Pulmonologist": MedicalAgent(
                "Pulmonologist",
                "Focus on respiratory causes: evaluate cough, breathlessness, wheeze, hemoptysis. Recommend chest X-ray, spirometry, CT or labs if needed."
            ),
            "Psychologist": MedicalAgent(
                "Psychologist",
                "Focus on mental health aspects: assess anxiety, depression, somatic symptoms, cognitive change. Suggest screening and red flags for urgent psychiatric referral."
            ),
            "Neurologist": MedicalAgent(
                "Neurologist",
                "Focus on neurological causes: evaluate headache, dizziness, focal deficits, seizures. Suggest neuro exam elements and imaging if needed."
            ),
            "MultidisciplinaryTeam": MedicalAgent(
                "Multidisciplinary Team",
                "Synthesize the specialists' outputs into a single, clear final diagnosis and action plan suitable for a clinician. Provide a short summary for patient notes and recommended next steps."
            ),
        }
        # A main conversation history (persistent for orchestrator) used for logging
        self.main_conversation_history = []

    def run_full_workflow(self, report_text: str):
        """
        Run: GP -> specialists -> multidisciplinary synthesis.
        Save detailed log to diagnosis_logs/.
        Return dict of outputs.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"diag_{timestamp}"

        # 1) General Physician triage
        gp_out = self.agents["GeneralPhysician"].analyze(report_text)
        self.main_conversation_history.append({"agent":"GeneralPhysician","text":gp_out,"time":timestamp})

        # 2) Decide which specialists to call.
        # For thoroughness and to match PDF, we will call all specialists but we could filter down later.
        cardio_out = self.agents["Cardiologist"].analyze(report_text)
        self.main_conversation_history.append({"agent":"Cardiologist","text":cardio_out,"time":timestamp})

        pulmon_out = self.agents["Pulmonologist"].analyze(report_text)
        self.main_conversation_history.append({"agent":"Pulmonologist","text":pulmon_out,"time":timestamp})

        psych_out = self.agents["Psychologist"].analyze(report_text)
        self.main_conversation_history.append({"agent":"Psychologist","text":psych_out,"time":timestamp})

        neuro_out = self.agents["Neurologist"].analyze(report_text)
        self.main_conversation_history.append({"agent":"Neurologist","text":neuro_out,"time":timestamp})

        # 3) Multidisciplinary synthesis (use specialist outputs)
        # Build synthesis prompt including specialists' outputs succinctly
        synth_input = (
            f"Patient report:\n{report_text}\n\n"
            f"GeneralPhysician:\n{gp_out}\n\n"
            f"Cardiologist:\n{cardio_out}\n\n"
            f"Pulmonologist:\n{pulmon_out}\n\n"
            f"Psychologist:\n{psych_out}\n\n"
            f"Neurologist:\n{neuro_out}\n\n"
            "Combine the above specialist notes into a concise final diagnosis, recommended tests, urgency, and next steps."
        )
        final_out = self.agents["MultidisciplinaryTeam"].analyze(synth_input)
        self.main_conversation_history.append({"agent":"MultidisciplinaryTeam","text":final_out,"time":timestamp})

        # 4) Persist logs (json + txt)
        log = {
            "session_id": session_id,
            "timestamp": timestamp,
            "report_text": report_text,
            "outputs": {
                "GeneralPhysician": gp_out,
                "Cardiologist": cardio_out,
                "Pulmonologist": pulmon_out,
                "Psychologist": psych_out,
                "Neurologist": neuro_out,
                "Final": final_out
            },
            "conversation_history": self.main_conversation_history[-100:]  # last 100 entries
        }

        json_path = LOG_DIR / f"{session_id}.json"
        txt_path = LOG_DIR / f"{session_id}.txt"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(log, jf, ensure_ascii=False, indent=2)
        with open(txt_path, "w", encoding="utf-8") as tf:
            tf.write("=== MedAgent Diagnosis Log ===\n")
            tf.write(f"Session ID: {session_id}\nTimestamp: {timestamp}\n\n")
            tf.write("=== Report ===\n")
            tf.write(report_text + "\n\n")
            for k, v in log["outputs"].items():
                tf.write(f"--- {k} ---\n")
                tf.write(v + "\n\n")

        # Return outputs to UI
        return {
            "session_id": session_id,
            "timestamp": timestamp,
            "gp": gp_out,
            "cardio": cardio_out,
            "pulmo": pulmon_out,
            "psych": psych_out,
            "neuro": neuro_out,
            "final": final_out,
            "log_json": str(json_path),
            "log_txt": str(txt_path)
        }

    def ask_followup(self, agent_key: str, followup_question: str, context_text: str):
        """
        Ask a follow-up question to a specific agent or to the final combined output.
        agent_key: one of 'gp', 'cardio', 'pulmo', 'psych', 'neuro', 'final'
        context_text: the base text to feed (report or agent output)
        """
        name_map = {
            "gp": "General Physician",
            "cardio": "Cardiologist",
            "pulmo": "Pulmonologist",
            "psych": "Psychologist",
            "neuro": "Neurologist",
            "final": "Multidisciplinary Team"
        }
        agent_name = name_map.get(agent_key, "Multidisciplinary Team")
        prompt = (
            f"You are {agent_name}. Based on the following context, answer the user's question succinctly.\n\n"
            f"Context:\n{context_text}\n\n"
            f"User question: {followup_question}\n\n"
            f"Provide a clear clinical-style answer and recommended next steps if applicable."
        )
        response = model.generate_content(prompt)
        return response.text.strip()


# Provide a simple singleton orchestrator for UI import
_orch = MedicalOrchestrator()

def orchestrator_agent(report_text: str):
    """Wrapper for Streamlit to call a single function."""
    return (
        _orch.run_full_workflow(report_text)["gp"],
        _orch.run_full_workflow(report_text)["cardio"],  # note: run_full_workflow called twice? better to call once - fixed below
        _orch.run_full_workflow(report_text)["neuro"]
    )

# Better wrapper that calls once and returns full dict
def orchestrator_run_full(report_text: str):
    return _orch.run_full_workflow(report_text)

def ask_followup(agent_key: str, followup_question: str, context_text: str):
    return _orch.ask_followup(agent_key, followup_question, context_text)
