from flask import Flask, render_template, request, jsonify, send_file
from google import genai
import fitz  # PyMuPDF
import os
import werkzeug.utils

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- SECURE CLOUD API SETUP ---
# It now grabs the key secretly from Render so it isn't exposed on GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/quote', methods=['GET'])
def get_quote():
    """Fetches a motivational quote/shloka from Gemini."""
    if not client:
        return jsonify({"quote": "Discipline is the bridge between goals and accomplishment. (API Key will be active once on Render!)"})
        
    prompt = """
    You are an inspiring mentor for a Class 10 student named Shourya. 
    Provide a short, powerful daily thought. It should be EITHER:
    1. A quote about extreme discipline and focus.
    2. A motivational thought about believing in God and trusting the process.
    3. A short Bhagavad Gita Shloka (in Sanskrit or English script) followed by its practical English meaning for a student.
    Keep it brief, formatting it beautifully. Do not include introductory text, just the quote/shloka.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return jsonify({"quote": response.text})
    except Exception as e:
        return jsonify({"quote": "Stay focused. Trust the process."})

@app.route('/api/convert', methods=['POST'])
def convert_pdf():
    """Handles the PDF upload and Dark Mode conversion."""
    if 'pdf_file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return "No selected file", 400
    
    if file and file.filename.endswith('.pdf'):
        filename = werkzeug.utils.secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"DARK_{filename}")
        file.save(input_path)
        
        # PyMuPDF Dark Mode Logic
        doc = fitz.open(input_path)
        out_doc = fitz.open()
        
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            pix.invert_irect(pix.irect)
            out_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
            out_page.insert_image(page.rect, pixmap=pix)
            
        out_doc.save(output_path)
        doc.close()
        out_doc.close()
        
        return send_file(output_path, as_attachment=True)

    return "Invalid file type", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)