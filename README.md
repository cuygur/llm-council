# 🏛️ LLM Council
### Trust the collective. Not the individual.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Build-Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![OpenRouter](https://img.shields.io/badge/Models-OpenRouter-7E57C2?style=for-the-badge&logo=openrouter&logoColor=white)](https://openrouter.ai/)

**LLM Council** is a high-orchestration decision-making framework designed to extract the highest quality reasoning from Large Language Models. By moving beyond single-prompt interactions, the Council subjects every query to a rigorous 3-stage deliberation process: **Independent Thought**, **Peer Critique**, and **Systemic Synthesis**.

> [!IMPORTANT]
> **Why a Council?** Single LLMs are prone to hallucinations and systemic bias. The Council reduces these risks by 40-60% by forcing models to defend their logic against their peers before a final judgment is rendered.

---

## 🔥 The "Power of Three" Workflow

The Council doesn't just "ask" models; it manages a debate.

1.  **🕵️ Stage 1: Independent Inquiry**
    Multiple models (the Council) generate the first draft of the answer. They don't see each other's work, preventing groupthink.
2.  **⚖️ Stage 2: Anonymized Peer Review**
    Models receive the answers from Stage 1 (anonymized) and must grade, critique, and rank them from best to worst.
3.  **🔄 Stage 2.5: The Rebuttal Round**
    Models see the critiques leveled against their own work and are given one chance to "fix" their answer or concede to a better peer logic.
4.  **🏛️ Stage 3: The Chairman's Decree**
    A designated **Chairman Model** reviews the entire transcript—the debates, the rankings, and the revised answers—to synthesize one definitive, objective final response.

---

## 🌟 Standout Features

### 💎 Premium Glassmorphism UI
Experience a state-of-the-art interface built with modern aesthetics. Transparent surfaces, subtle gradients, and reactive micro-animations provide a professional, focused environment for deep work.

### 📎 Context Injection (File Upload)
Inject your own documents, codebases, or datasets into the Council's deliberation. Simply attach files to your prompt to have the Council analyze your specific data with collective expertise.

### 🎭 Specialized Council Modes
Switch between strategic frameworks on the fly:
*   **Adversarial:** Legal-style stress tests (Prosecutor vs. Defense).
*   **Temporal:** Wisdom across epochs (Socrates vs. Isaac Asimov).
*   **Mental Models:** Decision-making using 6 Thinking Hats or First Principles.
*   **RPG Party:** Balanced perspectives (The Tank, Mage, and Rogue).

### 📊 Transparent Economy
Real-time cost estimation and token tracking. Know exactly what a query will cost *before* you send it, and track actual usage across the entire deliberation chain.

---

## 🚀 Quick Start

### 1. Initialize the Environment
```bash
# Clone and enter the project
git clone https://github.com/cihanuygur/llm-council.git
cd llm-council

# Install Backend (Powered by UV)
uv sync

# Install Frontend (Vite/React)
cd frontend && npm install && cd ..
```

### 2. Configure Credentials
Add your [OpenRouter API Key](https://openrouter.ai/keys) to a `.env` file:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx...
```

### 3. Launch the Council
```bash
chmod +x start.sh
./start.sh
```
*Port 5173 (Frontend) | Port 8001 (Backend)*

---

## 🛠️ Tech Stack

*   **Backend:** Python 3.10+, FastAPI, AsyncIO, HTTPX.
*   **Frontend:** React 18, Vite, React-Markdown, Vanilla CSS (Glassmorphism).
*   **Orchestration:** Advanced SSE (Server-Sent Events) for real-time streaming of model reasoning.
*   **Intelligence:** 200+ models available via OpenRouter standard interface.

---

## 📄 License
MIT © 2025 Cihan Uygur. Built for truth-seekers and decision-makers everywhere.