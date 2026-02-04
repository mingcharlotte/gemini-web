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
if "model_name" not in st.session_state:
    try:
        models = client.models.list()
        for m in models:
            if "flash" in m.name:
                st.session_state.model_name = m.name
                break
        if "model_name" not in st.session_state:
            st.session_state.model_name = "gemini-2.5-flash" 
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
    
    # Model Fallback List (in order of preference/stability)
    model_fallbacks = [
        st.session_state.model_name,  # The model that was automatically selected
        "gemini-3-flash",             # Second attempt
        "gemini-2.5-flash-lite",      # Third attempt (lower resource)
        "gemini-2.5-flash"            # Final attempt
    ]
    response = None 

    # Loop through the fallbacks to find a working model
    for model_to_try in model_fallbacks:
        try:
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
            # If successful, break the loop
            break 

        except Exception as e:
            error_message = str(e)
            
            # Check for Quota Exhausted (429) or Model Not Found (404/NOT_FOUND) errors
            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message or "NOT_FOUND" in error_message:
                st.warning(f"Quota/Model error for {model_to_try}. Trying next model...")
                continue
            else:
                # Any other unexpected error
                st.error(f"An unexpected error occurred with {model_to_try}: {e}")
                response = None 
                break # Exit the loop immediately


    # Process the result only if a valid response was generated
    if response:
        with st.chat_message("assistant",avatar="🕊️"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    # If all models failed
    elif not response and prompt:
         st.error("❌ All available models failed due to persistent quota limits or unexpected errors.")
