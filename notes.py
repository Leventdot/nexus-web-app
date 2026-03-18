import streamlit as st
from supabase import create_client, Client

# --- 1. SECURE CONFIGURATION ---
# These pull from your "Secrets" vault in Streamlit Cloud
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    MASTER_ADMIN_PASS = st.secrets["ADMIN_PASSWORD"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Secrets are missing! Please add SUPABASE_URL, SUPABASE_KEY, and ADMIN_PASSWORD to Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="Nexus Global", page_icon="🌐", layout="centered")

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.is_admin = False

# --- 3. LOGIN / SIGNUP UI ---
if not st.session_state.logged_in:
    st.title("🌐 NEXUS GLOBAL")
    st.write("Welcome to the private network.")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        
        if st.button("Log In"):
            # Check database for user
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            
            # LOGIN LOGIC: Check DB OR check Master Secret for Admin
            is_master_admin = (u.lower() == "admin" and p == MASTER_ADMIN_PASS)
            
            if res.data or is_master_admin:
                st.session_state.logged_in = True
                st.session_state.user = u
                
                # Determine Admin status
                if is_master_admin:
                    st.session_state.is_admin = True
                else:
                    st.session_state.is_admin = (res.data[0]['role'] == 'admin')
                
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

    with tab2:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Create Account"):
            try:
                # Basic protection: If they name themselves ADMIN, they don't get auto-rights
                # unless they know your Secret Password (handled in Login)
                role = 'user' 
                supabase.table("users").insert({"username": new_u, "password": new_p, "role": role}).execute()
                st.success("Account created! Please switch to the Login tab.")
            except:
                st.error("That username is already taken.")

# --- 4. MAIN APP INTERFACE ---
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.session_state.is_admin:
        st.sidebar.info("⭐ System Administrator")
    
    menu = ["Cloud Workspace", "Global Chat", "Private Msgs", "Report"]
    if st.session_state.is_admin:
        menu.append("Admin Panel")
    
    choice = st.sidebar.radio("Navigate", menu)

    # --- CLOUD WORKSPACE ---
    if choice == "Cloud Workspace":
        st.header("📝 Your Cloud Notepad")
        res = supabase.table("user_notes").select("content").eq("username", st.session_state.user).execute()
        current_content = res.data[0]['content'] if res.data else ""
        
        note = st.text_area("Your private notes:", value=current_content, height=300)
        if st.button("Save to Cloud"):
            supabase.table("user_notes").upsert({"username": st.session_state.user, "content": note}).execute()
            st.toast("Saved!")

    # --- GLOBAL CHAT ---
    elif choice == "Global Chat":
        st.header("💬 Global Chat")
        msg = st.text_input("Message the network...")
        if st.button("Send"):
            if msg:
                supabase.table("comments").insert({"username": st.session_state.user, "message": msg}).execute()
                st.rerun()
        
        st.divider()
        res = supabase.table("comments").select("*").order("id", desc=True).limit(15).execute()
        for r in res.data:
            st.write(f"**{r['username']}**: {r['message']}")

    # --- PRIVATE MESSAGES ---
    elif choice == "Private Msgs":
        st.header("🔒 Private Messages")
        t1, t2 = st.tabs(["Inbox", "Compose"])
        
        with t1:
            msgs = supabase.table("messages").select("*").eq("receiver", st.session_state.user).order("id", desc=True).execute()
            if msgs.data:
                for m in msgs.data:
                    with st.chat_message("user"):
                        st.write(f"**From {m['sender']}**")
                        st.write(m['content'])
            else:
                st.write("No messages.")
        
        with t2:
            target = st.text_input("Recipient Username:")
            body = st.text_area("Message Content:")
            if st.button("Send Secure Message"):
                if target and body:
                    supabase.table("messages").insert({"sender": st.session_state.user, "receiver": target, "content": body}).execute()
                    st.success("Sent!")

    # --- REPORT ---
    elif choice == "Report":
        st.header("🚩 Report an Issue")
        issue = st.text_area("What is the problem?")
        if st.button("Submit"):
            supabase.table("reports").insert({"username": st.session_state.user, "issue": issue}).execute()
            st.success("Admin notified.")

    # --- ADMIN PANEL ---
    elif choice == "Admin Panel":
        st.header("🛠️ Admin Dashboard")
        a_tab1, a_tab2 = st.tabs(["Users", "
