import streamlit as st
import os
from worker import process
from utils import save_uploaded_file, cleanup_temp
import hashlib

def file_hash(file):
    file.seek(0)
    return hashlib.md5(file.getvalue()).hexdigest()


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Smart Comparator",
    page_icon="⚖️",
    layout="wide"
)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


# =====================================================
# PREMIUM CSS
# =====================================================

st.markdown("""
<style>

.diff-box {
    background: white;
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #e6eaf1;
    height: 500px;
    overflow-y: auto;
    line-height: 1.7;
    font-size: 15px;
}

.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 3em;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# HEADER
# =====================================================

col1, col2 = st.columns([3,1])

with col1:
    st.title("⚖️ Smart Document Comparator")
    st.write("Detect clause changes, financial edits, and legal risks — fully offline.")

with col2:
    st.success("LOCAL ENGINE")

st.divider()


# =====================================================
# FILE UPLOAD
# =====================================================

c1, c2 = st.columns(2)

with c1:
    master_file = st.file_uploader(
        "📘 Upload Master Document",
        type=["pdf","docx","txt"]
    )

with c2:
    test_file = st.file_uploader(
        "📕 Upload Test Document",
        type=["pdf","docx","txt"]
    )


# =====================================================
# ⭐ AUTO CLEAR OLD RESULTS + TEMP FILES
# =====================================================

current_files = (
    file_hash(master_file) if master_file else None,
    file_hash(test_file) if test_file else None
)

if "last_files" not in st.session_state:
    st.session_state.last_files = (None, None)

# If user uploads NEW documents → wipe everything
if st.session_state.last_files != current_files:

    st.session_state.pop("result", None)

    # 🔥 DELETE OLD TEMP FILES
    cleanup_temp()

    st.session_state.last_files = current_files


# =====================================================
# RUN ANALYSIS
# =====================================================

if master_file and test_file:

    if st.button("🚀 Run Deep Analysis"):
        master_file.seek(0)
        test_file.seek(0)


        # EXTRA SAFETY — clean before run
        cleanup_temp()

        with st.spinner("Analyzing legal risks..."):

            try:

                master_path = save_uploaded_file(master_file)
                test_path = save_uploaded_file(test_file)

                result = process(master_path, test_path)

                st.session_state.result = result

            except Exception as e:
                st.error(str(e))


# =====================================================
# RESULTS
# =====================================================

if "result" in st.session_state:

    result = st.session_state.result

    changes = result["changes"]
    risk = result["risk"]
    reasons = result["reasons"]

    # =====================================================
    # DASHBOARD
    # =====================================================

    st.subheader("📊 Risk Dashboard")

    d1, d2, d3 = st.columns(3)

    with d1:
        st.metric("Risk Score", risk)

    with d2:

        if risk > 8:
            status = "🚨 HIGH RISK"
        elif risk > 3:
            status = "⚠️ Moderate"
        else:
            status = "✅ Low"

        st.metric("Document Status", status)

    with d3:
        st.metric("Flags Raised", len(reasons))

    st.divider()


    # =====================================================
    # KEY FINDINGS
    # =====================================================

    if reasons:

        st.subheader("🔎 Key Findings")

        for r in reasons:
            st.write(f"• {r}")

        st.divider()


    # =====================================================
    # FULL DOCUMENT VIEW
    # =====================================================

    st.subheader("📑 Full Document Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📘 MASTER")
        st.markdown(
            f"<div class='diff-box'>{result['master_html']}</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("### 📕 TEST")
        st.markdown(
            f"<div class='diff-box'>{result['test_html']}</div>",
            unsafe_allow_html=True
        )

    st.divider()


    # =====================================================
    # CLAUSE LEVEL
    # =====================================================

    st.subheader("📌 Detailed Clause Changes")

    for change in changes:

        risk_val = change["risk"]

        if risk_val >= 7:
            emoji = "🚨"
        elif risk_val >= 3:
            emoji = "⚠️"
        else:
            emoji = "ℹ️"

        label = f"{emoji} {change['type']} — Risk: {risk_val}"

        with st.expander(label):

            for reason in change["reasons"]:
                st.write(f"- {reason}")

            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**MASTER**")
                st.markdown(
                    f"<div class='diff-box'>{change.get('master','')}</div>",
                    unsafe_allow_html=True
                )

            with c2:
                st.markdown("**TEST**")
                st.markdown(
                    f"<div class='diff-box'>{change.get('test','')}</div>",
                    unsafe_allow_html=True
                )


else:
    st.info("Upload both documents and click **Run Deep Analysis**.")
