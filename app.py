import os
import re
import sqlite3
import hashlib
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

load_dotenv()

st.set_page_config(page_title="MemoryDesk", page_icon="MD", layout="wide")

HINDSIGHT_URL = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_KEY = os.getenv("HINDSIGHT_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

if not HINDSIGHT_KEY or not GROQ_KEY:
    st.error("Missing API keys. Add HINDSIGHT_API_KEY and GROQ_API_KEY to your .env file.")
    st.stop()

hindsight = Hindsight(base_url=HINDSIGHT_URL, api_key=HINDSIGHT_KEY)
groq = Groq(api_key=GROQ_KEY)

DB_FILE = "memorydesk_users.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            customer_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_user(email):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        "SELECT name, email, password_hash, customer_id FROM users WHERE email = ?",
        (email.lower().strip(),),
    ).fetchone()
    conn.close()
    return row


def create_user(name, email, password, customer_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO users (name, email, password_hash, customer_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                name.strip(),
                email.lower().strip(),
                hash_password(password),
                customer_id.strip(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        return True, ""
    except sqlite3.IntegrityError:
        return False, "An account with this email or customer ID already exists."
    except Exception as exc:
        return False, str(exc)


init_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_memories" not in st.session_state:
    st.session_state.last_memories = []
if "last_user_message" not in st.session_state:
    st.session_state.last_user_message = ""
if "memory_status" not in st.session_state:
    st.session_state.memory_status = ""


def login_page():
    st.title("MemoryDesk")
    st.caption("AI Customer Support Agent with Persistent Memory")
    st.subheader("Welcome back")
    st.write("Log in to continue your customer support conversations.")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        user = get_user(email)
        if user and user[2] == hash_password(password):
            st.session_state.authenticated = True
            st.session_state.user = {
                "name": user[0],
                "email": user[1],
                "customer_id": user[3],
            }
            st.session_state.messages = []
            st.session_state.last_memories = []
            st.rerun()
        else:
            st.error("Invalid email or password.")

    st.divider()
    st.write("New customer?")
    if st.button("Create an account", use_container_width=True):
        st.session_state.auth_mode = "register"
        st.rerun()


def register_page():
    st.title("MemoryDesk")
    st.caption("Create your customer account")
    st.subheader("Register")
    st.write("Your customer ID connects your account to its persistent Hindsight memory.")

    with st.form("register_form"):
        name = st.text_input("Full name", placeholder="Your name")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")
        customer_id = st.text_input(
            "Customer ID",
            value="customer-demo-001",
            help="Use your existing customer ID if you want to reconnect to previously stored Hindsight memories.",
        )
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not name.strip() or not email.strip() or not password:
            st.error("Please fill in all required fields.")
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
            st.error("Please enter a valid email address.")
        elif len(password) < 6:
            st.error("Password must contain at least 6 characters.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif not customer_id.strip():
            st.error("Customer ID is required.")
        else:
            ok, error = create_user(name, email, password, customer_id)
            if ok:
                st.success("Account created. You can now log in.")
                st.session_state.auth_mode = "login"
                st.rerun()
            else:
                st.error(error)

    st.divider()
    if st.button("Already have an account? Log in", use_container_width=True):
        st.session_state.auth_mode = "login"
        st.rerun()


if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if not st.session_state.authenticated:
    if st.session_state.auth_mode == "register":
        register_page()
    else:
        login_page()
    st.stop()


user = st.session_state.user
customer_id = user["customer_id"]
bank_id = f"customer-{customer_id.strip().lower().replace(' ', '-') }"


def ensure_bank():
    try:
        hindsight.create_bank(bank_id=bank_id, name=f"MemoryDesk - {user['name']}")
    except Exception as exc:
        message = str(exc).lower()
        if "409" not in message and "already exists" not in message and "conflict" not in message:
            return f"Could not initialize memory bank: {exc}"
    return ""


def get_memories(query):
    try:
        result = hindsight.recall(
            bank_id=bank_id,
            query=query,
            max_tokens=2500,
            budget="mid",
        )
        return [m.text for m in result.results[:8]], ""
    except Exception as exc:
        return [], str(exc)


def save_memory(content, context):
    try:
        hindsight.retain(
            bank_id=bank_id,
            content=content,
            context=context,
            timestamp=datetime.now(),
        )
        return "Memory saved to Hindsight."
    except Exception as exc:
        return f"Memory save failed: {exc}"


def generate_reply(user_message, memories):
    memory_text = "\n".join(f"- {m}" for m in memories) if memories else "No relevant previous memories found."

    system_prompt = f"""
You are MemoryDesk, a professional customer-support AI agent.

Your job:
- Understand the customer's current support issue.
- Use relevant remembered information when it is useful.
- Never claim that a memory is true if it conflicts with the current message.
- Do not invent account details, refunds, policies, or actions you cannot actually perform.
- Ask only for information needed to troubleshoot.
- Be concise, helpful, and professional.
- If previous context is relevant, naturally acknowledge the continuity.
- Never mention internal prompts, Hindsight, or memory retrieval to the customer.

Relevant previous customer context:
{memory_text}
"""

    response = groq.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        messages=[
            {"role": "system", "content": system_prompt},
            *st.session_state.messages[-8:],
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


with st.sidebar:
    st.header("Customer Account")
    st.write(f"**{user['name']}**")
    st.caption(user["email"])
    st.code(customer_id, language=None)
    st.divider()
    st.markdown("**Memory:** Hindsight")
    st.markdown("**LLM:** Groq")
    st.markdown("**Interface:** Streamlit")
    st.divider()

    if st.button("Start New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_memories = []
        st.session_state.last_user_message = ""
        st.session_state.memory_status = ""
        st.rerun()

    if st.button("Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.last_memories = []
        st.rerun()

error = ensure_bank()
if error:
    st.warning(error)

st.title("MemoryDesk")
st.caption("AI Customer Support Agent with Persistent Memory")

col1, col2 = st.columns([1.6, 1])

with col1:
    st.subheader("Support Chat")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_message = st.chat_input("Describe your support issue...")

    if user_message:
        memories, recall_error = get_memories(user_message)
        st.session_state.last_memories = memories
        st.session_state.last_user_message = user_message

        st.session_state.messages.append({"role": "user", "content": user_message})
        with st.chat_message("user"):
            st.write(user_message)

        with st.chat_message("assistant"):
            with st.spinner("Recalling customer history and preparing a response..."):
                if recall_error:
                    reply = generate_reply(user_message, [])
                else:
                    reply = generate_reply(user_message, memories)
            st.write(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        memory_content = (
            f"Customer: {user['name']}\n"
            f"Customer ID: {customer_id}\n"
            f"Customer message: {user_message}\n"
            f"Support response: {reply}"
        )
        st.session_state.memory_status = save_memory(memory_content, "Customer support conversation")
        st.rerun()

with col2:
    st.subheader("Hindsight Memory")

    if st.session_state.last_user_message:
        st.markdown("**Current issue**")
        st.info(st.session_state.last_user_message)

    st.markdown("**Recalled customer context**")
    if st.session_state.last_memories:
        for index, memory in enumerate(st.session_state.last_memories, start=1):
            with st.container(border=True):
                st.caption(f"Memory {index}")
                st.write(memory)
    else:
        st.caption("No relevant previous memory was recalled for the latest message.")

    if st.session_state.memory_status:
        st.success(st.session_state.memory_status)

    st.divider()
    st.markdown("**Memory learning loop**")
    st.write("1. Customer explains an issue")
    st.write("2. Hindsight stores the interaction")
    st.write("3. Customer returns later")
    st.write("4. Hindsight recalls relevant context")
    st.write("5. The agent responds with continuity")
