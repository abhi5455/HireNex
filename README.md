# HireNex: WhatsApp Resume Parser

Recruiters often struggle with manually sorting through hundreds of resumes, identifying candidate details like names, emails, phone numbers, and experience levels. This process is time-consuming, error-prone, and inefficient — especially when applications come from multiple sources.

HireNex eliminates that hassle by automating the entire process.
When a candidate sends their resume through WhatsApp, the system automatically downloads, processes, and logs their details into a Google Sheet.
A confirmation message is instantly sent back to the candidate summarizing the extracted information.

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
- A confirmation message is sent back to the sender summarizing extracted details.  

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
```

## ⚡Demo
<img width="1377" height="963" alt="Screenshot 2025-10-26 131924" src="https://github.com/user-attachments/assets/75d00f7e-36d6-4e4a-b7c7-7dedd4d828a0" />
<br><br>
<img width="1513" height="387" alt="Screenshot 2025-10-26 132150" src="https://github.com/user-attachments/assets/7394df14-63b1-4d3f-8ec0-144367fd663e" />





