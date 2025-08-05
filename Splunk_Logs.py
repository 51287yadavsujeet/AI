import streamlit as st
import pandas as pd
import google.generativeai as genai
# API Key is Altered

genai.configure(api_key="AIzaSyAna34rGTsC--SiSq7cwYgit1ozkYtMuag")

st.set_page_config(page_title="Splunk Log Chat Analyzer", layout="wide")

st.title("Splunk API Log Analyzer")
st.markdown("Upload your Splunk log  file and chat for detailed issue analysis.")

if "df" not in st.session_state:
    st.session_state.df = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# File uploader
uploaded_file = st.file_uploader(" Upload Splunk CSV file", type=["csv"])
## TODO-- need to integrate with feed from Splunk

if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.subheader(" Preview of Uploaded Logs")
    st.dataframe(st.session_state.df.head(10))

    user_input = st.chat_input("Ask a question about the issue (e.g. 'Which API fails most often?')")
    if user_input:

        history_text = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in st.session_state.chat_history])

        prompt = f"""
        You are an expert in Splunk log analysis.
        The following is the chat history:
        {history_text}
        Analyze the logs below and answer the new question in detail.
        Logs:
        {st.session_state.df.head(50).to_string()}
        New Question:
        {user_input}
        """

        with st.spinner("Analyzing issue..."):
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)


            st.session_state.chat_history.append({"user": user_input, "ai": response.text})

    # Display chat history
    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat["user"])
        with st.chat_message("assistant"):
            st.write(chat["ai"])

else:
    st.info("Please upload a CSV file to start chatting with the log analyzer.")
