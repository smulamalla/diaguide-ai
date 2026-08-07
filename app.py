import json
import streamlit as st
from rag_pipeline import query_rag
from datetime import datetime
import uuid
from pathlib import Path


# Custom avatars for user and assistant messages
USER_AVATAR = ":material/person:"
ASSISTANT_AVATAR = ":material/stethoscope:"


# Define custom CSS for the Streamlit app
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded');

:root {
  --ink: #14213D;
  --paper: #F6FAF9;
  --panel: #E9F3F1;
  --teal: #0F9B8E;
  --teal-deep: #0C7F74;
  --teal-soft: #D9F0EC;
  --amber: #EFA23B;
  --line: #D7E1E0;
  --muted: #7C8A93;
}

.material-symbols-rounded {
  font-family: 'Material Symbols Rounded';
  font-weight: normal;
  font-style: normal;
  font-size: 18px;
  line-height: 1;
  vertical-align: middle;
}

.sidebar-footer {
    position: fixed;
    left: 1rem;
    bottom: 1rem;
    width: 250px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    color: var(--muted);
    text-align: center;
    line-height: 1.5;
}

.stApp {
    background-color: #FFFFFF;
    background-image:
        linear-gradient(rgba(20,33,61,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(20,33,61,0.015) 1px, transparent 1px);
    background-size: 28px 28px;
    font-family: 'IBM Plex Sans', sans-serif;
}

h1 {
  font-family: 'IBM Plex Serif', serif;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ink) !important;
}

[data-testid="stCaptionContainer"] { font-family: 'IBM Plex Mono', monospace; color: var(--muted); }

[data-testid="stChatMessage"] {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-left: 3px solid var(--teal);
  border-radius: 10px;
  padding: 0.7rem 1rem;
  margin-bottom: 0.6rem;
  box-shadow: 0 1px 2px rgba(20,33,61,0.04);
}

[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] h3 {
  font-family: 'IBM Plex Mono', monospace;
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  color: var(--ink);
}

[data-testid="stExpander"] summary {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.8rem;
  color: var(--teal-deep);
}

.stButton button {
    background: #E9F7F5;
    color: var(--ink);      /* Change this */
    border: 1px solid #CFE9E4;
    border-radius: 10px;
    font-weight: 500;
    padding: 0.55rem 0.9rem;
    min-height: 58px;
    transition: all 0.18s ease;
}

.stButton button:hover {
    background: #D9F0EC;
    border-color: var(--teal);
    color: var(--teal-deep);
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stBottom"] {
    background: transparent !important;
}

[data-testid="stBottom"] > div {
    background: transparent !important;
}

[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
}

.st-key-sidebar_bottom_group {
    position: fixed;
    left: 0.85rem;
    bottom: 2.8rem;
    width: 270px;
    z-index: 5;
}

.st-key-chat_controls {
    margin-bottom: 0.55rem;
    margin-top: 0.8rem;
}

.st-key-chat_controls .stButton button,
.st-key-chat_controls [data-testid="stDownloadButton"] button {
    background: transparent;
    color: var(--teal-deep) !important;

    border: 1px solid var(--line);
    border-radius: 8px;

    min-height: 42px;
    padding: 0.45rem 0.6rem;

    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    font-weight: 500;

    box-shadow: none;
    transition: all 0.18s ease;
}

.st-key-chat_controls .stButton button:hover,
.st-key-chat_controls [data-testid="stDownloadButton"] button:hover {
    background: #D9F0EC;
    border-color: var(--teal);
    color: var(--teal-deep) !important;
}

.st-key-chat_controls button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}
</style>
"""


THEME_CSS = THEME_CSS.replace("</style>", """
@keyframes drawTrace {
  from { stroke-dashoffset: 700; }
  to { stroke-dashoffset: 0; }
}

@keyframes fadeInDot {
  from { opacity: 0; }
  to { opacity: 1; }
}

.glucose-path {
  stroke-dasharray: 700;
  stroke-dashoffset: 700;
  animation: drawTrace 2.5s ease-out forwards;
}

