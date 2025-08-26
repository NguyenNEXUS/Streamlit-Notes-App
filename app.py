import streamlit as st
import base64
from urllib.parse import quote, unquote

# ====================
# Config
# ====================
st.set_page_config(page_title="Apple Notes Inspired", layout="centered")

BASE_URL = "https://yourappname.streamlit.app"  # <- Replace with your Streamlit app URL
PASSWORD = "1234"  # <- Change this to your own password

# ====================
# Password Gate
# ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🔒 Enter password to continue")
    pwd = st.text_input("Password", type="password")
    if st.button("Unlock"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()  # <- reload so UI updates
        else:
            st.error("Wrong password.")
    st.stop()

# ====================
# Notes Logic (only shows after login)
# ====================
st.markdown(
    """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .title { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
        .note-box textarea {
            font-size: 1.1em !important;
            border-radius: 12px !important;
            padding: 12px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='title'>📝 Apple Notes</div>", unsafe_allow_html=True)

# Load existing note from query params if present
if "note" in st.query_params:
    try:
        decoded = base64.urlsafe_b64decode(unquote(st.query_params["note"])).decode("utf-8")
    except Exception:
        decoded = ""
else:
    decoded = ""

note = st.text_area("Write your note:", value=decoded, height=250, key="note_input")

# Share button
if st.button("Generate Share Link"):
    encoded = quote(base64.urlsafe_b64encode(note.encode("utf-8")).decode("utf-8"))
    share_url = f"{BASE_URL}/?note={encoded}"
    st.markdown(f"🔗 **Share this link:** [Open Note]({share_url})")
    st.code(share_url, language="text")

