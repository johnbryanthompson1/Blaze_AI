 Blaze AI

A locally hosted LLM teaching assistant for K-12 schools. No data leaves the building.

---

## What it is

Blaze AI is a school-facing AI assistant built on open-source tools and running entirely on local hardware. Teachers can ask it questions about curriculum, school policy, and course content — and get answers grounded in actual school documents rather than the open internet.

The motivating problem was straightforward: commercial AI tools like ChatGPT raise real data privacy concerns in school environments, and the subscription costs add up fast. Blaze AI is an attempt to build something that works well enough for daily teacher use, costs almost nothing to run after the initial hardware, and keeps everything on-premises.

---

## Stack

- **Ollama** — local model serving
- **Open WebUI** — browser-based chat interface with built-in user management
- **Docker** — containerized deployment
- **Microsoft Phi-4** — the current model (upgraded from Mistral 7B during Stage 1)
- **RAG knowledge base** — school documents loaded via Open WebUI's document store

---

## Knowledge Base

The RAG pipeline is populated with manually downloaded documents:

- Concordia curriculum atlas (Atlas Curriculum)
- School policies and employee handbook
- Course materials pulled from Canvas via a custom API script

When a teacher asks a question, the system retrieves relevant document chunks before generating a response. This keeps answers grounded in what the school actually says rather than what the model guesses.

---

## Architecture

```
Teacher (browser) → Open WebUI → Ollama → Phi-4
                         ↑
                   RAG document store
                   (school docs, Canvas content)
```

Everything runs on a Mac Mini M4 Pro on the school's local network. Teachers connect via the Mac Mini's local IP address. No internet connection required during use, no data transmitted externally.

---

## Deployment stages

**Stage 1 (complete):** Proof of concept on a MacBook Air (8GB M3). Mistral 7B, single-user, used in John's classes only.

**Stage 2 (current):** Mac Mini M4 Pro, Phi-4, five-teacher pilot. User accounts managed manually through Open WebUI's admin panel. Open registration disabled.

**Stage 3 (planned):** Broader high school deployment, larger model, possible Canvas LTI integration.

---

## Security and privacy

- No API calls to external services during inference
- No user data stored outside the school network
- Open WebUI access restricted to manually created accounts
- Documents are loaded manually by the admin — no automated sync with external systems during the pilot

This architecture was designed partly in response to administrator concerns about data handling. The honest answer is that local deployment eliminates the largest category of risk (data leaving the building) while shifting responsibility for access control to whoever manages the hardware.

---

## Canvas API script

The repo includes a Python script that connects to the Canvas LMS REST API and pulls course assignments and materials for a given teacher's courses. Output is formatted for ingestion into Open WebUI's RAG document store.

To use it, you need a Canvas API token with read access to your courses. The script does not write to Canvas.

---

## Why Phi-4

Phi-4 is a small language model from Microsoft that performs well on instruction-following tasks at a fraction of the compute cost of larger models. On the Mac Mini M4 Pro with 48GB unified memory, it runs comfortably with response times that are reasonable for classroom use. The tradeoff compared to GPT-4 class models is noticeable on complex reasoning tasks, but for policy lookups, curriculum questions, and lesson planning support it's sufficient.

---

## Setup

Full setup requires Ollama, Docker, and Open WebUI. The general sequence:

1. Install Ollama and pull your model (`ollama pull phi4`)
2. Deploy Open WebUI via Docker
3. Connect Open WebUI to Ollama (`http://host.docker.internal:11434`)
4. Upload school documents to the RAG knowledge base
5. Create user accounts and disable open registration

Detailed setup notes are in `SETUP.md`.

---

## Author

John Thompson — high school English teacher, PhD (Texas Tech).
Concordia International School Shanghai.

This project is part of a broader interest in building AI infrastructure that schools can actually own and control.

---

MIT License