.glucose-path + circle {
  opacity: 0;
  animation: fadeInDot 0.2s ease-out 1.7s forwards;
}

</style>""")


GLUCOSE_DIVIDER = """
<div style="margin: 0.1rem 0 1.1rem 0;">
<svg width="100%" height="42" viewBox="0 0 600 42" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <path
  d="
    M 8 12
    H 600
    V 20
    Q 600 28 592 28
    H 0
    V 20
    Q 0 12 8 12
    Z
  "
  fill="#D9F0EC"
  />
  <path 
    class="glucose-path"
    d="M0,28 C 60,10 100,34 160,20 C 220,6 260,32 320,18 C 380,8 420,28 480,16 C 530,8 570,22 596,14"
    fill="none"
    stroke="#0F9B8E"
    stroke-width="2.5"
    stroke-linecap="round"
  />
  <circle cx="596" cy="14" r="4" fill="#0F9B8E"/>
</svg>
<div style="display:flex; justify-content:space-between; font-family:'IBM Plex Mono',monospace;
            font-size:0.65rem; color:#7C8A93; letter-spacing:0.05em; margin-top:2px;">
  <span>EVIDENCE-BASED · ADA · NICE · CDC</span>
  <span>TARGET RANGE 70–180 MG/DL</span>
</div>
</div>
"""

# Save chat history in a directory named "data/chat_history"
CHAT_HISTORY_DIR = Path("data/chat_history")
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

if "session_id" not in st.session_state:
    existing = st.query_params.get("session")
    st.session_state.session_id = existing or str(uuid.uuid4())[:8]
    st.query_params["session"] = st.session_state.session_id


# Suggested questions for users to explore at first
SUGGESTED_QUESTIONS = [
    "What is the target A1C for most adults with type 2 diabetes?",
    "When should metformin be started for type 2 diabetes?",
    "What are the recommendations for diabetic kidney disease screening?",
    "How often should people with diabetes get a foot exam?",
    "What blood pressure target is recommended for people with diabetes?",
    "What medications are recommended for type 2 diabetes with heart disease?",
]


# Load guidelines metadata
SOURCES_FILE = "data/sources.json"

@st.cache_data
def load_guideline_metadata():
    with open(SOURCES_FILE) as f:
        return json.load(f)


# Save and load chat history functions
def save_history():
    """
    Save the current chat history and last mentioned drugs to a JSON file
    """
    path = CHAT_HISTORY_DIR / f"{st.session_state.session_id}.json"

    data = {
        "messages": st.session_state.messages,
        "last_drugs": st.session_state.last_drugs,
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_history(session_id):
    """
    Load chat history and last mentioned drugs from a JSON file for the given session_id.
    """
    path = CHAT_HISTORY_DIR / f"{session_id}.json"

    if path.exists():
        with open(path) as f:
            data = json.load(f)

        # Old format: just a list of messages
        if isinstance(data, list):
            return {
                "messages": data,
                "last_drugs": [],
            }

        return data

    return {
        "messages": [],
        "last_drugs": [],
    }


def build_transcript(messages):
    """
    Build a Markdown transcript from the current conversation.
    """
    lines = ["# DiaGuide AI — Conversation Transcript\n"]

    for msg in messages:
        speaker = (
            "You"
            if msg["role"] == "user"
            else "DiaGuide AI"
        )

        lines.append(
            f"**{speaker}:** {msg['content']}\n"
        )

    return "\n".join(lines)

def is_stale(year: int, threshold_years: int = 2) -> bool:
    """
    Check if a guideline is considered stale based on its year.
    A guideline is considered stale if it is older than the threshold_years.
    """
    return (datetime.now().year - year) > threshold_years


# Set up the Streamlit app
st.set_page_config(
    page_title="DiaGuide AI",
    page_icon="🩺"
)

st.markdown(
    THEME_CSS,
    unsafe_allow_html=True
)

st.title("DiaGuide AI 🩺")

st.markdown(
    """
    <div style="
        font-family:'IBM Plex Mono', monospace;
        font-size:0.65rem;
        color:#7C8A93;
        letter-spacing:0.05em;
        margin-top:0.25rem;
    ">
        EVIDENCE-BASED DIABETES GUIDANCE ASSISTANT
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="
        font-family:'IBM Plex Mono', monospace;
        font-size:0.65rem;
        color:#7C8A93;
        letter-spacing:0.05em;
        margin-top:0.15rem;
        margin-bottom:0.9rem;
    ">
        EDUCATIONAL USE ONLY · NOT A SUBSTITUTE FOR MEDICAL ADVICE
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    GLUCOSE_DIVIDER,
    unsafe_allow_html=True
)

