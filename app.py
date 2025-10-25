from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import os
import requests
from io import BytesIO
import pdfplumber
from pypdf import PdfReader
import docx
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Gemini config
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

# Google Sheets Setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

# open or create Google Sheet
SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Resume Database')
try:
    spreadsheet = gc.open(SHEET_NAME)
    sheet = spreadsheet.sheet1
except:
    spreadsheet = gc.create(SHEET_NAME)
    sheet = spreadsheet.sheet1
    # Share with your email
    spreadsheet.share('abhiramashok1062004@gmail.com', perm_type='user', role='writer')

# Initialize sheet headers if empty
if not sheet.get_all_values():
    sheet.append_row([
        'Timestamp',
        'Name',
        'Email',
        'Phone',
        'Skills',
        'Experience (Years)',
        'Education',
        'WhatsApp Number',
        'Status'
    ])
    # Format header row
    sheet.format('A1:I1', {'textFormat': {'bold': True}})


def download_twilio_file(file_url):
    """Download media from Twilio with authentication"""
    response = requests.get(
        file_url,
        auth=(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN')),
        timeout=30
    )
    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code} - {response.text}")
    return BytesIO(response.content)


def extract_text_from_pdf(file_url):
    """Extract text from PDF file using multiple methods"""
    try:
        print("📥 Downloading PDF...")
        response = requests.get(file_url, timeout=30)
        file_data = download_twilio_file(file_url)

        text = ""

        # Method 1: Try pdfplumber first (better for complex PDFs)
        try:
            print("🔧 Trying pdfplumber...")
            with pdfplumber.open(file_data) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        print(f"   ✓ Page {page_num}: {len(page_text)} chars")

            if len(text.strip()) > 50:
                print(f"✅ pdfplumber success! Extracted {len(text)} characters")
                return text
            else:
                print("⚠️ pdfplumber extracted too little text, trying alternative...")

        except Exception as e:
            print(f"⚠️ pdfplumber failed: {str(e)}, trying pypdf...")

        # Method 2: Fallback to pypdf
        try:
            file_data.seek(0)  # Reset file pointer
            print("🔧 Trying pypdf...")
            pdf_reader = PdfReader(file_data)

            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    print(f"   ✓ Page {page_num}: {len(page_text)} chars")

            if len(text.strip()) > 50:
                print(f"✅ pypdf success! Extracted {len(text)} characters")
                return text
            else:
                return "ERROR: PDF appears to be empty or scanned image. Please send a text-based PDF."

        except Exception as e:
            print(f"❌ pypdf failed: {str(e)}")
            return f"ERROR: Could not read PDF - {str(e)}"

    except Exception as e:
        print(f"❌ Download failed: {str(e)}")
        return f"ERROR: Could not download PDF - {str(e)}"


def extract_text_from_docx(file_url):
    """Extract text from DOCX file"""
    try:
        response = requests.get(file_url, timeout=30)
        file_data = BytesIO(response.content)
        doc = docx.Document(file_data)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"


def extract_text_from_file(file_url, file_type):
    """Download and extract text from resume file"""
    try:
        if 'pdf' in file_type.lower():
            return extract_text_from_pdf(file_url)
        elif 'word' in file_type.lower() or 'document' in file_type.lower():
            return extract_text_from_docx(file_url)
        elif 'text' in file_type.lower():
            response = requests.get(file_url, timeout=30)
            return response.text
        else:
            return "Unsupported file format"
    except Exception as e:
        return f"Error processing file: {str(e)}"


