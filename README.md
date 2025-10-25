# WhatsApp Resume Parser — Technical Implementation

An automated resume processing system that receives resumes via **WhatsApp**, extracts key candidate information using **AI (Google Gemini)**, and stores structured data in **Google Sheets** — all in real time.

---

## 🚀 Overview

The system automates resume collection and parsing through WhatsApp.  
When a candidate sends their resume, it is automatically downloaded, processed, and logged into Google Sheets.  
A confirmation message is sent back to the candidate summarizing the extracted details.

---

## ⚙️ Architecture & Workflow

**1. Message Handling**  
- WhatsApp messages are received through **Twilio WhatsApp Sandbox**.  
- Each message (with or without attachments) triggers a **Flask webhook**.

**2. Backend Processing**  
- Flask handles incoming requests.  
- Files are downloaded via Twilio’s media URL.  
- Text is extracted using:
  - `pdfplumber` for PDF resumes  
  - `python-docx` for Word documents

**3. Data Parsing (AI)**  
- Extracted text is passed to **Google Gemini API**, which structures the data into JSON.  
- Parsed fields include: Name, Email, Phone, Education, Experience, and Skills.

**4. Storage**  
- Parsed JSON data is written to a **Google Sheet** using the **Google Sheets API**.  
- Each row includes a timestamp and sender’s WhatsApp number.

**5. Feedback Loop**  
- A confirmation message is sent back to the sender summarizing extracted details (without emojis).  

---

## 🧩 Tech Stack

| Component | Technology |
|------------|-------------|
| Messaging | Twilio WhatsApp Sandbox |
| Backend | Flask (Python) |
| AI Model | Google Gemini |
| Storage | Google Sheets API |
| File Parsing | pdfplumber, python-docx |
| Deployment | Localhost (ngrok for webhook exposure) |

---

## 🔧 Configuration

Create a `.env` file in the project root directory and define the following environment variables:

```bash
GEMINI_API_KEY
GOOGLE_SHEET_NAME
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
DEV_EMAIL
