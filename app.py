import streamlit as st
import numpy as np
import pandas as pd
import pickle
import sqlite3
from datetime import datetime
from io import BytesIO
import plotly.graph_objects as gofrom 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

from utils.auth import add_user, create_users_table, login_user, reset_password
from utils.ocr import extract_text_from_pdf, extract_text_from_image, extract_cbc_values
from utils.email_sender import send_email_report

st.set_page_config(page_title="AI CBC Health Analyzer", layout="wide")

# ---------------- LOAD ML MODELS ----------------

rf = pickle.load(open("models/model_rf.pkl","rb"))
scaler = pickle.load(open("models/scaler.pkl","rb"))
le = pickle.load(open("models/label_encoder.pkl","rb"))

create_users_table()

# ---------------- DATABASE ----------------

conn = sqlite3.connect("users.db",check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
date TEXT,
hemoglobin REAL,
wbc REAL,
rbc REAL,
platelets REAL,
mcv REAL,
mch REAL,
mchc REAL,
neutrophils REAL,
lymphocytes REAL,
monocytes REAL,
eosinophils REAL,
basophils REAL,
disease TEXT
)
""")

conn.commit()

# ---------------- CBC FEATURES ----------------

features = [
"hemoglobin","wbc","rbc","platelets","mcv","mch","mchc",
"neutrophils","lymphocytes","monocytes","eosinophils","basophils"
]

default_values = {
"hemoglobin":14,
"wbc":7000,
"rbc":5,
"platelets":250000,
"mcv":90,
"mch":30,
"mchc":34,
"neutrophils":60,
"lymphocytes":30,
"monocytes":5,
"eosinophils":3,
"basophils":1
}

# ---------------- DISEASE SIMPLIFICATION ----------------

def simplify_disease(disease_raw):

    mapping = {
        "Thrombocytopenia":"Dengue",
        "Leukocytosis":"Possible Typhoid",
        "Leukopenia":"Viral Infection",
        "Neutrophilia":"Bacterial Infection",
        "Lymphocytosis":"Viral Infection",
        "Anemia":"Anemia",
        "Normal":"Healthy"
    }

    return mapping.get(disease_raw,"General Infection")

# ---------------- PRECAUTIONS ----------------

precautions = {

"Dengue":[
"Drink plenty of fluids",
"Take adequate rest",
"Avoid mosquito bites",
"Monitor platelet count",
"Consult doctor immediately"
],

"Possible Typhoid":[
"Drink clean boiled water",
"Maintain hygiene",
"Avoid outside food",
"Eat freshly cooked food",
"Consult doctor"
],

"Viral Infection":[
"Take rest",
"Stay hydrated",
"Eat nutritious food",
"Avoid contact with infected people",
"Consult doctor if symptoms persist"
],

"Bacterial Infection":[
"Take prescribed antibiotics",
"Maintain hygiene",
"Drink fluids",
"Rest properly",
"Follow doctor advice"
],

"Anemia":[
"Eat iron rich foods",
"Consume vitamin C foods",
"Avoid tea after meals",
"Take iron supplements",
"Consult doctor"
]

}

# ---------------- PDF REPORT ----------------

from datetime import datetime
from io import BytesIO
import plotly.graph_objects as go

st.set_page_config(page_title="AI CBC Health Analyzer", layout="wide")

# ---------------- LOAD ML MODELS ----------------

rf = pickle.load(open("models/model_rf.pkl","rb"))
scaler = pickle.load(open("models/scaler.pkl","rb"))
le = pickle.load(open("models/label_encoder.pkl","rb"))

create_users_table()

# ---------------- DATABASE ----------------

conn = sqlite3.connect("users.db",check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
date TEXT,
hemoglobin REAL,
wbc REAL,
rbc REAL,
platelets REAL,
mcv REAL,
mch REAL,
mchc REAL,
neutrophils REAL,
lymphocytes REAL,
monocytes REAL,
eosinophils REAL,
basophils REAL,
disease TEXT
)
""")

conn.commit()

# ---------------- CBC FEATURES ----------------

features = [
"hemoglobin","wbc","rbc","platelets","mcv","mch","mchc",
"neutrophils","lymphocytes","monocytes","eosinophils","basophils"
]

