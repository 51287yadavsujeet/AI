import streamlit as st
import psycopg2
import pandas as pd
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
import webbrowser

# ======================
# CONFIG
# ======================
# Gemini API Key (Replace with your --this is Tempred)

GENAI_API_KEY = "AIzaSyAna34rGTsC--SiSq7cwYgit1ozkYtMuag---SUJEET"
genai.configure(api_key=GENAI_API_KEY)

# PostgreSQL connection config
PG_HOST = "localhost"
PG_DB = "postgres"
PG_USER = "postgres"
PG_PASS = "admin"
PG_PORT = "5432"

# Email Config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # App password for Gmail
model = genai.GenerativeModel("gemini-1.5-flash")
def connect_postgres():
    return psycopg2.connect(
        host=PG_HOST, database=PG_DB,
        user=PG_USER, password=PG_PASS, port=PG_PORT
    )

def fetch_schema():
    conn = connect_postgres()
    cursor = conn.cursor()
    query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    schema = {}
    for table, column, data_type in rows:
        schema.setdefault(table, []).append(f"{column} ({data_type})")

    schema_text = ""
    for table, columns in schema.items():
        schema_text += f"Table: {table}\nColumns:\n  - " + "\n  - ".join(columns) + "\n\n"
    return schema_text

def natural_language_to_sql(user_query, schema_text):
    prompt = f"""
    You are an expert SQL generator.
    Convert the following natural language query into a valid PostgreSQL query.
    Return only the raw SQL (no ```sql or explanations).

    Database schema:
    {schema_text}

    User request:
    {user_query}
    """
    response = model.generate_content(prompt)
    sql_query = response.text.strip().replace("```sql", "").replace("```", "").strip()
    return sql_query

def execute_query(sql_query):
    conn = connect_postgres()
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
        else:
            conn.commit()
            return pd.DataFrame()
    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()
    finally:
        cursor.close()
        conn.close()



# QA Buddy Function
def send_email(to_email, subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False



# Streamlit App
st.set_page_config(page_title="Buddy App", layout="wide")
st.title("Buddy App – SQL & API Issue Analyzer")

tab1, tab2 = st.tabs(["SQL Buddy", "QA Buddy"])

# ---------------------- SQL Buddy UI ----------------------
with tab1:
    st.subheader("SQL Buddy – Ask DB Questions in Plain English")

    if "schema_text" not in st.session_state:
        with st.spinner("Fetching database schema..."):
            st.session_state.schema_text = fetch_schema()

    user_query = st.text_input("Enter your database question:")
    if st.button("Run Query", key="run_sql"):
        if user_query.strip():
            with st.spinner("Generating SQL query..."):
                sql_query = natural_language_to_sql(user_query, st.session_state.schema_text)
            st.subheader("Generated SQL Query")
            st.code(sql_query, language="sql")

            with st.spinner("Executing SQL query..."):
                result_df = execute_query(sql_query)

            if not result_df.empty:
                st.subheader("Results")
                st.dataframe(result_df)
            else:
                st.warning("No results or query executed successfully.")
        else:
            st.warning("Please enter a question.")

# ---------------------- QA Buddy UI ----------------------
with tab2:
    st.subheader("QA Buddy – Splunk Log Analyzer")
    if "df" not in st.session_state:
        st.session_state.df = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_issue_detected" not in st.session_state:
        st.session_state.last_issue_detected = None
    if "email_draft" not in st.session_state:
        st.session_state.email_draft = ""

    uploaded_file = st.file_uploader("Upload Splunk CSV file", type=["csv"])
    if uploaded_file:
        st.session_state.df = pd.read_csv(uploaded_file)
        st.dataframe(st.session_state.df.head(10))

        user_input = st.chat_input("Ask about the logs")
        if user_input:
            history_text = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in st.session_state.chat_history])
            prompt = f"""
            You are an expert in Splunk log analysis.
            If any service/API error or outage is found, clearly highlight it in the answer.
            Chat history:
            {history_text}

            Logs:
            {st.session_state.df.head(50).to_string()}

            New Question:
            {user_input}
            """
            with st.spinner("Analyzing..."):
                response = model.generate_content(prompt)
                answer = response.text

            if any(k in answer.lower() for k in ["fail", "error", "outage", "unavailable", "service down"]):
                st.session_state.last_issue_detected = answer
                st.session_state.email_draft = f"""
Hello Team,

The following service issue has been detected from Splunk logs:

{answer}

Please investigate and share the ETA.

Regards,
QA Team
"""
            else:
                st.session_state.last_issue_detected = None
                st.session_state.email_draft = ""

            st.session_state.chat_history.append({"user": user_input, "ai": answer})

        for chat in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(chat["user"])
            with st.chat_message("assistant"):
                st.write(chat["ai"])

        if st.session_state.last_issue_detected:
            st.warning("⚠ Service Issue Detected!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Report to Team"):
                    with st.form("email_form"):
                        edited_email = st.text_area("Edit Email", value=st.session_state.email_draft, height=200)
                        submitted = st.form_submit_button("Send Email")
                        if submitted:
                            if send_email("api_issu@test.com", "Service Issue Detected", edited_email):
                                st.success("Reported to api_issu@test.com")
                                st.toast("Email sent successfully")
            with col2:
                if st.button("Create Service Ticket"):
                    webbrowser.open_new_tab("https://www.servicenow.com/contact-us.html")
    else:
        st.info("Upload a CSV file to start log analysis.")
