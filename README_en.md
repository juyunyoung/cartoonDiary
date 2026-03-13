# 🎨 Cartoon Diary

An intelligent diary application that transforms your daily reflections into a 4-panel cartoon using AI (AWS Nova). It features LangGraph-based agent orchestration and SSE (Server-Sent Events) for real-time state tracking.

## 🌟 Key Features
- **Diary Writing & Character Customization**: Consistent character generation based on user profile (gender, age, etc.).
- **Automated 4-Panel Comic Generation**: Analyzes diary content to compose storyboards and generate high-quality images.
- **Real-time Progress Tracking**: Live updates of the generation stages via SSE (Server-Sent Events).
- **Quality Assurance Loop**: Multi-modal AI Visual QA for quality inspection and automated retries.
- **Multi-language Support**: Full support for both Korean and English.

---

## 📐 Architecture

### 1. System Architecture
![system_architecture](system_architecture.png)

### 2. AI Orchestration Flow
![ai orchestration](ai_archestration.png)

---

## 🏗️ Project Structure

### 1. Backend (`cdiary-be`) - **AI Engine & API**
Built with FastAPI, orchestrating complex AI workflows using LangGraph.

- **Core Technologies**:
  - **Framework**: FastAPI (Python 3.12+)
  - **AI Orchestration**: LangGraph, LangChain
  - **LLM/LMM**: AWS Bedrock (Nova Canvas, Nova Text, Claude 3.5)
  - **Database**: SQLite (SQLAlchemy)
  - **Storage**: AWS S3 (Stores images and reference data)
- **How to Run**:
  ```bash
  cd cdiary-be
  python3 -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate
  pip install -r requirements.txt
  python main.py
  ```

### 2. Frontend (`cdiary-fe`) - **Interactive UI**
Highly responsive and visually stunning UI powered by Vite and React.

- **Core Technologies**:
  - **Framework**: React 18 (TypeScript)
  - **Build Tool**: Vite
  - **Styling**: Tailwind CSS
  - **Icons**: Lucide React
  - **State Management**: React Context API
- **How to Run**:
  ```bash
  cd cdiary-fe
  npm install
  npm run dev
  ```

---

## 🚀 Deep Dive: Core Mechanisms

### 📡 SSE (Server-Sent Events) Architecture
When a user requests a diary generation, the backend immediately returns a `jobId`. The frontend then subscribes to real-time status updates via SSE.

- **Endpoint**: `GET /api/jobs/stream?token=...`
- **Workflow**:
  1. Client (`EventSource`) maintains a persistent connection with the backend.
  2. Backend (Python Async Generator) serializes the in-memory `JOBS` state every second.
  3. Frontend (`DiaryList.tsx`) parses the incoming data to update progress bars and step-by-step status text.
  4. Automatically transitions to the result screen when the state becomes `DONE`.

### 🤖 AI Orchestration (LangGraph Flow)
Instead of simple prompt execution, it utilizes a state-based agent workflow to ensure high-quality comic production.

1.  **Plan Storyboard**: Analyzes the diary to create a 4-panel storyboard including summaries, emotions, scene descriptions, and dialogues.
2.  **Build Prompts**: Constructs image generation prompts for each panel, applying character consistency and style guidelines.
3.  **Generate Images**: Calls AWS Nova Canvas to generate images, using previous panels as references to maintain visual continuity.
4.  **Visual QA (Critic)**: Multi-modal models inspect whether the generated images align with the storyboard's intent.
5.  **Retry Loop**: Upon QA failure, analyzes the failure reason, adjusts the prompt, and retries the generation (within a set limit).
6.  **Done**: Finalizes the artifacts and stores them in the database upon successful completion.

---

## ☁️ Deployment (AWS)

- **Frontend**: AWS Amplify (Static Web Hosting)
- **Backend**: AWS App Runner (Containerized Python Server)
- **Storage**: Amazon S3 (Serving generated images)
- **AI**: AWS Bedrock (Requires access to the Nova model family)
