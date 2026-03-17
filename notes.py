import streamlit as st
from supabase import create_client, Client

# --- 1. SUPABASE CONFIG ---
# Replace these with your actual Supabase credentials
URL = "https://zlpubuddzujxfafwnxyx.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHVidWRkenVqeGZhZndueHl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2MDAwMTcsImV4cCI6MjA4OTE3NjAxN30.WEi7DZ9Do6zCD2keHEDJ3dqxL89ZukMZ9PvC8DZXCuY"
supabase: Client = create_client(URL, KEY)

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
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.session_state.is_admin = (res.data[0]['role'] == 'admin')
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

    with tab2:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Create Account"):
            try:
                # First user to name themselves 'ADMIN' becomes admin
                role = 'admin' if new_u.upper() == "ADMIN" else 'user'
                supabase.table("users").insert({"username": new_u, "password": new_p, "role": role}).execute()
                st.success("Account created successfully! Please switch to the Login tab.")
            except:
                st.error("That username is already taken.")

# --- 4. MAIN APP INTERFACE ---
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.session_state.is_admin:
        st.sidebar.caption("System Administrator")
    
    menu = ["Cloud Workspace", "Global Chat", "Private Msgs", "Report"]
    if st.session_state.is_admin:
        menu.append("Admin Panel")
    
    choice = st.sidebar.radio("Navigate", menu)

    # --- WORKSPACE ---
    if choice == "Cloud Workspace":
        st.header("📝 Your Cloud Notepad")
        res = supabase.table("user_notes").select("content").eq("username", st.session_state.user).execute()
        current_content = res.data[0]['content'] if res.data else ""
        
        note = st.text_area("Write something to save to your account:", value=current_content, height=300)
        if st.button("Save to Cloud"):
            supabase.table("user_notes").upsert({"username": st.session_state.user, "content": note}).execute()
            st.toast("Progress saved to cloud!")

    # --- GLOBAL CHAT ---
    elif choice == "Global Chat":
        st.header("💬 Global Chat")
        msg = st.text_input("Type a message to the network...")
        if st.button("Send"):
            if msg:
                supabase.table("comments").insert({"username": st.session_state.user, "message": msg}).execute()
                st.rerun()
        
        st.divider()
        res = supabase.table("comments").select("*").order("id", desc=True).limit(20).execute()
        for r in res.data:
            st.write(f"**{r['username']}**: {r['message']}")

    # --- PRIVATE MESSAGES ---
    elif choice == "Private Msgs":
        st.header("🔒 Private Messages")
        t1, t2 = st.tabs(["Inbox", "Send New"])
        
        with t1:
            msgs = supabase.table("messages").select("*").eq("receiver", st.session_state.user).order("id", desc=True).execute()
            if msgs.data:
                for m in msgs.data:
                    with st.chat_message("user"):
                        st.write(f"**From {m['sender']}**")
                        st.write(m['content'])
            else:
                st.info("Your inbox is empty.")
        
        with t2:
            target = st.text_input("Send to (Username):")
            body = st.text_area("Message:")
            if st.button("Send Message"):
                if target and body:
                    supabase.table("messages").insert({
                        "sender": st.session_state.user, 
                        "receiver": target, 
                        "content": body
                    }).execute()
                    st.success(f"Message sent to {target}!")

    # --- REPORT ---
    elif choice == "Report":
        st.header("🚩 Submit a Report")
        st.write("Report bugs or user behavior directly to the admin.")
        issue = st.text_area("Details of the issue:")
        if st.button("Submit Report"):
            if issue:
                supabase.table("reports").insert({
                    "username": st.session_state.user, 
                    "issue": issue
                }).execute()
                st.success("Report submitted. Thank you.")

    # --- ADMIN PANEL ---
    elif choice == "Admin Panel":
        st.header("🛠️ Admin Control Center")
        admin_tab1, admin_tab2 = st.tabs(["User Management", "System Reports"])
        
        with admin_tab1:
            users = supabase.table("users").select("*").execute()
            for user_data in users.data:
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{user_data['username']}** ({user_data['role']})")
                if user_data['username'] != st.session_state.user:
                    if col2.button("Delete", key=f"del_{user_data['username']}"):
                        supabase.table("users").delete().eq("username", user_data['username']).execute()
                        st.rerun()
        
        with admin_tab2:
            reps = supabase.table("reports").select("*").order("id", desc=True).execute()
            if reps.data:
                for r in reps.data:
                    st.warning(f"**From {r['username']}**: {r['issue']}")
            else:
                st.write("No active reports.")

    # --- LOGOUT ---
    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
