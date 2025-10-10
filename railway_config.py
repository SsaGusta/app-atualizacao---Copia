# Configuration for Railway deployment

# Use Python 3.11 instead of 3.12 to avoid distutils issues
python_version = "3.11"

# Minimal requirements for Railway deploy
minimal_requirements = [
    "Flask==2.3.3",
    "Flask-Session==0.5.0", 
    "Flask-CORS==4.0.0",
    "gunicorn==21.2.0",
    "python-dotenv==1.0.0",
    "requests==2.31.0",
    "psycopg2-binary==2.9.7"
]

# Optional ML requirements (install only if needed)
ml_requirements = [
    "scikit-learn==1.3.0",
    "joblib==1.3.2", 
    "numpy==1.24.3"
]

# Instructions:
# 1. First deploy with minimal_requirements
# 2. Once working, gradually add ML requirements if needed
# 3. Use environment variables to enable/disable features