# MemoryDesk

MemoryDesk is an AI customer-support agent designed to demonstrate persistent memory using Hindsight.

## Problem

Traditional support chatbots often treat every conversation as a new conversation. Customers may have to repeat the same issue, preferences, and troubleshooting history.

## Solution

MemoryDesk uses Hindsight as a persistent memory layer. Relevant information from previous support conversations is stored and recalled when a customer returns.

### Core flow

Customer message -> Hindsight recall -> AI support agent -> Response -> Hindsight retain

## Features

- Persistent customer memory
- Context-aware support responses
- Recall of previous support conversations
- Customer-specific memory banks
- Streamlit interface
- Groq-powered LLM
- Visible memory panel for demonstrations

## Tech Stack

- Python
- Streamlit
- Hindsight
- Groq
- python-dotenv

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and add your Hindsight and Groq API keys.

### 4. Run

```bash
streamlit run app.py
```

## Hackathon Demonstration

The key demonstration is persistence across separate interactions.

Example:

1. Customer reports a payment problem and provides relevant context.
2. MemoryDesk stores the support conversation in Hindsight.
3. Later, the same customer reports a related problem.
4. MemoryDesk recalls the earlier interaction.
5. The agent uses that context to provide a more personalized response.

## Hindsight

Hindsight is the required memory layer for this project. The application uses:

- `retain` to store support conversation information.
- `recall` to retrieve relevant customer memories.

This makes memory central to the agent rather than a simple chat-history feature.
