import streamlit as st
import boto3
import os
import json
import time
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# --------------------------------------------------
# LOAD .env FROM PROJECT ROOT
# --------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# --------------------------------------------------
# STOP IF ENV IS NOT LOADED
# --------------------------------------------------
if not AWS_REGION or not S3_BUCKET or not AWS_ACCESS_KEY:
    st.error("❌ Environment variables not loaded properly. Fix .env file.")
    st.stop()

# --------------------------------------------------
# CREATE S3 CLIENT
# --------------------------------------------------
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# --------------------------------------------------
# HELPER: FETCH JOB RESULTS FROM S3
# --------------------------------------------------
def fetch_job_results(bucket, resume_filename):
    result_key = f"results/{resume_filename}.json"
    try:
        response = s3.get_object(Bucket=bucket, Key=result_key)
        return json.loads(response["Body"].read())
    except Exception:
        return None

# --------------------------------------------------
# STREAMLIT UI
# --------------------------------------------------
st.set_page_config(page_title="AI Resume Job Matcher", layout="centered")

st.title("📄 AI Resume Job Matcher")
st.write("Upload your resume to get AI-powered job recommendations")

uploaded_file = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])

if uploaded_file and st.button("Upload & Match Jobs"):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    resume_filename = f"{timestamp}_{uploaded_file.name}"
    file_key = f"resumes/{resume_filename}"

    try:
        # Upload resume to S3
        s3.upload_fileobj(
            uploaded_file,
            S3_BUCKET,
            file_key,
            ExtraArgs={"ContentType": "application/pdf"}
        )

        st.success("✅ Resume uploaded successfully!")
        st.info("⏳ Processing resume and matching jobs…")

        results = None

        # --------------------------------------------------
        # POLL S3 FOR RESULTS (UP TO 60 SECONDS)
        # --------------------------------------------------
        for _ in range(12):  # 12 × 5s = 60s
            time.sleep(5)
            results = fetch_job_results(S3_BUCKET, resume_filename)
            if results:
                break

        # --------------------------------------------------
        # DISPLAY RESULTS
        # --------------------------------------------------
        if results:
            st.success("🎯 Recommended Jobs")

            for idx, job in enumerate(results, start=1):
                st.markdown(
                    f"""
                    ### {idx}. {job['job_title']}
                    **Company:** {job['company']}  
                    **Location:** {job['location']}  
                    **Salary:** {job['salary']}  
                    **Match:** {job['match_percentage']}%  
                    **Matched Skills:** {", ".join(job['matched_skills'])}  
                    🚀 **Career Path:** {job['career_path']}
                    ---
                    """
                )

        else:
            st.error(
                "❌ Job recommendations are still processing.\n\n"
                "Please wait 30–60 seconds and refresh the page."
            )

    except Exception as e:
        st.error(f"❌ Upload failed: {e}")
