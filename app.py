import os
import zipfile
import tempfile
import requests
import streamlit as st
from google import genai

# Page Configuration
st.set_page_config(
    page_title="RepoDoc AI - Smart Docs Generator",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 3em;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1565C0;
    }
    </style>
""", unsafe_allow_html=True)

# App UI Header
st.markdown('<p class="main-header">⚡ RepoDoc AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated README.md & Architecture Diagram Generator for GitHub Repositories</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key:", type="password", help="Get free API key from Google AI Studio")
    st.divider()
    st.markdown("### 💡 Quick Tip")
    st.info("Paste any public GitHub repository link to generate structured documentation instantly.")

# Main Input Layout
col_input, _ = st.columns([2, 1])
with col_input:
    repo_url = st.text_input("GitHub Repository URL:", placeholder="https://github.com/expressjs/express")

def download_and_extract_repo(repo_url):
    """Downloads repository zip directly from GitHub without needing Git software"""
    clean_url = repo_url.strip().strip("/")
    parts = clean_url.split("/")
    
    if len(parts) < 2:
        return None
        
    owner, repo = parts[-2], parts[-1]
    
    # Try downloading 'main' or 'master' branch zip archive
    zip_urls = [
        f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
        f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = None
    
    for url in zip_urls:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            response = res
            break
            
    if not response:
        return None

    # Extract zip in temp directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "repo.zip")
    
    with open(zip_path, "wb") as f:
        f.write(response.content)
        
    file_list = []
    ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        
    for root, dirs, files in os.walk(temp_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if not file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.zip', '.pdf', '.exe')):
                rel_path = os.path.relpath(os.path.join(root, file), temp_dir)
                # Remove top-level extracted folder name from path
                clean_path = "/".join(rel_path.split(os.sep)[1:])
                if clean_path:
                    file_list.append(clean_path)
                    
    return file_list[:35]

if st.button("🚀 Generate Documentation"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar.")
    elif not repo_url:
        st.warning("⚠️ Please provide a valid GitHub repository URL.")
    else:
        try:
            with st.spinner("🔍 Fetching & analyzing repository files..."):
                file_list = download_and_extract_repo(repo_url)
            
            if not file_list:
                st.error("❌ Could not read repository. Please ensure the URL is valid, public, and contains code.")
            else:
                client = genai.Client(api_key=api_key)
                
                prompt = f"""
                You are a senior software architect. Analyze this file structure and generate a professional `README.md`.

                Repository URL: {repo_url}
                File Structure:
                {chr(10).join(file_list)}

                Required Sections:
                1. Title & High-level Overview
                2. Key Features
                3. Directory Breakdown
                4. Architecture Flowchart (Must use ```mermaid ... ``` format)
                5. Setup & Installation Steps
                """
                
                with st.spinner("🤖 AI is drafting architecture & documentation..."):
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                    )
                
                st.success("✅ Documentation generated successfully!")
                
                # Split Screen Output Tabs
                tab1, tab2 = st.tabs(["📄 Live Documentation Preview", "📥 Raw Markdown"])
                
                with tab1:
                    st.markdown(response.text)
                
                with tab2:
                    st.code(response.text, language="markdown")
                    st.download_button(
                        label="💾 Download README.md File",
                        data=response.text,
                        file_name="README.md",
                        mime="text/markdown"
                    )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")