def parse_resume_with_gemini(text):
    """Use Gemini AI to extract structured data from resume"""

    prompt = f"""
You are a resume parser. Extract the following information from the resume text below and return ONLY a valid JSON object with no additional text:

{{
  "name": "Full name of the candidate",
  "email": "Email address",
  "phone": "Phone number",
  "skills": "Top 5-7 key skills (comma-separated)",
  "experience": "Total years of experience (just the number)",
  "education": "Highest degree and institution"
}}

Rules:
- If any field is not found, use "Not found"
- For experience, extract just the number of years (e.g., "5" not "5 years")
- Return ONLY the JSON object, no markdown formatting or explanations

Resume Text:
{text[:3000]}
"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        # Parse JSON
        parsed_data = json.loads(result_text)

        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'skills', 'experience', 'education']
        for field in required_fields:
            if field not in parsed_data:
                parsed_data[field] = "Not found"

        return parsed_data

    except json.JSONDecodeError as e:
        # Fallback: try to extract with a simpler prompt
        return {
            "name": "Parsing error",
            "email": "Parsing error",
            "phone": "Parsing error",
            "skills": "Parsing error",
            "experience": "0",
            "education": "Parsing error"
        }
    except Exception as e:
        return {
            "name": f"Error: {str(e)}",
            "email": "Error",
            "phone": "Error",
            "skills": "Error",
            "experience": "0",
            "education": "Error"
        }


@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""

    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    num_media = int(request.values.get('NumMedia', 0))

    resp = MessagingResponse()
    msg = resp.message()

    print(f"📱 Received message from {from_number}")

    try:
        resume_text = ""
        file_type = "text"

        # Check if message contains file attachment
        if num_media > 0:
            media_url = request.values.get('MediaUrl0')
            media_type = request.values.get('MediaContentType0')
            file_type = media_type

            print(f"📎 Processing file: {media_type}")
            print(f"📎 File URL: {media_url}")

            msg.body("✅ Resume received! Processing your document...")

            resume_text = extract_text_from_file(media_url, media_type)

            # Check for errors
            if resume_text.startswith("ERROR:"):
                error_msg = resume_text.replace("ERROR: ", "")
                msg.body(f"\n\n❌ {error_msg}")

                # Add helpful tip
                if "scanned image" in error_msg.lower():
                    msg.body(
                        "\n\n💡 Tip: Your PDF is a scanned image. Please:\n• Use a text-based PDF\n• Or copy-paste your resume as text")
                else:
                    msg.body("\n\n💡 Try sending your resume as:\n• Plain text message\n• DOCX file\n• Different PDF")

                return str(resp)

            if len(resume_text) < 50:
                msg.body(
                    f"\n\n❌ Could not extract enough text from file (only {len(resume_text)} characters).\n\n💡 Please send as:\n• PDF with actual text (not scanned)\n• DOCX file\n• Plain text")
                return str(resp)

        else:
            # Treat text message as resume
            resume_text = incoming_msg

            if len(resume_text) < 50:
                msg.body(
                    "👋 Hi! Please send your resume as:\n• PDF/DOCX file\n• Or paste your resume text (minimum 50 characters)")
                return str(resp)

            msg.body("✅ Text received! Extracting your details...")

        print(f"📄 Extracted text length: {len(resume_text)} characters")
        print(f"📄 First 200 chars: {resume_text[:200]}...")

        # Parse resume using Gemini
        print("🤖 Sending to Gemini for parsing...")
        parsed_data = parse_resume_with_gemini(resume_text)

        print(f"✨ Parsed data: {parsed_data}")

        # Check if parsing was successful
        if parsed_data.get('name') in ['Parsing error', 'Error', 'Not found']:
            msg.body(
                "\n\n⚠️ Could not extract all details. Please make sure your resume includes:\n• Your full name\n• Email address\n• Phone number\n• Work experience\n• Skills")
            return str(resp)

        # Store in Google Sheets
        from datetime import datetime
        row_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            parsed_data.get('name', 'Not found'),
            parsed_data.get('email', 'Not found'),
            parsed_data.get('phone', 'Not found'),
            parsed_data.get('skills', 'Not found'),
            parsed_data.get('experience', '0'),
            parsed_data.get('education', 'Not found'),
            from_number,
            'New'
        ]

        sheet.append_row(row_data)
        print("✅ Data saved to Google Sheets")

        # Send confirmation message
        confirmation = f"""
✅ *Resume Processed Successfully!*

📋 *Extracted Details:*
👤 Name: {parsed_data.get('name', 'Not found')}
📧 Email: {parsed_data.get('email', 'Not found')}
📞 Phone: {parsed_data.get('phone', 'Not found')}
💼 Experience: {parsed_data.get('experience', '0')} years
🎓 Education: {parsed_data.get('education', 'Not found')}

Your application has been recorded. Our team will review and contact you soon!
"""
        msg.body(confirmation)

    except Exception as e:
        error_msg = f"❌ Error processing resume: {str(e)}"
        print(error_msg)
        print(f"Full error details: {repr(e)}")
        import traceback
        traceback.print_exc()
        msg.body(error_msg)

    return str(resp)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'sheet_name': SHEET_NAME
    }


@app.route('/', methods=['GET'])
def home():
    """Home page with instructions"""
    return """
    <h1>📱 WhatsApp Resume Parser</h1>
    <p>✅ Server is running!</p>
    <h3>How to test:</h3>
    <ol>
        <li>Send your resume to the Twilio WhatsApp sandbox</li>
        <li>Resume can be: PDF, DOCX, or plain text</li>
        <li>System will extract details and save to Google Sheets</li>
    </ol>
    <p><a href="/health">Check health status</a></p>
    """


if __name__ == '__main__':
    print("🚀 Starting WhatsApp Resume Parser...")
    print(f"📊 Google Sheet: {SHEET_NAME}")
    print(f"🔗 Webhook URL: http://localhost:5000/webhook")
    app.run(debug=True, port=5000)