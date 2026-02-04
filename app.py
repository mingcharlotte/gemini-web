import streamlit as st
from google import genai
import os

st.set_page_config(page_title="Christian AI Chat", page_icon="🤖")
st.title("🤖 Christian AI Web Assistant")
st.caption("Auto-connecting to the best available Gemini model")

# 1. Get Key
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ API Key not found! Please run the export command in the terminal.")
    st.stop()

client = genai.Client(api_key=api_key)

# 2. AUTOMATIC MODEL FINDER
# This part finds the correct name (e.g., gemini-3.0-flash) automatically
if "model_name" not in st.session_state:
    try:
        models = client.models.list()
        # Find the first model that supports chatting (generate_content)
        # and has "flash" in the name (because it's free/fast)
        for m in models:
            if "flash" in m.name:
                st.session_state.model_name = m.name
                break
        # Fallback if no flash found
        if "model_name" not in st.session_state:
            st.session_state.model_name = "gemini-2.0-flash" 
    except Exception as e:
        st.error(f"Could not find models: {e}")
        st.stop()

st.write(f"📡 Connected to: `{st.session_state.model_name}`")

# 3. Chat Logic
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    # Assign icon based on who is speaking
    icon = "👤" if message["role"] == "user" else "🕊️" 
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        # Use the automatically found model name
        response = client.models.generate_content(
            model=st.session_state.model_name,
            contents=prompt,
            config={
                'system_instruction': (
                    "You are a friendly Christian Counselor Assistant for Christ Church Worksop. "
                    "Provide encouraging, kind, and faith-based responses. Tone: Gentle, emojis: 🙏/🕊️. "
                    "\n\nOFFICIAL LINKS:"
                    "\n- Website: https://christchurchworksop.org.uk/"
                    "\n- YouTube: https://www.youtube.com/channel/UCKTxue-nNxsMOZJh6po5PVg"
                    "\n- Facebook: https://www.facebook.com/ChristChurchWorksop"
                    "\n\nSEARCHING INSTRUCTIONS:"
                    "\n1. For official details or long-term events, search: 'site:christchurchworksop.org.uk [user query]'"
                    "\n2. For recent updates, news, or community posts, search: 'site:facebook.com/ChristChurchWorksop [user query]'"
                    "\nAlways prioritize these two sources. If info is found on Facebook, mention it is from a recent social media update."
                ),
                'tools': [
                    {'google_search': {}} 
                ]
            }
        )
        with st.chat_message("assistant",avatar="🕊️"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Error: {e}")