default_values = {
"hemoglobin":14,
"wbc":7000,
"rbc":5,
"platelets":250000,
"mcv":90,
"mch":30,
"mchc":34,
"neutrophils":60,
"lymphocytes":30,
"monocytes":5,
"eosinophils":3,
"basophils":1
}

# ---------------- DISEASE SIMPLIFICATION ----------------

def simplify_disease(disease_raw):

    mapping = {
        "Thrombocytopenia":"Dengue",
        "Leukocytosis":"Possible Typhoid",
        "Leukopenia":"Viral Infection",
        "Neutrophilia":"Bacterial Infection",
        "Lymphocytosis":"Viral Infection",
        "Anemia":"Anemia",
        "Normal":"Healthy"
    }

    return mapping.get(disease_raw,"General Infection")

# ---------------- PRECAUTIONS ----------------

precautions = {

"Dengue":[
"Drink plenty of fluids",
"Take adequate rest",
"Avoid mosquito bites",
"Monitor platelet count",
"Consult doctor immediately"
],

"Possible Typhoid":[
"Drink clean boiled water",
"Maintain hygiene",
"Avoid outside food",
"Eat freshly cooked food",
"Consult doctor"
],

"Viral Infection":[
"Take rest",
"Stay hydrated",
"Eat nutritious food",
"Avoid contact with infected people",
"Consult doctor if symptoms persist"
],

"Bacterial Infection":[
"Take prescribed antibiotics",
"Maintain hygiene",
"Drink fluids",
"Rest properly",
"Follow doctor advice"
],

"Anemia":[
"Eat iron rich foods",
"Consume vitamin C foods",
"Avoid tea after meals",
"Take iron supplements",
"Consult doctor"
]

}

