📄 AI Resume Job Matcher

An AI-powered resume analysis and job recommendation system built using AWS serverless services, Amazon Bedrock, and Streamlit.
The application analyzes a candidate’s resume and recommends suitable job roles with match percentage, skills, salary, and career path.

🚀 Features
📄 Resume upload (PDF)
🔍 Resume text extraction using Amazon Textract
🧠 Semantic understanding using Amazon Bedrock (Titan Embeddings)
📊 Job match score converted to percentage
🧩 Skill extraction and matching
🏢 Job details (Company, Location, Salary)
🚀 Career path recommendations
☁️ Fully serverless AWS architecture
🎨 Interactive UI built with Streamlit
🏗️ System Architecture

1.User uploads resume via Streamlit UI
2.Resume is stored in Amazon S3
3.S3 triggers AWS Lambda
4.Lambda:
    Extracts text using Amazon Textract
    Generates embeddings using Amazon Bedrock
    Calculates cosine similarity with job descriptions
    Saves job recommendations in S3 (results/)
5.Streamlit polls S3 and displays recommendations

🛠️ Technologies Used

Frontend
  Streamlit
  Python

Backend / Cloud
  AWS S3 – File storage
  AWS Lambda – Serverless processing
  Amazon Textract – OCR & text extraction
  Amazon Bedrock (Titan Embeddings) – Semantic embeddings
  IAM – Permissions & security
  
AI / ML
  Text embeddings
  Cosine similarity
  Skill keyword extraction
