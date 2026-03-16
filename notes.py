import streamlit as st
from supabase import create_client, Client

# --- SUPABASE CONFIG ---
URL = "https://zlpubuddzujxfafwnxyx.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHVidWRkenVqeGZhZndueHl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2MDAwMTcsImV4cCI6MjA4OTE3NjAxN30.WEi7DZ9Do6zCD2keHEDJ3dqxL89ZukMZ9PvC8DZXCuY"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Nexus Global Web", page_icon="🌐")

# --- Session State for Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.is_admin = False

# --- UI Logic ---
if not st.session_state.logged_in:
    st.title("NEXUS GLOBAL")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Log In"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.session_state.is_admin = (res.data[0]['role'] == 'admin')
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                role = 'admin' if new_u.upper() == "ADMIN" else 'user'
                supabase.table("users").insert({"username": new_u, "password": new_p, "role": role}).execute()
                st.success("Account created! Go to Login tab.")
            except:
                st.error("Username taken.")

else:
    # --- Main App Interface ---
    st.sidebar.title(f"Welcome, {st.session_state.user}")
    menu = ["Workspace", "Global Chat", "Private Msgs", "Report"]
    if st.session_state.is_admin:
        menu.append("Admin Panel")
    
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "Workspace":
        st.subheader("Cloud Notepad")
        res = supabase.table("user_notes").select("content").eq("username", st.session_state.user).execute()
        current_content = res.data[0]['content'] if res.data else ""
        note = st.text_area("Your private notes:", value=current_content, height=300)
        if st.button("Save to Cloud"):
            supabase.table("user_notes").upsert({"username": st.session_state.user, "content": note}).execute()
            st.toast("Saved!")

    elif choice == "Global Chat":
        st.subheader("World Chat")
        msg = st.text_input("Message")
        if st.button("Send"):
            supabase.table("comments").insert({"username": st.session_state.user, "message": msg}).execute()
        
        res = supabase.table("comments").select("*").order("id", desc=True).execute()
        for r in res.data:
            st.write(f"**{r['username']}**: {r['message']}")

    elif choice == "Admin Panel":
        st.subheader("System Control")
        users = supabase.table("users").select("*").execute()
        for u in users.data:
            col1, col2 = st.columns([3, 1])
            col1.write(f"{u['username']} ({u['role']})")
            if u['username'] != st.session_state.user:
                if col2.button("Delete", key=u['username']):
                    supabase.table("users").delete().eq("username", u['username']).execute()
                    st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
