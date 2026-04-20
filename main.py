import streamlit as st
from groq import Groq
import uuid
import json
import os
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
api_key = st.secrets.get("GROQ_KEY", "missing_key")
client = Groq(api_key=api_key)
DB_FILE = "users_data.json"

SYSTEM_INSTRUCTIONS = "Ти си Kenok - полезен ИИ асистент. Твоят създател е Tarnak66. Отговаряй на български."

# --- ФУНКЦИИ ЗА БАЗАТА ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def cleanup_old_accounts(data):
    now = datetime.now()
    to_delete = [u for u, info in data.items() if info.get("last_seen") and (now - datetime.fromisoformat(info["last_seen"]) > timedelta(days=30))]
    for user in to_delete: del data[user]
    if to_delete: save_data(data)
    return data

if "global_db" not in st.session_state:
    st.session_state.global_db = cleanup_old_accounts(load_data())

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "editing_chat_id" not in st.session_state:
    st.session_state.editing_chat_id = None

# --- 2. СТИЛИЗИРАНЕ ---
st.markdown("""
    <style>
    div[data-testid="InputInstructions"] { display: none; }
    [data-testid="column"] { display: flex; flex-direction: row; align-items: center; justify-content: flex-start; }
    .stButton button { padding: 2px 5px !important; }
    button[key="delete_acc_btn"] { color: #ff4b4b !important; border-color: #ff4b4b !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. ЕКРАН ЗА ВХОД ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🤖 Kenok</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Потребител", placeholder="Потребител", label_visibility="collapsed")
        password = st.text_input("Парола", type="password", placeholder="Парола", label_visibility="collapsed")
        
        if st.button("Влез / Регистрация", use_container_width=True):
            if user and password:
                if user not in st.session_state.global_db:
                    st.session_state.global_db[user] = {"password": password, "chats": {}, "last_seen": datetime.now().isoformat()}
                
                if st.session_state.global_db[user]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.global_db[user]["last_seen"] = datetime.now().isoformat()
                    save_data(st.session_state.global_db)
                    st.rerun()
                else: st.error("Грешна парола!")
        st.write("---")
        st.info("За да използвате Kenok, първо трябва да си направите профил. Измислете име и парола. Ако не влизате 30 дни, акаунтът ви се трие автоматично.")

# --- 4. ГЛАВЕН ИНТЕРФЕЙС ---
else:
    user_chats = st.session_state.global_db[st.session_state.username]["chats"]
    
    with st.sidebar:
        st.markdown(f"### **{st.session_state.username}**")
        if st.button("+ Нов чат", use_container_width=True):
            new_id = str(uuid.uuid4())
            user_chats[new_id] = {"name": f"Чат {len(user_chats)+1}", "messages": []}
            st.session_state.current_chat_id = new_id
            save_data(st.session_state.global_db)
            st.rerun()
        
        st.write("---")
        for chat_id, chat_data in list(user_chats.items()):
            c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
            with c1:
                if st.session_state.editing_chat_id == chat_id:
                    new_name = st.text_input("Edit", value=chat_data["name"], key=f"in_{chat_id}", label_visibility="collapsed")
                    if st.button("💾", key=f"sv_{chat_id}"):
                        user_chats[chat_id]["name"] = new_name
                        st.session_state.editing_chat_id = None
                        save_data(st.session_state.global_db)
                        st.rerun()
                else:
                    if st.button(chat_data["name"], key=f"s_{chat_id}", use_container_width=True):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
            with c2:
                if st.button("✏️", key=f"e_{chat_id}"):
                    st.session_state.editing_chat_id = chat_id
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"d_{chat_id}"):
                    del user_chats[chat_id]
                    save_data(st.session_state.global_db)
                    st.rerun()

        st.write("---")
        if st.button("🚪 Изход", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        
        if st.button("❗ Изтрий акаунт", key="delete_acc_btn", use_container_width=True):
            st.session_state.confirm_delete = True
            
        if st.session_state.get("confirm_delete"):
            st.error("Сигурен ли си?")
            col_y, col_n = st.columns(2)
            if col_y.button("ДА", use_container_width=True):
                del st.session_state.global_db[st.session_state.username]
                save_data(st.session_state.global_db)
                st.session_state.logged_in = False
                st.session_state.confirm_delete = False
                st.rerun()
            if col_n.button("НЕ", use_container_width=True):
                st.session_state.confirm_delete = False
                st.rerun()

    # --- ЧАТ ЗОНА ---
    if st.session_state.get("current_chat_id") in user_chats:
        curr = user_chats[st.session_state.current_chat_id]
        st.subheader(f"💬 {curr['name']}")
        
        for msg in curr["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("Питай ме нещо..."):
            st.session_state.global_db[st.session_state.username]["last_seen"] = datetime.now().isoformat()
            curr["messages"].append({"role": "user", "content": prompt})
            save_data(st.session_state.global_db)
            
            with st.chat_message("user"): st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Kenok мисли..."):
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": SYSTEM_INSTRUCTIONS}] + curr["messages"][-10:]
                    ).choices[0].message.content
                    st.write(res)
                    curr["messages"].append({"role": "assistant", "content": res})
                    save_data(st.session_state.global_db)