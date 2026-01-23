import json
import boto3
import urllib.parse
import re
import math

# ---------------------------
# AWS CLIENTS
# ---------------------------
s3 = boto3.client("s3")
textract = boto3.client("textract")

# ✅ Bedrock MUST be us-east-1
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

# ---------------------------
# TEXT CLEANING
# ---------------------------
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

# ---------------------------
# TEXT CHUNKING
# ---------------------------
def chunk_text(text, chunk_size=500):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# ---------------------------
# SKILL EXTRACTION
# ---------------------------
SKILL_KEYWORDS = [
    "python", "aws", "sql", "machine learning", "data analysis",
    "lambda", "s3", "docker", "kubernetes", "api",
    "devops", "nlp", "flask", "django", "power bi", "excel"
]

def extract_skills(text):
    text = text.lower()
    return [skill for skill in SKILL_KEYWORDS if skill in text]

# ---------------------------
# BEDROCK EMBEDDINGS
# ---------------------------
def generate_embedding(text):
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text})
    )
    response_body = json.loads(response["body"].read())
    return response_body["embedding"]

# ---------------------------
# COSINE SIMILARITY
# ---------------------------
def cosine_similarity(vec1, vec2):
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    return dot / (norm1 * norm2)

# ---------------------------
# JOB DATA (EXTENDED)
# ---------------------------
JOB_DESCRIPTIONS = [
    {
        "title": "Cloud Engineer",
        "company": "Amazon Web Services",
        "location": "Bangalore, India",
        "salary": "₹12–18 LPA",
        "description": "AWS, Lambda, S3, EC2, DevOps, cloud infrastructure"
    },
    {
        "title": "Data Analyst",
        "company": "Accenture",
        "location": "Chennai, India",
        "salary": "₹6–10 LPA",
        "description": "SQL, Python, Excel, Power BI, data analysis"
    },
    {
        "title": "Python Developer",
        "company": "Infosys",
        "location": "Remote",
        "salary": "₹5–9 LPA",
        "description": "Python, Django, Flask, APIs, backend systems"
    },
    {
        "title": "Machine Learning Engineer",
        "company": "TCS",
        "location": "Hyderabad",
        "salary": "₹10–16 LPA",
        "description": "Machine learning, Python, NLP, AI systems"
    },
    {
        "title": "Data Scientist",
        "company": "IBM",
        "location": "Bangalore",
        "salary": "₹12–20 LPA",
        "description": "Statistics, Python, ML models, data science"
    },
    {
        "title": "DevOps Engineer",
        "company": "Wipro",
        "location": "Pune",
        "salary": "₹8–14 LPA",
        "description": "CI/CD, Docker, Kubernetes, AWS, DevOps"
    },
    {
        "title": "Backend Developer",
        "company": "Zoho",
        "location": "Chennai",
        "salary": "₹7–12 LPA",
        "description": "REST APIs, databases, Python, backend development"
    },
    {
        "title": "AI Engineer",
        "company": "Startups",
        "location": "Remote",
        "salary": "₹15–25 LPA",
        "description": "AI pipelines, embeddings, NLP, LLMs"
    },
    {
        "title": "Software Engineer",
        "company": "Google",
        "location": "Hyderabad",
        "salary": "₹20–30 LPA",
        "description": "Software engineering, problem solving, system design"
    },
    {
        "title": "Business Analyst",
        "company": "Deloitte",
        "location": "Mumbai",
        "salary": "₹6–11 LPA",
        "description": "Business analysis, analytics, stakeholder management"
    }
]

CAREER_PATHS = {
    "Cloud Engineer": "AWS Architect → DevOps Lead → Cloud Manager",
    "Data Analyst": "Senior Analyst → Data Scientist → Analytics Manager",
    "Python Developer": "Backend Engineer → Full Stack Developer → Tech Lead",
    "Machine Learning Engineer": "ML Engineer → AI Architect → AI Lead",
    "Data Scientist": "Senior DS → AI Scientist → Head of Data"
}

# ---------------------------
# LAMBDA HANDLER
# ---------------------------
def lambda_handler(event, context):
    try:
        record = event["Records"][0]
        bucket_name = record["s3"]["bucket"]["name"]
        object_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        print("📂 File received:", object_key)

        # Process ONLY resumes
        if not object_key.startswith("resumes/") or not object_key.lower().endswith(".pdf"):
            print("⏭ Skipping file")
            return {"statusCode": 200}

        # Textract
        response = textract.detect_document_text(
            Document={"S3Object": {"Bucket": bucket_name, "Name": object_key}}
        )

        full_text = "\n".join(
            block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"
        )

        cleaned_text = clean_text(full_text)
        chunks = chunk_text(cleaned_text)
        resume_embedding = generate_embedding(chunks[0])
        resume_skills = extract_skills(cleaned_text)

        job_matches = []

        for job in JOB_DESCRIPTIONS:
            job_embedding = generate_embedding(job["description"])
            score = cosine_similarity(resume_embedding, job_embedding)

            job_matches.append({
                "job_title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "salary": job["salary"],
                "match_percentage": round(score * 100, 2),
                "matched_skills": resume_skills[:5],
                "career_path": CAREER_PATHS.get(job["title"], "Career growth path")
            })

        # ✅ FIXED SORT
        job_matches.sort(key=lambda x: x["match_percentage"], reverse=True)

        result_key = f"results/{object_key.split('/')[-1]}.json"

        s3.put_object(
            Bucket=bucket_name,
            Key=result_key,
            Body=json.dumps(job_matches),
            ContentType="application/json"
        )

        print("✅ Results saved:", result_key)

        return {"statusCode": 200}

    except Exception as e:
        print("❌ ERROR:", str(e))
        raise e
