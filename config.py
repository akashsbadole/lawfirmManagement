import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///lawfirm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    # Search Engine API Keys (replace with actual keys)
    GOOGLE_SEARCH_API_KEY = os.environ.get('GOOGLE_SEARCH_API_KEY') or 'your-google-api-key'
    GOOGLE_SEARCH_CX = os.environ.get('GOOGLE_SEARCH_CX') or 'your-google-custom-search-engine-id'
    BING_SEARCH_API_KEY = os.environ.get('BING_SEARCH_API_KEY') or 'your-bing-api-key'
    DUCKDUCKGO_API_ENABLED = True  # DuckDuckGo doesn't require API key