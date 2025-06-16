"""
RAG demo for https://www.educosys.com/
• Fetches page HTML on first run
• Splits → embeds → stores in Chroma
• Lets you query via Gemini‑2.0‑Flash with retrieved context
"""
import os, requests, streamlit as st
import google.generativeai as genai
from bs4 import BeautifulSoup
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

URL = "https://www.educosys.com/"
st.set_page_config(page_title="chatboat")
st.title("ChatBoat")
api_key_env = "AIzaSyDOf-ICLBbumX9SLUQ6NDxRUSVPRkmzYp8"
api_key = os.getenv(api_key_env) or st.sidebar.text_input(
    "Place your Google Key here", type="password",
    help=f"Set once here or via env var {api_key_env}"
)
if api_key:
    genai.configure(api_key=api_key)


# 2.  Build embeddings + Chroma once per session
@st.cache_resource(show_spinner=False)
def init_rag_stack():
    embeds = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-002",
        task_type="RETRIEVAL_DOCUMENT",
    )
    vectordb = Chroma(
        collection_name="edu_rag",
        embedding_function=embeds,
        persist_directory="edu_chroma",
    )
    return embeds, vectordb


embeds, vectordb = init_rag_stack()


@st.cache_data(show_spinner="Fetching & ingesting EducoSys…", ttl=24 * 3600)
def ingest_edu_page() -> int:
    ## Download URL,split into chunks, embed & save. Returns chunks.
    if vectordb._collection.count() > 0:
        return 0  # already done

    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    raw_text = soup.get_text(" ", strip=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024, chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(raw_text)
    vectordb.add_texts(chunks, metadatas=[{"source": URL}] * len(chunks))
    vectordb.persist()
    return len(chunks)


if api_key:  # don’t ingest until a key is supplied
    new_cnt = ingest_edu_page()
    if new_cnt:
        st.sidebar.success(f"Ingested {new_cnt} text chunks from EducoSys ✅")

# User query → retrieve top‑k → LLM answer

st.subheader("Ask a question about EducoSys:")
query = st.text_area("Your question", height=120,
                     placeholder="E.g. “What services does EducoSys offer?”")

temperature = st.slider("Temperature (creativity)", 0.0, 1.0, 0.3, 0.05)
if st.button("Generate answer", use_container_width=True):
    if not api_key:
        st.error("Enter your API key first.")
        st.stop()
    if not query.strip():
        st.warning("Please type a question.")
        st.stop()

    # 4‑a  Retrieve relevant chunks
    k = 4
    hits = vectordb.similarity_search(query, k=k)
    context = "\n\n---\n\n".join([h.page_content for h in hits])

    # 4‑b  Build prompt & call Gemini‑Flash
    prompt = f"""
    You are an expert on the EducoSys website. Use ONLY the context to answer.
    If the answer isn't in the context, say you don't have enough info.
    ### Context
    {context}
    ### Question
    {query}
    ### Answer
    """
    with st.spinner("wait while.... I am  thinking…"):
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash",
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 512,
            },
        )
        result = model.generate_content(prompt)

    # 4‑c  Show answer & retrieved snippets
    st.success("Answer")
    st.write(result.text)

    with st.expander(" Retrieved context (for transparency)"):
        for h in hits:
            st.caption(f"{h.metadata.get('source')}")
            st.write(h.page_content)

# --- Footer ---
st.markdown(
    """
    <hr style="margin-top:3rem">
    <small>created by Sujeet Yadav for Learning Purpose</small>
    """,
    unsafe_allow_html=True,
)