# ---------------- PDF REPORT ----------------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_pdf(user, values, disease):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=(8.5 * 72, 11 * 72))
    styles = getSampleStyleSheet()
    elements = []

    # TITLE
    elements.append(Paragraph("<font size=22><b>AI CBC Health Analyzer</b></font>", styles["Title"]))
    elements.append(Paragraph("<font size=12>AI Powered Blood Test Disease Prediction Report</font>", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # PATIENT TABLE
    patient_data = [
        ["Patient Name", user],
        ["Report Generated", str(pd.Timestamp.now())],
        ["Predicted Disease", disease],
    ]

    table = Table(patient_data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))

    elements.append(Paragraph("<b>Patient Information</b>", styles["Heading2"]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # CBC TABLE
    cbc_data = [["Parameter","Value"]]
    for k,v in values.items():
        cbc_data.append([k.upper(),str(v)])

    cbc_table = Table(cbc_data, colWidths=[250,150])
    cbc_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4CAF50")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("ALIGN",(1,1),(-1,-1),"CENTER")
    ]))

    elements.append(Paragraph("<b>CBC Test Results</b>", styles["Heading2"]))
    elements.append(cbc_table)
    elements.append(Spacer(1,20))

    # PRECAUTIONS
    elements.append(Paragraph("<b>Recommended Precautions</b>", styles["Heading2"]))
    for p in precautions.get(disease, ["Stay healthy"]):
        elements.append(Paragraph("• "+p, styles["Normal"]))

    elements.append(Spacer(1,20))

    # DISCLAIMER
    elements.append(Paragraph(
        "<i>This report is generated using AI and should not replace medical advice.</i>",
        styles["Italic"]
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
# ---------------- SESSION ----------------

if "page" not in st.session_state:
    st.session_state.page="login"

if "user" not in st.session_state:
    st.session_state.user=None

# ---------------- LOGIN PAGE ----------------

def login():
    col1, col2 = st.columns([1, 1])

    # LEFT SIDE
    with col1:
        st.image(
            "https://cdn-icons-png.flaticon.com/512/2785/2785544.png",
            width=300,
        )

        st.markdown("""
        ## AI CBC Health Analyzer
        Smart Blood Test Disease Prediction System
        """)

    # RIGHT SIDE
    with col2:
        st.markdown("### Login / Sign Up")

        menu = st.radio(
            "",
            ["Login", "Sign Up", "Forgot Password"],
            horizontal=True,
            key="menu"
        )

        st.write("---")

        # -------- LOGIN --------
        if menu == "Login":
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login", use_container_width=True):
                user = login_user(username, password)

                if user:
                    st.session_state.user = username
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

        # -------- SIGN UP --------
        elif menu == "Sign Up":
            username = st.text_input("Username", key="signup_user")
            email = st.text_input("Email Address", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pass")

            if st.button("Create Account", use_container_width=True):
                add_user(username, password, email)
                st.success("Account created successfully")

        # -------- RESET PASSWORD --------
        elif menu == "Forgot Password":
            st.subheader("Reset Password")

            username = st.text_input("Username", key="reset_user")
            new_password = st.text_input("New Password", type="password", key="reset_pass")
            confirm_password = st.text_input("Confirm Password", type="password", key="reset_confirm")

            if st.button("Reset Password", use_container_width=True):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success = reset_password(username, new_password)

                    if success:
                        st.success("Password reset successful. Please login.")
                    else:
                        st.error("Username not found")

# ---------------- DASHBOARD ----------------

def dashboard():

    st.title("CBC Disease Prediction Dashboard")

    st.success(f"Logged in as {st.session_state.user}")

    if st.button("Logout"):

        st.session_state.page="login"
        st.session_state.user=None
        st.rerun()

# ---------------- GET USER EMAIL ----------------

    c.execute(
    "SELECT email FROM users WHERE username=?",
    (st.session_state.user,)
    )

    user_email = c.fetchone()[0]

# ---------------- REPORT UPLOAD ----------------

    uploaded_file = st.file_uploader("Upload CBC Report",type=["pdf","png","jpg"])

    extracted_values = {}

    if uploaded_file:

        if uploaded_file.type=="application/pdf":

            text = extract_text_from_pdf(uploaded_file)

        else:

            text = extract_text_from_image(uploaded_file)

        extracted_values = extract_cbc_values(text)

        st.json(extracted_values)

# ---------------- FILL MISSING VALUES ----------------

    for f in features:

        if f not in extracted_values:

            extracted_values[f] = default_values[f]

# ---------------- MANUAL CBC INPUT ----------------

    with st.form("cbc_form"):

        inputs={}

        for f in features:

            inputs[f] = st.number_input(
                f.upper(),
                value=float(extracted_values.get(f,default_values[f]))
            )

        submit = st.form_submit_button("Predict Disease")

# ---------------- PREDICTION ----------------

    if submit:

        input_data = np.array([list(inputs.values())])

        scaled = scaler.transform(input_data)

        prediction = rf.predict(scaled)

        disease_raw = le.inverse_transform(prediction)[0]

        disease = simplify_disease(disease_raw)

        st.success(f"Medical Condition: {disease_raw}")
        st.info(f"Possible Disease: {disease}")

        if disease in precautions:

            st.subheader("Precautions")

            for p in precautions[disease]:

                st.write("•",p)

# ---------------- SAVE HISTORY ----------------

        c.execute("""
        INSERT INTO history(
        username,date,hemoglobin,wbc,rbc,platelets,
        mcv,mch,mchc,neutrophils,lymphocytes,
        monocytes,eosinophils,basophils,disease
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(
        st.session_state.user,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        *inputs.values(),
        disease
        ))

        conn.commit()

# ---------------- PDF REPORT ----------------

        pdf = generate_pdf(st.session_state.user,inputs,disease)

        st.download_button(
        "Download Health Report",
        pdf,
        file_name="cbc_report.pdf"
        )

# ---------------- SEND EMAIL ----------------

        send_email_report(user_email,pdf)

        st.success("Report has been sent to your email.")

# ---------------- INTERACTIVE CHART ----------------

    history = pd.read_sql_query(
    "SELECT * FROM history WHERE username=?",
    conn,
    params=(st.session_state.user,)
    )

    if not history.empty:

        st.subheader("📊 CBC Trend Analysis Dashboard")

        params = st.multiselect(
        "Select CBC Parameters",
        features,
        default=["wbc","platelets","hemoglobin"]
        )

        fig = go.Figure()

        for p in params:

            fig.add_trace(
            go.Scatter(
            x=history["date"],
            y=history[p],
            mode="lines+markers",
            name=p.upper()
            )
            )

        fig.update_layout(
        title="CBC Trends Over Time",
        template="plotly_white",
        hovermode="x unified"
        )

        st.plotly_chart(fig,use_container_width=True)

# ---------------- ROUTER ----------------

if st.session_state.page=="login":
    login()

if st.session_state.page=="dashboard":
    dashboard()


