# 🏛️ LLM Council

![LLM Council Header](header.jpg)

**LLM Council** is a powerful decision-making and problem-solving framework that leverages the collective intelligence of multiple Large Language Models (LLMs). Instead of trusting a single model, the Council orchestrates a multi-stage process where models provide independent opinions, critique each other, and arrive at a synthesized final answer.

## 🌟 Key Features

*   **The 3-Stage Process:** Orchestrates a rigorous flow of independent thought, peer review, and final synthesis.
*   **Dynamic Council Modes:** Specialized operating modes like *Adversarial (The Trial)*, *Temporal (Past to Future)*, *Multiverse*, and *Socratic* that dynamically assign expert personas to models.
*   **Rebuttal Round (Stage 2.5):** Models see critiques of their work and are given a chance to refine their answers before the final synthesis.
*   **Universal Model Support:** Access hundreds of LLMs (GPT-4o, Claude 3.5, Gemini 3, Grok, DeepSeek, etc.) via a single OpenRouter integration.
*   **Cost & Token Transparency:** Real-time pre-flight cost estimation while you type, and exact actual spending tracking per message and session.
*   **Modern Chat Interface:** A sleek, reactive UI with tabbed views for inspecting individual model thinking and peer rankings.
*   **Conversation Management:** Full history support with easy export (Markdown, JSON, HTML) and session cleanup.

## ⚙️ How it Works: The 3-Stage Orchestration

1.  **Stage 1: Independent Responses**
    Each council member is given the query independently. If a **Council Mode** is active, models are assigned specialized personas (e.g., a "Neuroscientist" or "Venture Capitalist") tailored to your specific problem.
2.  **Stage 2: Peer Review & Ranking**
    The models review each other's responses anonymously. They provide detailed critiques and rank the answers from best to worst.
3.  **Stage 2.5: The Rebuttal**
    Models receive the peer feedback directed at them and are given one opportunity to update and "fix" their original answers based on valid critiques.
4.  **Stage 3: Final Synthesis**
    A designated **Chairman model** (assigned a synthesis-focused persona) reviews all original answers, peer rankings, and revised responses to produce a single, comprehensive, and objective final determination.

## 🎭 Council Modes

Beyond standard chat, you can summon specialized strategic frameworks:

*   **⚖️ Adversarial:** A legal stress-test with a Prosecutor, Defense, and Star Witness.
*   **⏳ Temporal:** Wisdom across time, featuring an Ancient Philosopher and a Sci-Fi Futurist.
*   **⚔️ RPG Party:** Balanced archetypes including The Tank (Risk), The Mage (Innovation), and The Rogue (Efficiency).
*   **🔍 Scale:** Analysis through different lenses, from Micro-detail to Cosmic-scale.
*   **🎭 Critics:** Specifically for perfecting outputs with a Harsh Editor and a competitive Rival.
*   **🧘 Socratic:** The council is forbidden from giving answers and will only ask deep, probing questions.
*   **🤖 Auto:** The AI analyzes your query and automatically chooses the most effective mode for you.

## 🚀 Getting Started

### 1. Prerequisites
*   [Python 3.10+](https://www.python.org/)
*   [Node.js & npm](https://nodejs.org/)
*   [uv](https://docs.astral.sh/uv/) (Recommended for lightning-fast Python management)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/cihanuygur/llm-council.git
cd llm-council

# Install backend dependencies
uv sync

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
OPENROUTER_API_KEY=your_openrouter_key_here
```
*Get your key at [openrouter.ai](https://openrouter.ai/).*

### 4. Running the App
The simplest way is to use the provided start script:
```bash
chmod +x start.sh
./start.sh
```
*This will start the FastAPI backend on port 8001 and the Vite frontend on port 5173.*

## 🛠️ Technical Stack

*   **Backend:** FastAPI (Python), Async Orchestration, httpx.
*   **Frontend:** React, Vite, React-Markdown, SSE (Server-Sent Events) for real-time streaming.
*   **Storage:** Local JSON-based persistent storage.
*   **Models:** Orchestrated via OpenRouter Chat Completions API.

## 📄 License
MIT License - feel free to use, modify, and build upon this framework.