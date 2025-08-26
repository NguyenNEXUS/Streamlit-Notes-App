# app.py
import streamlit as st
import base64
import zlib
from urllib.parse import quote, unquote
import html

# ----------------- CONFIG -----------------
# AFTER FIRST DEPLOY: set this to your actual Streamlit app URL, e.g.
# BASE_URL = "https://yourappname.streamlit.app"
BASE_URL = "https://yourappname.streamlit.app"
# ------------------------------------------

st.set_page_config(page_title="Cloud Notes", page_icon="📝", layout="wide")

# ----------------- HELPERS -----------------
def compress_text(text: str) -> str:
    compressed = zlib.compress(text.encode("utf-8"))
    return base64.urlsafe_b64encode(compressed).decode("utf-8")

def decompress_text(encoded: str) -> str | None:
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

def short_title(text: str, length=30):
    first = text.strip().splitlines()[0] if text.strip() else "Untitled"
    return (first[:length] + "…") if len(first) > length else first

def st_copy_to_clipboard(js_variable_name="txt"):
    # simple copy button using JS in components
    st.components.v1.html(
        f"""
        <script>
        function copyText(txt) {{
            navigator.clipboard.writeText(txt).then(()=>{{}});
        }}
        </script>
        """,
        height=0,
    )

# ----------------- STYLES (Apple Notes inspired) -----------------
st.markdown(
    """
    <style>
    /* page */
    .reportview-container {background: #f2f3f5;}
    .main .block-container{padding-top:18px;padding-left:14px;padding-right:14px;}
    /* top header */
    .notes-top {display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}
    .app-title {font-size:20px;font-weight:600;}
    /* layout */
    .notes-grid {display:flex;gap:16px;}
    .sidebar {width:320px;min-width:260px;background:transparent;padding:8px 8px 16px 8px}
    .content {flex:1;padding:4px 8px;}
    /* note list items */
    .note-item {background:#fff;border-radius:14px;padding:12px;margin-bottom:10px;box-shadow:0 2px 6px rgba(0,0,0,0.06);}
    .note-title {font-weight:600;margin-bottom:6px;}
    .note-meta {font-size:12px;color:#666;}
    /* note card */
    .note-card {background:#fff;border-radius:14px;padding:18px;box-shadow:0 6px 18px rgba(0,0,0,0.06);min-height:220px;}
    .toolbar {display:flex;gap:8px;align-items:center;margin-bottom:12px;}
    .btn {background:#f1f2f6;border-radius:10px;padding:8px 12px;cursor:pointer;border:1px solid #e6e7ea;}
    .primary {background:#0071e3;color:white;border:0;}
    /* mobile tweaks */
    @media (max-width:720px){
      .notes-grid {flex-direction:column;}
      .sidebar{width:100%;}
    }
    /* inputs bigger for touch */
    textarea, input[type="text"], input[type="password"]{font-size:16px;padding:10px;}
    code.stCodeBlock {overflow-wrap:anywhere;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- SHARED NOTE VIEW (via ?note=...) -----------------
query_params = st.experimental_get_query_params()
if "note" in query_params:
    encoded = query_params["note"][0]
    pw, txt = decode_bundle(encoded)
    st.markdown("<div class='notes-top'><div class='app-title'>🗝️ Shared Note</div></div>", unsafe_allow_html=True)
    if txt is None:
        st.error("Invalid or corrupted note link.")
        st.stop()

    entered_pw = st.text_input("Enter password to view:", type="password")
    if entered_pw:
        if entered_pw == pw:
            st.success("Password correct — viewing note")
            st.markdown(f"<div class='note-card'><textarea style='width:100%;height:300px;border:none;background:transparent' readonly>{html.escape(txt)}</textarea></div>", unsafe_allow_html=True)
        else:
            st.error("Wrong password")
    st.stop()

# ----------------- APP MAIN (notes editor) -----------------
if "notes" not in st.session_state:
    st.session_state.notes = []  # list of dicts: {"text":..., "time":...}

# top bar
st.markdown("<div class='notes-top'><div class='app-title'>📝 Cloud Notes</div><div style='font-size:13px;color:#666'>Apple Notes — inspired UI</div></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2], gap="small")
with col1:
    st.markdown("<div class='sidebar'>", unsafe_allow_html=True)

    # create new note area
    with st.form("new_note", clear_on_submit=True):
        new_text = st.text_area("New note", "", height=140, placeholder="Start typing…")
        submitted = st.form_submit_button("➕ Create")
        if submitted and new_text.strip():
            st.session_state.notes.insert(0, {"text": new_text.strip()})
            st.success("Created")

    st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)

    st.markdown("<div style='font-weight:600;margin-bottom:8px'>Your Notes</div>", unsafe_allow_html=True)
    # Note list
    for idx, note in enumerate(st.session_state.notes):
        title = short_title(note["text"])
        # show item with edit / delete in a compact layout
        st.markdown(f"""
            <div class='note-item'>
              <div class='note-title'>{html.escape(title)}</div>
              <div class='note-meta'>Tap to open • {len(note['text'])} chars</div>
              <div style='margin-top:8px;display:flex;gap:6px;'>
                <form action="" method="GET">
                  <input type="hidden" name="open" value="{idx}">
                  <button class="btn" onclick="window.parent.location.search='?open={idx}';return false;">Open</button>
                </form>
                <button class="btn" onclick="window.parent.location.search='?edit={idx}';return false;">Edit</button>
                <button class="btn" onclick="window.parent.location.search='?del={idx}';return false;">Delete</button>
              </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='content'>", unsafe_allow_html=True)

    # handle open / edit / delete via query params (simple routing)
    q = st.experimental_get_query_params()
    if "open" in q:
        try:
            i = int(q["open"][0])
            note = st.session_state.notes[i]
            st.markdown("<div class='note-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='toolbar'><div style='font-weight:600'>Viewing Note</div></div>", unsafe_allow_html=True)
            st.text_area("Note content (read-only)", note["text"], height=300, disabled=True)
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception:
            st.error("Unable to open note (invalid index).")

    elif "edit" in q:
        try:
            i = int(q["edit"][0])
            note = st.session_state.notes[i]
            st.markdown("<div class='note-card'>", unsafe_allow_html=True)
            st.markdown("<div class='toolbar'><div style='font-weight:600'>Edit Note</div></div>", unsafe_allow_html=True)
            with st.form(f"edit_{i}", clear_on_submit=False):
                edited = st.text_area("Edit note", note["text"], height=300)
                if st.form_submit_button("Save"):
                    st.session_state.notes[i]["text"] = edited.strip()
                    st.success("Saved")
                    # refresh (remove query params)
                    st.experimental_set_query_params()
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception:
            st.error("Unable to edit note (invalid index).")

    elif "del" in q:
        try:
            i = int(q["del"][0])
            if 0 <= i < len(st.session_state.notes):
                st.session_state.notes.pop(i)
                st.success("Deleted")
                st.experimental_set_query_params()
            else:
                st.error("Invalid index")
        except Exception:
            st.error("Unable to delete note (invalid index).")

    else:
        # main dashboard view
        st.markdown("<div class='note-card'>", unsafe_allow_html=True)
        st.markdown("<div class='toolbar'><div style='font-weight:600'>Notes Dashboard</div></div>", unsafe_allow_html=True)

        if st.session_state.notes:
            # show first note preview
            st.text_area("Quick preview (first note)", st.session_state.notes[0]["text"], height=200)
        else:
            st.info("No notes yet — create one on the left")

        st.markdown("---")
        st.subheader("Share Notes")
        share_pw = st.text_input("Set password for shared link", type="password", key="sharepw")
        if st.button("🔗 Generate & Copy Share Link"):
            if not st.session_state.notes:
                st.warning("No notes to share.")
            elif not share_pw:
                st.warning("Set a password first.")
            else:
                combined = "\n\n".join([n["text"] for n in st.session_state.notes])
                encoded = encode_bundle(combined, share_pw)
                share_url = f"{BASE_URL}/?note={quote(encoded)}"
                # show and copy
                st.code(share_url, language="text")
                # copy via JS
                st.components.v1.html(
                    f"""
                    <script>
                    navigator.clipboard.writeText("{share_url}").then(()=>{{
                      // optionally show a tiny confirmation in page
                    }});
                    </script>
                    <div style='margin-top:8px;font-size:13px;color:#444'>Link copied to clipboard (if your browser allows it). Share the link + password.</div>
                    """,
                    height=70,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# keep session alive small footprint
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
