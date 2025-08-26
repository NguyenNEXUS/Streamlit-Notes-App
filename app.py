# app.py
import streamlit as st
import base64
import zlib
import uuid
import html
from datetime import datetime
from urllib.parse import quote, unquote

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Cloud Notes", page_icon="📝", layout="wide")
BASE_URL = "https://yourappname.streamlit.app"  # <-- replace with your streamlit URL after first deploy
# ----------------------------------------

# ---------------- HELPERS ----------------
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

def note_title(text: str, limit=36):
    if not text or not text.strip():
        return "Untitled"
    first_line = text.strip().splitlines()[0]
    return (first_line[:limit] + "…") if len(first_line) > limit else first_line

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# ---------------- STYLES (Apple Notes-ish) ----------------
st.markdown(
    """
    <style>
    :root { --bg: #f7f7f7; --card: #ffffff; --muted: #6b6f76; --accent: #0071e3; }
    .reportview-container { background: var(--bg); }
    .block-container { padding-top: 14px; padding-left: 14px; padding-right: 14px; }
    .topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
    .app-title { font-family: -apple-system,BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; font-size:20px; font-weight:600; }
    .subtle { color: var(--muted); font-size:13px; }
    .wrap { display:flex; gap:18px; }
    .sidebar { width:340px; min-width:240px; }
    .sidebar .new-btn { width:100%; padding:10px 12px; border-radius:10px; background:var(--card); border:1px solid #e9e9ea; cursor:pointer; box-shadow:0 3px 8px rgba(0,0,0,0.03); }
    .note-item { background:var(--card); border-radius:12px; padding:12px; margin-bottom:10px; box-shadow:0 3px 10px rgba(0,0,0,0.04); }
    .note-title { font-weight:600; margin-bottom:6px; }
    .note-meta { font-size:12px; color:var(--muted); }
    .main-card { background:var(--card); padding:18px; border-radius:14px; box-shadow:0 8px 26px rgba(0,0,0,0.05); min-height:320px; }
    .toolbar { display:flex; gap:8px; align-items:center; margin-bottom:12px; }
    .btn { padding:8px 12px; border-radius:10px; border:1px solid #eaeaea; background:#fafafa; cursor:pointer; }
    .primary { background:var(--accent); color:white; border:0; }
    .danger { background:#fff1f0; color:#b00020; border:1px solid #ffd8d8; }
    textarea, input[type="text"], input[type="password"]{ font-size:16px !important; padding:10px !important; }
    @media (max-width:900px){
        .wrap { flex-direction:column; }
        .sidebar { width:100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- QUERY-BASED SHARED-NOTE VIEW ----------------
qp = st.query_params  # dict-like

if "note" in qp:
    encoded = qp.get("note")[0]
    pw, txt = decode_bundle(encoded)
    st.markdown("<div class='topbar'><div class='app-title'>🔐 Shared Note</div><div class='subtle'>Password protected</div></div>", unsafe_allow_html=True)

    if txt is None:
        st.error("Invalid or corrupted link.")
        st.stop()

    # prompt for password
    entered = st.text_input("Enter password to view the note", type="password", key="shared_pw")
    if st.button("Unlock"):
        if entered == pw:
            st.success("✅ Password correct — read-only view")
            st.markdown(f"<div class='main-card'><textarea style='width:100%;height:420px;border:none;background:transparent' readonly>{html.escape(txt)}</textarea></div>", unsafe_allow_html=True)
        else:
            st.error("❌ Wrong password")
    st.stop()

# ---------------- APP STATE ----------------
if "notes" not in st.session_state:
    # each note: {"id","content","created","updated"}
    st.session_state.notes = []
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

# ---------------- TOP BAR ----------------
st.markdown("<div class='topbar'><div><span class='app-title'>📝 Cloud Notes</span><div class='subtle'>Apple Notes inspired — mobile friendly</div></div></div>", unsafe_allow_html=True)

col_left, col_main = st.columns([1, 2], gap="small")
with col_left:
    st.markdown("<div class='sidebar'>", unsafe_allow_html=True)
    # New note button & search
    if st.button("＋ New Note", key="new_note_btn"):
        nid = uuid.uuid4().hex[:8]
        st.session_state.notes.insert(0, {"id": nid, "content": "", "created": now_str(), "updated": now_str()})
        # open it
        st.query_params = {"id": nid}
        st.experimental_rerun()

    search_q = st.text_input("Search notes", key="search_input", placeholder="Search by title or text…")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Note list (filtered)
    filtered = st.session_state.notes
    if search_q:
        sq = search_q.lower()
        filtered = [n for n in st.session_state.notes if sq in n["content"].lower() or sq in note_title(n["content"]).lower()]

    for n in filtered:
        # show title + meta + small action buttons
        st.markdown("<div class='note-item'>", unsafe_allow_html=True)
        t = note_title(n["content"])
        st.markdown(f"<div class='note-title'>{html.escape(t)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='note-meta'>{n['updated']} • {len(n['content'])} chars</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3,1,1])
        with c1:
            if st.button("Open", key=f"open_{n['id']}"):
                st.query_params = {"id": n["id"]}
                st.experimental_rerun()
        with c2:
            if st.button("Edit", key=f"edit_{n['id']}"):
                st.session_state.editing_id = n["id"]
                st.query_params = {"id": n["id"], "mode": "edit"}
                st.experimental_rerun()
        with c3:
            if st.button("Delete", key=f"del_{n['id']}"):
                st.session_state.confirm_delete = n["id"]
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col_main:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)

    selected_id = qp.get("id", [None])[0] if qp.get("id") else None
    mode = qp.get("mode", [None])[0] if qp.get("mode") else None

    # Confirm delete workflow
    if st.session_state.confirm_delete:
        cid = st.session_state.confirm_delete
        st.warning("Are you sure you want to delete this note? This action cannot be undone.")
        c_yes, c_no = st.columns(2)
        with c_yes:
            if st.button("Yes — Delete", key="confirm_yes"):
                st.session_state.notes = [x for x in st.session_state.notes if x["id"] != cid]
                st.session_state.confirm_delete = None
                st.query_params = {}
                st.experimental_rerun()
        with c_no:
            if st.button("Cancel", key="confirm_no"):
                st.session_state.confirm_delete = None
                st.experimental_rerun()

    # If no notes yet show empty state
    if not st.session_state.notes:
        st.info("No notes yet. Use **New Note** to create one.")
    else:
        # if nothing selected, show the most recent preview
        if not selected_id:
            main_note = st.session_state.notes[0]
            st.markdown(f"### {html.escape(note_title(main_note['content']))}")
            st.markdown(f"**Updated:** {main_note['updated']}")
            st.text_area("Preview", main_note["content"], height=220, disabled=True)
        else:
            # find selected note
            note_obj = next((x for x in st.session_state.notes if x["id"] == selected_id), None)
            if not note_obj:
                st.error("Note not found.")
            else:
                st.markdown(f"### {html.escape(note_title(note_obj['content']))}")
                st.markdown(f"**Created:** {note_obj['created']} • **Updated:** {note_obj['updated']}")
                if mode == "edit" or st.session_state.editing_id == note_obj["id"]:
                    # edit form
                    with st.form(f"form_edit_{note_obj['id']}"):
                        edited = st.text_area("Edit note", value=note_obj["content"], height=300, key=f"edit_area_{note_obj['id']}")
                        c1, c2 = st.columns([1,1])
                        with c1:
                            if st.form_submit_button("Save"):
                                note_obj["content"] = edited
                                note_obj["updated"] = now_str()
                                st.session_state.editing_id = None
                                # clear query mode
                                st.query_params = {"id": note_obj["id"]}
                                st.success("Saved")
                                st.experimental_rerun()
                        with c2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.editing_id = None
                                st.query_params = {"id": note_obj["id"]}
                                st.experimental_rerun()
                else:
                    # read-only view + action buttons
                    st.text_area("Note", note_obj["content"], height=320, disabled=True)
                    A, B, C = st.columns([1,1,1])
                    with A:
                        if st.button("✏️ Edit", key=f"main_edit_{note_obj['id']}"):
                            st.session_state.editing_id = note_obj["id"]
                            st.query_params = {"id": note_obj["id"], "mode": "edit"}
                            st.experimental_rerun()
                    with B:
                        if st.button("🗑 Delete", key=f"main_del_{note_obj['id']}"):
                            st.session_state.confirm_delete = note_obj["id"]
                            st.experimental_rerun()
                    with C:
                        if st.button("🔗 Share", key=f"share_{note_obj['id']}"):
                            # open share panel below
                            st.session_state._share_for = note_obj["id"]
                            st.experimental_rerun()

    # Share panel
    if "_share_for" in st.session_state and st.session_state._share_for:
        sid = st.session_state._share_for
        target = next((x for x in st.session_state.notes if x["id"] == sid), None)
        if target:
            st.markdown("---")
            st.subheader("Share this note (password protected)")
            pw = st.text_input("Set a password for this link", type="password", key=f"share_pw_{sid}")
            if st.button("Generate share link", key=f"gen_{sid}"):
                if not pw:
                    st.warning("Please set a password before generating a link.")
                else:
                    encoded = encode_bundle(target["content"], pw)
                    share_url = f"{BASE_URL}/?note={quote(encoded)}"
                    st.code(share_url)
                    # copy to clipboard (JS)
                    safe_url = html.escape(share_url)
                    st.components.v1.html(
                        f"""
                        <script>
                        function copyToClipboard() {{
                            navigator.clipboard.writeText("{safe_url}");
                        }}
                        copyToClipboard();
                        </script>
                        <div style='margin-top:6px;font-size:13px;color:#444'>Link copied to clipboard if your browser allows it. Share the link AND the password.</div>
                        """,
                        height=80,
                    )
                    st.success("Share link generated")
                    # clear the share target so it doesn't keep showing
                    st.session_state._share_for = None
        else:
            st.error("Cannot find the note to share.")
            st.session_state._share_for = None

    st.markdown("</div>", unsafe_allow_html=True)
