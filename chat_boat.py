import os
import streamlit as st
import google.generativeai as genai

##API Key is Tempered # Not to Use
API_KEY_ENV_VAR = "AIzaSyDOf-ICLBbumX9SLUQ6NDxRUSVPRkmzYp8sky"
# ------------------------------------
st.set_page_config(page_title="My Chat Boat")
st.title("Sujeet Chat Boat")
# --- Sidebar for API key & settings ---
st.sidebar.header("API Key Set Up")
api_key_input = st.sidebar.text_input(
    "Place your Google Key here",
    value=os.getenv(API_KEY_ENV_VAR, ""),
    type="password",
    help="Your key from https://makersuite.google.com/app/apikey "
         "(saved to the GEMINI_API_KEY env var if present).",
)
temperature = st.sidebar.slider(
    "Temperature (creativity)",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.05,
)
max_tokens = st.sidebar.number_input(
    "Max tokens (response length)",
    min_value=10,
    max_value=2048,
    value=256,
    step=10,
)
# --- Configure the SDK once we have a key ---
if api_key_input:
    genai.configure(api_key=api_key_input)


@st.cache_resource(show_spinner=False)
def load_model():
    """Initialise the  model once per session."""
    return genai.GenerativeModel(
        model_name="models/gemini-2.0-flash",
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        },
    )
# --- Prompt input area --
prompt = st.text_area(
    "Enter your prompt below→",
    height=100,
    placeholder="Explain the question asked here..”",
)
if st.button("Generate", use_container_width=True):
    if not api_key_input:
        st.error("Please enter your API key in the sidebar.")
    elif not prompt.strip():
        st.warning("Prompt is empty. Type something first!")
    else:
        with st.spinner("Calling selected Model…"):
            try:
                model = load_model()
                response = model.generate_content(prompt)
                st.success("Response received!")
                st.write(response.text)
            except Exception as e:
                st.exception(e)
# --- Footer ---
st.markdown(
    """
    <hr style="margin-top:3rem">
    <small>created by Sujeet Yadav for Learning Purpose</small>
    """,
    unsafe_allow_html=True,
)