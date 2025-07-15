import streamlit as st
import httpx

###API Key is Altered:
GEMINI_API_KEY = "AIzaSyAr1ZujuMnwC6eEyaI7dKLaLwD6DNwP9rI"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="Gemini AI Mock Generator", layout="centered")
st.title("API Mock Generator using AI")
prompt = st.text_area("Enter your API description or prompt",
                      height=150,
                      placeholder=" Generate a mock response add your sample request")

if st.button("Generate Mock Response"):
    if not prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        try:
            with st.spinner("Calling Gemini..."):
                response = httpx.post(GEMINI_ENDPOINT, json=payload,
                                      headers={"Content-Type": "application/json"},timeout=30.0 )
                if response.status_code != 200:
                    st.error(f"API Error {response.status_code}: {response.text}")
                else:
                    data = response.json()
                    mock_response = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    st.code(mock_response, language="json")
        except Exception as e:
            st.error(f"Something went wrong: {e}")