import streamlit as st
import base64
import zlib
from urllib.parse import quote, unquote

BASE_URL = "https://noteslite.streamlit.app"

st.set_page_config(page_title="Cloud Notes", page_icon="📝", layout="centered")

# --- Helper functions ---
def compress_text(text: str) -> str:
    compressed = zlib.compress(text.encode("utf-8"))
    return base64.urlsafe_b64encode(compressed).decode("utf-8")

def decompress_text(encoded: str) -> str:
    try:
        compressed = base64.urlsafe_b64decode(encoded.encode("utf-8"))
        return zlib.decompress(compressed).decode("utf-8")
    except Exception:
        return None

def encode_bundle(text: str, password: str) -> str:
    bundle = f"{password}|||{text}"
    return compress_text(bundle)

def decode_bundle(encoded: str):
    decoded = decompress_text(encoded)
    if not decoded:
        return None, None
    if "|||" in decoded:
        pw, txt = decoded.split("|||", 1)
        return pw, txt
    return None, None

# --- UI ---
st.markdown(
    "<h2 style='text-align:center;'>📝 Cloud Notes</h2>",
    unsafe_allow_html=True
)
st.caption("Mobile-friendly note app with password-protected share links")

# --- Check if viewing shared note ---
query_params = st.query_params
if "note" in query_params:
    encoded = query_params["note"][0]
    pw, txt = decode_bundle(encoded)

    if not txt:
        st.error("Invalid or corrupted note link.")
        st.stop()

    entered_pw = st.text_input("🔑 Enter password to view:", type="password")
    if entered_pw:
        if entered_pw == pw:
            st.success("✅ Correct password!")
            st.text_area("📖 Shared Note:", txt, height=300, disabled=True)
        else:
            st.error("❌ Wrong password")
    st.stop()

# --- Normal Note-Taking Mode ---
if "notes" not in st.session_state:
    st.session_state.notes = []

with st.form("new_note", clear_on_submit=True):
    new_note = st.text_area("✍️ Write your note:", "", height=100)
    submitted = st.form_submit_button("➕ Add Note")
    if submitted and new_note.strip():
        st.session_state.notes.append(new_note.strip())
        st.success("Note added!")

if st.session_state.notes:
    st.subheader("📒 Your Notes")
    for i, note in enumerate(reversed(st.session_state.notes), 1):
        st.markdown(f"**Note {i}:** {note}")

    st.markdown("---")
    st.subheader("🔗 Share Notes")
    share_pw = st.text_input("Set a password:", type="password")
    if st.button("Generate Share Link") and share_pw:
        combined = "\n\n".join(st.session_state.notes)
        encoded = encode_bundle(combined, share_pw)
        share_url = f"{BASE_URL}/?note={quote(encoded)}"
        st.code(share_url, language="text")
        st.info("Give people this link + password to access your notes.")
else:
    st.info("No notes yet. Add one above!")
