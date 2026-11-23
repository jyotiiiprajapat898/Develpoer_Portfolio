
import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Developer Portfolio", page_icon="💻", layout="wide")

conn = sqlite3.connect("portfolio.db", check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS projects(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT, description TEXT, tech TEXT, status TEXT
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS reviews(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 project_id INTEGER, reviewer TEXT, rating INTEGER, feedback TEXT
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS profile(
 id INTEGER PRIMARY KEY CHECK(id=1),
 name TEXT, skills TEXT, bio TEXT
)
""")
conn.commit()

st.title("💻 Developer Portfolio Dashboard")
st.caption("Manage your profile, projects and reviewer feedback.")

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "My Profile", "Projects", "Reviews"]
)

def get_projects():
    return pd.read_sql_query("SELECT * FROM projects", conn)

if menu == "Dashboard":
    df = get_projects()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Projects", len(df))
    c2.metric("Completed", len(df[df.status == "Completed"]) if len(df) else 0)
    c3.metric("In Progress", len(df[df.status == "In Progress"]) if len(df) else 0)

    st.subheader("Project Overview")
    if not df.empty:
        st.bar_chart(df["status"].value_counts())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No projects added yet.")

elif menu == "My Profile":
    st.subheader("Developer Profile")

    with st.form("profile"):
        name = st.text_input("Developer Name")
        skills = st.text_input("Skills (Python, Java, SQL)")
        bio = st.text_area("Short Bio")
        save = st.form_submit_button("Save Profile")

    if save:
        conn.execute("""
        INSERT OR REPLACE INTO profile(id,name,skills,bio)
        VALUES(1,?,?,?)
        """, (name, skills, bio))
        conn.commit()
        st.success("Profile saved successfully!")

    profile = conn.execute(
        "SELECT name,skills,bio FROM profile WHERE id=1"
    ).fetchone()

    if profile:
        st.write("### Saved Profile")
        st.write("Name:", profile[0])
        st.write("Skills:", profile[1])
        st.write("Bio:", profile[2])

elif menu == "Projects":
    st.subheader("Add New Project")

    with st.form("project"):
        title = st.text_input("Project Title")
        description = st.text_area("Project Description")
        tech = st.text_input("Technology Stack")
        status = st.selectbox(
            "Status", ["Planning", "In Progress", "Completed"]
        )
        save = st.form_submit_button("Add Project")

    if save:
        if title.strip() and tech.strip():
            conn.execute("""
            INSERT INTO projects(title,description,tech,status)
            VALUES(?,?,?,?)
            """, (title, description, tech, status))
            conn.commit()
            st.success("Project added!")
        else:
            st.error("Title and technology are required.")

    st.divider()
    df = get_projects()

    search = st.text_input("Search projects")
    if search:
        df = df[
            df["title"].str.contains(search, case=False, na=False) |
            df["tech"].str.contains(search, case=False, na=False)
        ]

    st.dataframe(df, use_container_width=True)

    if not df.empty:
        project_id = st.selectbox("Select project ID", df["id"])
        if st.button("Delete Selected Project"):
            conn.execute("DELETE FROM projects WHERE id=?", (int(project_id),))
            conn.execute("DELETE FROM reviews WHERE project_id=?", (int(project_id),))
            conn.commit()
            st.rerun()

elif menu == "Reviews":
    st.subheader("Reviewer Feedback")

    projects = get_projects()

    if projects.empty:
        st.info("Add a project before requesting reviews.")
    else:
        project_id = st.selectbox(
            "Select Project",
            projects["id"],
            format_func=lambda x: projects.loc[
                projects.id == x, "title"
            ].iloc[0]
        )

        with st.form("review"):
            reviewer = st.text_input("Reviewer Name")
            rating = st.slider("Rating", 1, 5, 4)
            feedback = st.text_area("Feedback")
            save = st.form_submit_button("Submit Review")

        if save:
            if reviewer.strip():
                conn.execute("""
                INSERT INTO reviews(project_id,reviewer,rating,feedback)
                VALUES(?,?,?,?)
                """, (int(project_id), reviewer, rating, feedback))
                conn.commit()
                st.success("Review saved!")
            else:
                st.error("Reviewer name is required.")

        reviews = pd.read_sql_query("""
        SELECT p.title, r.reviewer, r.rating, r.feedback
        FROM reviews r JOIN projects p ON p.id=r.project_id
        ORDER BY r.id DESC
        """, conn)

        st.dataframe(reviews, use_container_width=True)

conn.close()
