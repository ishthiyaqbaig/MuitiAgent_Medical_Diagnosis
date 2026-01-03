
# 🧑‍⚕️ MultiAgent Medical Diagnosis

A prototype framework that uses **LangChain** and **Streamlit** to orchestrate multiple AI agents for assisting in medical diagnosis.  
This project demonstrates how specialized agents (e.g., symptom analyzer, knowledge retriever, treatment suggester) can collaborate to provide structured diagnostic insights.

---

## 🚀 Features
- **Multi-Agent Orchestration**: Each agent has a defined role (symptom analysis, medical knowledge retrieval, recommendation).
- **LangChain Integration**: Chains and tools manage reasoning and context across agents.
- **Streamlit UI**: Simple, interactive web interface for entering patient symptoms and viewing diagnostic outputs.
- **Extensible Design**: Add or modify agents for different domains (e.g., cardiology, dermatology).
- **Educational Use**: Intended for research and demonstration, **not for real medical advice**.

---

## ⚙️ Setup Instructions  

### 1️⃣ Clone the Repository  

git clone https://github.com/YOUR-USERNAME/MedAgentApp.git
cd MedAgentApp

2️⃣ Create and Activate a Virtual Environment

python -m venv venv
venv\Scripts\activate        # For Windows

# or
source venv/bin/activate     # For macOS/Linux

3️⃣ Install Required Packages

pip install -r requirements.txt

4️⃣ Add Your Gemini API Key Securely

Create a file named .env in the same folder as app.py and add your Gemini API key:

GOOGLE_API_KEY=your_actual_api_key_here

⚠️ Never upload your .env file to GitHub — it’s already protected in .gitignore.

5️⃣ Run the Application

streamlit run app.py

Now open your browser and visit 👉 http://localhost:8501

🧰 Project Structure
```
📁 MEDICAL/
├── app.py                # 🎯 Main Streamlit web app
├── agent.py              # 🤖 Gemini AI logic & multi-agent analysis
├── .env                  # 🔑 API key (secure, ignored by Git)
├── .gitignore            # 🚫 Prevents secret uploads
├── requirements.txt      # 📦 All dependencies
├── diagnosis_logs/       # 📄 AI-generated reports (PDF)
├── diagnosis_logs_json/  # 🧠 JSON logs per user
└── vector_db/            # ⚙️ Optional embeddings / cache
```
---

🧾 Example Output

Smooth, responsive Streamlit UI

Sidebar navigation for Report & Analyze, Follow-up, and Download Report

Real-time AI agent animation (“🧠 Agent analyzing...”)

Downloadable PDF reports

Stored analysis history for personalized follow-ups

---

🚀 Future Enhancements

🧬 Integration with wearable devices (Fitbit, Apple Health)

📊 Symptom tracking dashboard

🌍 Multi-language report analysis

🧠 Offline AI diagnosis (local LLM support)

🕵️ Doctor Portal for AI-reviewed case histories

---
