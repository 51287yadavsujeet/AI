import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="TEMP")

st.set_page_config(page_title="Splunk Log Chat Analyzer", layout="wide")

st.title("Splunk API Log Analyzer")
st.markdown("Upload your Splunk log file and chat for detailed issue analysis.")

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_issue_detected" not in st.session_state:
    st.session_state.last_issue_detected = None  # To store last detected issue for action buttons

# File uploader
uploaded_file = st.file_uploader("Upload Splunk CSV file", type=["csv"])

if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.subheader("Preview of Uploaded Logs")
    st.dataframe(st.session_state.df.head(10))

    # User input
    user_input = st.chat_input("Ask a question about the issue (e.g. 'Which API fails most often?')")
    if user_input:

        # Prepare conversation history
        history_text = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in st.session_state.chat_history])

        # Prompt to Gemini
        prompt = f"""
        You are an expert in Splunk log analysis.
        If any service/API error or outage is found, clearly highlight it in the answer.
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
            answer = response.text

            # Check if response mentions a service issue
            if "fail" in answer.lower() or "error" in answer.lower() or "outage" in answer.lower():
                st.session_state.last_issue_detected = answer
            else:
                st.session_state.last_issue_detected = None

            st.session_state.chat_history.append({"user": user_input, "ai": answer})

    # Display chat history
    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat["user"])
        with st.chat_message("assistant"):
            st.write(chat["ai"])

    # Action buttons if issue detected
    if st.session_state.last_issue_detected:
        st.warning("⚠ Service Issue Detected! Choose an action below:")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📢 Report to Team"):
                st.success("Issue reported to the team successfully!")
                # TODO: Add your integration (Slack, Email, Teams, etc.)

        with col2:
            if st.button("🛠 Create Service Ticket"):
                st.success("Service ticket created successfully!")
                # TODO: Add integration with Jira, ServiceNow, etc.

else:
    st.info("Please upload a CSV file to start chatting with the log analyzer.")
