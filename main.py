import streamlit as st
from groq import Groq
import uuid

# --- 1. КОНФИГУРАЦИЯ ---
client = Groq(api_key=st.secrets.get["GROQ_KEY"])

client = Groq(api_key=api_key)

SYSTEM_INSTRUCTIONS = """
Ти си Kenok - полезен ИИ асистент. Твоят създател е Tarnak66. 
Не споменавай други компании. Отговаряй винаги на български.
"""

# --- 2. ИНИЦИАЛИЗАЦИЯ НА ГЛОБАЛНАТА БАЗА ---
if "global_db" not in st.session_state:
    st.session_state.global_db = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "editing_chat_id" not in st.session_state:
    st.session_state.editing_chat_id = None

# --- ФУНКЦИИ ---
def create_new_chat():
    user = st.session_state.username
    user_chats = st.session_state.global_db[user]["chats"]
    existing_numbers = [int(chat["name"].split(" ")[1]) for chat in user_chats.values() if chat["name"].startswith("Чат ") and chat["name"].split(" ")[1].isdigit()]
    next_num = 1
    while next_num in existing_numbers:
        next_num += 1
    new_id = str(uuid.uuid4())
    user_chats[new_id] = {"name": f"Чат {next_num}", "messages": []}
    st.session_state.current_chat_id = new_id

# --- СТИЛИЗИРАНЕ (ФИКС ЗА ПОДРЕДБА И НАДПИСИ) ---
st.markdown("""
    <style>
    /* Премахва "Press Enter to apply" */
    div[data-testid="InputInstructions"] {
        display: none;
    }
    /* Форсира колоните в Sidebar да стоят на един ред */
    [data-testid="column"] {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: flex-start;
        min-width: 0px !important;
    }
    /* Малко разстояние между иконките */
    .stButton button {
        padding: 2px 5px !important;
    }
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
                    st.session_state.global_db[user] = {"password": password, "chats": {}}
                if st.session_state.global_db[user]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    if not st.session_state.global_db[user]["chats"]:
                        create_new_chat()
                    st.rerun()
                else:
                    st.error("Грешна парола!")
            else:
                st.error("Попълни полетата!")
        st.write("---")
        st.info("За да използвате Kenok, направете си профил: име и парола.")

# --- 4. ГЛАВЕН ИНТЕРФЕЙС ---
else:
    user_chats = st.session_state.global_db[st.session_state.username]["chats"]
    with st.sidebar:
        try:
            st.image("kk.jpg", width=80)
        except: pass
        st.markdown(f"### **{st.session_state.username}**")
        if st.button("+ Нов чат", use_container_width=True):
            create_new_chat()
            st.rerun()
        st.write("---")
        
        # Списък с чатове
        for chat_id, chat_data in list(user_chats.items()):
            # Правим 3 много тесни колони за бутоните
            c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
            
            with c1:
                if st.session_state.editing_chat_id == chat_id:
                    new_name = st.text_input("Edit", value=chat_data["name"], key=f"in_{chat_id}", label_visibility="collapsed")
                    if st.button("💾", key=f"sv_{chat_id}"):
                        user_chats[chat_id]["name"] = new_name
                        st.session_state.editing_chat_id = None
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
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = None
                    st.rerun()

        st.write("---")
        if st.button("🚪 Изход", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ЧАТ ЗОНА ---
    if st.session_state.current_chat_id and st.session_state.current_chat_id in user_chats:
        curr = user_chats[st.session_state.current_chat_id]
        st.subheader(f"💬 {curr['name']}")
        for msg in curr["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Питай ме нещо..."):
            curr["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            ai_messages = [{"role": "system", "content": SYSTEM_INSTRUCTIONS}] + curr["messages"][-10:]
            with st.chat_message("assistant"):
                with st.spinner("Kenok мисли..."):
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=ai_messages,
                        temperature=0.6
                    ).choices[0].message.content
                    st.write(response)
                curr["messages"].append({"role": "assistant", "content": response})