st.markdown(
    "<div style='height: 2rem;'></div>",
    unsafe_allow_html=True
)


# Add a disclaimer acknowledgment checkbox to the session state
if "disclaimer_ack" not in st.session_state:
    st.session_state.disclaimer_ack = False


if not st.session_state.disclaimer_ack:
    st.info(
        "**Before you begin:** DiaGuide AI provides evidence-based diabetes "
        "information sourced from clinical guidelines (ADA, NICE, CDC). It is "
        "**not** a diagnostic tool and does not replace professional medical care."
    )

    if st.button("I understand, continue to DiaGuide AI"):
        st.session_state.disclaimer_ack = True
        st.rerun()

    st.stop()


# Initialize session state for chat messages, medications referenced, and suggested questions
if "messages" not in st.session_state:
    saved_history = load_history(
        st.session_state.session_id
    )

    st.session_state.messages = saved_history.get(
        "messages",
        []
    )

    st.session_state.last_drugs = saved_history.get(
        "last_drugs",
        []
    )

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = bool(
        st.session_state.messages
    )


# Sidebar for medications referenced, guidlines list, and footer
with st.sidebar:

    # Medications section
    medication_count = (
        f" ({len(st.session_state.last_drugs)})"
        if st.session_state.last_drugs
        else ""
    )

    with st.expander(
        f"Medications Referenced{medication_count}",
        expanded=bool(st.session_state.last_drugs),
        icon=":material/pill:",
    ):
        if st.session_state.last_drugs:
            for item in sorted(
                st.session_state.last_drugs,
                key=lambda x: x["drug"],
            ):
                st.markdown(
                    f"<div style='background:#FFFFFF; border:1px solid var(--teal); "
                    f"border-radius:8px; padding:0.55rem 0.8rem; margin-bottom:0.5rem;'>"
                    f"<div style='font-weight:600; color:var(--ink); font-size:0.92rem;'>"
                    f"{item['drug']}"
                    f"</div>"
                    f"<div style=\"font-family:'IBM Plex Mono', monospace; "
                    f"font-size:0.68rem; letter-spacing:0.04em; text-transform:uppercase; "
                    f"color:var(--teal-deep); margin-top:2px;\">"
                    f"{item['class']}"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        else:
            st.caption(
                "Medications mentioned in answers will appear here."
            )


    with st.container(key="sidebar_bottom_group"):

        # New chat/transcript export section
        with st.container(key="chat_controls"):
            col1, col2 = st.columns(2)

            if col1.button(
                "New Chat",
                icon=":material/add_comment:",
                use_container_width=True,
            ):
                st.session_state.session_id = str(
                    uuid.uuid4()
                )[:8]

                st.query_params["session"] = (
                    st.session_state.session_id
                )

                st.session_state.messages = []
                st.session_state.last_drugs = []
                st.session_state.pending_question = None
                st.session_state.conversation_started = False

                save_history()

                st.rerun()

            col2.download_button(
                "Export",
                data=build_transcript(
                    st.session_state.messages
                ),
                file_name=(
                    f"diaguide_chat_"
                    f"{st.session_state.session_id}.md"
                ),
                mime="text/markdown",
                icon=":material/download:",
                use_container_width=True,
                disabled=not st.session_state.messages,
            )

        # Guidelines section
        with st.expander(
            "Guidelines in this database",
            expanded=False,
            icon=":material/menu_book:",
        ):
            guidelines = load_guideline_metadata()

            for filename, meta in guidelines.items():
                stale = is_stale(meta["year"])

                badge = (
                    '<span style="color:var(--amber); '
                    'font-size:0.68rem;">⚠ Check for update</span>'
                    if stale
                    else
                    '<span style="color:var(--teal-deep); '
                    'font-size:0.68rem;">Current</span>'
                )

                st.markdown(
                    f"""<div style="margin-bottom:0.9rem;">
    <div style="font-weight:600; font-size:0.85rem; color:var(--ink);">
    {meta['organization']}
    </div>
    <div style="font-family:'IBM Plex Mono', monospace; font-size:0.7rem; color:var(--muted); margin-top:2px;">
    {meta['title']} · v{meta['version']}
    </div>
    <div style="margin-top:2px;">
    {badge}
    </div>
    </div>""",
                    unsafe_allow_html=True,
                )

    # Footer section
    st.markdown(
        """
        <div class="sidebar-footer">
            <span
                class="material-symbols-rounded"
                style="font-size:14px; vertical-align:middle;">
                database
            </span>
            RAG · ADA · NICE · CDC
        </div>
        """,
        unsafe_allow_html=True,
    )


# Display suggested questions if no messages yet
if (
    not st.session_state.messages
    and not st.session_state.conversation_started
):
    st.markdown(
        """
        <div style="
            margin-top:3rem;
            margin-bottom:0.8rem;
            font-family:'IBM Plex Mono', monospace;
            font-size:0.78rem;
            letter-spacing:0.08em;
            color:var(--muted);
        ">
            TRY ASKING...
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(2)

    for i, question in enumerate(SUGGESTED_QUESTIONS):
        if cols[i % 2].button(
            question,
            key=f"suggested_{i}",
            use_container_width=True,
        ):
            st.session_state.pending_question = question
            st.session_state.conversation_started = True
            st.rerun()


# Display chat messages from the session state
for msg in st.session_state.messages:
    avatar = (
        USER_AVATAR
        if msg["role"] == "user"
        else ASSISTANT_AVATAR
    )

    with st.chat_message(
        msg["role"],
        avatar=avatar
    ):
        st.markdown(msg["content"])

        # Display sources if available
        if msg.get("sources"):
            sources = msg["sources"]

            source_label = (
                "source"
                if len(sources) == 1
                else "sources"
            )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:6px;
                    font-family:'IBM Plex Mono', monospace;
                    font-size:0.82rem;
                    color:var(--muted);
                    margin-top:0.4rem;
                    margin-bottom:0.3rem;">
                    <span class="material-symbols-rounded" style="font-size:18px;">
                        menu_book
                    </span>
                    Based on {len(sources)} guideline {source_label}
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("Sources"):
                for source in msg["sources"]:
                    st.markdown(
                        f"**{source['title']}**"
                    )

                    # Citation
                    st.markdown(
                        f"""
                <div style="margin-top:0.45rem;">
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Citation
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.5rem;">
                    {source['citation']}
                </div>
                """,
                        unsafe_allow_html=True,
                    )

                    # Source
                    url = source.get("source_url")

                    if url:
                        st.markdown(
                            f"""
                <div>
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Source
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.5rem;">
                    <a href="{url}" target="_blank">{url}</a>
                </div>
                """,
                            unsafe_allow_html=True,
                        )

                    else:
                        st.markdown(
                            """
                <div>
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Source
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.5rem;">
                    URL unavailable
                </div>
                """,
                            unsafe_allow_html=True,
                        )

                    # Pages
                    pages = ", ".join(
                        str(page)
                        for page in source["pages"]
                    )

                    st.markdown(
                        f"""
                <div>
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Pages
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.9rem;">
                    {pages}
                </div>
                """,
                        unsafe_allow_html=True,
                    )

                    # Divider
                    st.markdown(
                        """
                    <div style="
                        border-top:1px solid var(--line);
                        margin:0.8rem 0 1rem 0;
                    "></div>
                    """,
                        unsafe_allow_html=True,
                    )


# Fetch typed user input
typed_input = st.chat_input(
    "Ask a diabetes-related question..."
)

# Put typed input into the same queue used by suggested questions
if typed_input:
    st.session_state.pending_question = typed_input
    st.session_state.conversation_started = True
    st.rerun()

# Process either a typed question or a clicked suggested question
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None
    st.session_state.conversation_started = True

    # Save and display the user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
    })

    save_history()

    with st.chat_message(
        "user",
        avatar=USER_AVATAR
    ):
        st.markdown(user_input)


    # Run the RAG pipeline
    with st.chat_message(
        "assistant",
        avatar=ASSISTANT_AVATAR
    ):
        try:
            with st.spinner(
                "Searching clinical guidelines..."
            ):
                # last 6 messages -> 3 turns, reasonable prompt length
                recent_history = (
                    st.session_state.messages[-6:]
                )

                answer, sources, drugs_mentioned = query_rag(
                    user_input,
                    chat_history=recent_history,
                )

                st.session_state.last_drugs = drugs_mentioned

        # Handle any errors that occur during the RAG pipeline execution
        except Exception as error:
            answer = (
                "Sorry, I was unable to process your question."
            )

            sources = []
            drugs_mentioned = []
            st.session_state.last_drugs = []

            st.error(str(error))

        st.markdown(answer)

        # Display sources if available
        if sources:
            source_label = (
                "source"
                if len(sources) == 1
                else "sources"
            )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:6px;
                    font-family:'IBM Plex Mono', monospace;
                    font-size:0.82rem;
                    color:var(--muted);
                    margin-top:0.4rem;
                    margin-bottom:0.3rem;">
                    <span class="material-symbols-rounded"
                          style="font-size:18px;">
                        menu_book
                    </span>
                    Based on {len(sources)} guideline {source_label}
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("Sources"):
                for source in sources:
                    st.markdown(
                        f"**{source['title']}**"
                    )

                    # Citation
                    st.markdown(
                        f"""
                <div style="margin-top:0.45rem;">
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Citation
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.5rem;">
                    {source['citation']}
                </div>
                """,
                        unsafe_allow_html=True,
                    )

                    # Source
                    url = source.get("source_url")

                    if url:
                        st.markdown(
                            f"""
                <div>
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Source
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.5rem;">
                    <a href="{url}" target="_blank">{url}</a>
                </div>
                """,
                            unsafe_allow_html=True,
                        )

                    else:
                        st.markdown(
                            """
                <div>
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Source
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.5rem;">
                    URL unavailable
                </div>
                """,
                            unsafe_allow_html=True,
                        )

                    # Pages
                    pages = ", ".join(
                        str(page)
                        for page in source["pages"]
                    )

                    st.markdown(
                        f"""
                <div>
                    <span class="material-symbols-rounded"
                        style="font-size:15px;color:var(--teal);vertical-align:middle;">
                        chevron_right
                    </span>
                    <span style="
                        font-family:'IBM Plex Mono', monospace;
                        font-size:0.72rem;
                        letter-spacing:0.05em;
                        color:var(--muted);
                    ">
                        Pages
                    </span>
                </div>

                <div style="margin-left:1.6rem;margin-top:0.2rem;margin-bottom:0.9rem;">
                    {pages}
                </div>
                """,
                        unsafe_allow_html=True,
                    )

                    # Divider
                    st.markdown(
                        """
                    <div style="
                        border-top:1px solid var(--line);
                        margin:0.8rem 0 1rem 0;
                    "></div>
                    """,
                        unsafe_allow_html=True
                    )


    # Save the assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "drugs": drugs_mentioned,
    })

    save_history()

    # Refresh to display the saved message history and updated sidebar
    st.rerun()