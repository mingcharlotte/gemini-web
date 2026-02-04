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
    
    # 1. Define a list of models to try in order (e.g., faster models first)
    # The current one (st.session_state.model_name) is already set, so we put it first.
    # Add other stable models as fallbacks.
    model_fallbacks = [st.session_state.model_name, "gemini-3-flash", "gemini-2.5-flash"]
    response = None # Initialize response variable

    # 2. Loop through the fallbacks and try to generate content
    for model_to_try in model_fallbacks:
        try:
            # Update the model name in session state for UI confirmation
            st.session_state.model_name = model_to_try
            
            response = client.models.generate_content(
                model=model_to_try,
                contents=prompt,
                config={
                    'system_instruction': (
                        "You are a friendly Christian Counselor Assistant for Christ Church Worksop. "
                        "Provide encouraging, kind, and faith-based responses. Tone: Gentle, emojis: 🙏/🕊️. "
                        
                        "\n\n**OFFICIAL LINKS & CRITICAL CURRENT EVENT INFORMATION:**"
                        "\n- Website: https://christchurchworksop.org.uk/"
                        "\n- YouTube: https://www.youtube.com/channel/UCKTxue-nNxsMOZJh6po5PVg"
                        "\n- Facebook: https://www.facebook.com/ChristChurchWorksop"
                        "\n\n**CURRENT EVENT:** The Lunar New Year & Valentine's Event will be held on **8 February 2026, from 2:30 PM - 4:30 PM**. Activities include Market Stalls, Festive Refreshments, Chinese Calligraphy, Quiz, and a Raffle."

                        "\n\nSEARCHING INSTRUCTIONS:"
                        "\nAlways use the Google Search tool for all other events, times, or community posts. You must search both site:christchurchworksop.org.uk AND site:facebook.com/ChristChurchWorksop. If no information is found for a non-listed event, politely advise the user to contact the church directly or attend a Sunday service for the latest announcements."
                    ),
                    'tools': [
                        {'google_search': {}} 
                    ]
                }
            )
            # If successful, break the loop and process the response
            break 

        except Exception as e:
            # Check for the Quota Exhausted error (Error 429)
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # If it's a quota error, show a warning and try the next model
                st.warning(f"Quota exhausted for {model_to_try}. Trying next model...")
                continue # Go to the next model in the list
            else:
                # If it's any other error (e.g., API key invalid), stop everything
                st.error(f"An unexpected error occurred: {e}")
                response = None 
                break # Exit the loop immediately

    # 3. Process the result only if a valid response was generated
    if response:
        with st.chat_message("assistant",avatar="🕊️"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    # Optional: If all models failed
    elif not response:
         st.error("❌ All available models failed due to persistent quota limits or unexpected errors.")
