import streamlit as st
from groq import Groq
from googlesearch import search
import requests
from bs4 import BeautifulSoup

# --- 1. НАСТРОЙКИ ---
api_key = st.secrets["GROQ_KEY"]
client = Groq(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

def clear_text():
    st.session_state["user_input"] = st.session_state["widget"]
    st.session_state["widget"] = ""

def scrape_google(query):
    try:
        links = list(search(query, num_results=5))
        for link in links:
            if any(x in link for x in ["facebook", "instagram", "twitter", "youtube"]):
                continue
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(link, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = " ".join([p.get_text() for p in soup.find_all('p')])
                if len(text) > 400:
                    return text[:3000], link
    except:
        pass
    return None, None

# --- 2. ГОРНА ЧАСТ (ИМЕ И ЛОГО) ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("# Kenok")
    st.markdown("*Useful AI*")
with col2:
    try:
        st.image("kk.jpg", width=100)
    except:
        st.write("📷")

st.write("---")

# --- 3. КОНТЕЙНЕР ЗА ЧАТА (За да се пълни нагоре) ---
chat_placeholder = st.container()

# --- 4. ПОЛЕ ЗА ПИСАНЕ (Най-отдолу) ---
st.text_input("Питай me нещо:", key="widget", on_change=clear_text)

# --- 5. ЛОГИКА ЗА ОБРАБОТКА ---
if "user_input" in st.session_state and st.session_state.user_input:
    user_query = st.session_state.user_input
    st.session_state.user_input = ""
    
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.spinner('Kenok мисли...'):
        chat_keywords = ["здравей", "как си", "кой си", "защо", "какво мислиш", "здрасти"]
        needs_search = not any(w in user_query.lower() for w in chat_keywords)
        
        info = ""
        source = ""
        if needs_search:
            info, source = scrape_google(user_query)

        # СТРИКТНИ ИНСТРУКЦИИ ЗА ЕЗИКА
        messages_for_ai = [
            {
                "role": "system", 
                "content": "Ти си Kenok, полезен ИИ асистент. ПИШИ САМО НА БЪЛГАРСКИ ЕЗИК. Не използвай китайски, английски или други чужди знаци в думите. Отговаряй ясно, точно и граматически правилно."
            }
        ]
        
        for m in st.session_state.messages:
            messages_for_ai.append({"role": m["role"], "content": m["content"]})
            
        if info:
            messages_for_ai[-1]["content"] += f"\n\nКонтекст от интернет (използвай го за отговора): {info}"

        chat_completion = client.chat.completions.create(
            messages=messages_for_ai,
            model="llama-3.3-70b-versatile",
            temperature=0.5, # По-нисък за повече стабилност на езика
        )
        
        response = chat_completion.choices[0].message.content
        if source:
            response += f"\n\n*Източник: {source}*"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# --- 6. ПЪЛНЕНЕ НА КОНТЕЙНЕРА ---
with chat_placeholder:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**Ти:** {msg['content']}")
        else:
            st.markdown(f"**Kenok:** {msg['content']}")