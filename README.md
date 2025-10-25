# WhatsApp Resume Parser - Technical Implementation

## Overview

I built an automated resume processing system that receives resumes via WhatsApp, extracts candidate information using AI, and organizes the data in Google Sheets. The entire workflow happens in real-time with no manual intervention required.

## Approach

The system works as a webhook-based pipeline. When a candidate sends their resume to a designated WhatsApp number, Twilio forwards the message to my Flask application. The app downloads any attached files, extracts text content, sends it to Google's Gemini AI for parsing, and finally writes the structured data to a Google Sheet.

I chose this architecture because webhooks provide instant notifications without constant polling, and cloud APIs handle the heavy lifting of file processing and natural language understanding.

## Technical Stack

**Messaging Layer:** Twilio WhatsApp Sandbox handles message reception and delivery. Their sandbox is free for testing and provides immediate webhook notifications when messages arrive.

**Backend:** Python Flask serves as the webhook endpoint. It's lightweight enough for a demo but production-ready if needed. The app runs locally during development with ngrok tunneling traffic from the internet.

**Document Processing:** I used two libraries for text extraction - `pdfplumber` for complex PDFs and `python-docx` for Word documents. The system tries multiple extraction methods before giving up, which improves success rates with varied file formats.

**AI Parsing:** Google Gemini (gemini-pro model) handles the actual data extraction. I send the resume text with a structured prompt asking for specific fields like name, email, phone number, skills, experience, and education. Gemini returns JSON which I validate before storage.

**Data Storage:** Google Sheets API stores the parsed data. I created a service account for authentication, which lets the application write to sheets without OAuth flows. Each resume becomes one row with timestamp, extracted fields, and the sender's WhatsApp number.

## What It Does

The system successfully processes resumes sent as PDF, DOCX, or plain text through WhatsApp. Within seconds of receiving a resume, it extracts key candidate details and responds with a confirmation message showing what was captured. Recruiters can then view all submissions in a single organized spreadsheet.

The demo handles multiple simultaneous submissions, provides helpful error messages when files are unreadable, and maintains conversation history in the sheet for follow-up.

[//]: # (## Limitations & Future Work)

[//]: # ()
[//]: # (Current limitations include inability to process scanned PDFs &#40;would need OCR integration&#41; and dependence on ngrok for local development. For production use, I would deploy to a cloud platform, add OCR support via Google Cloud Vision, implement better error recovery, and create a simple dashboard for recruiters to manage applications.)

[//]: # ()
[//]: # (The entire system runs on free tiers during testing - Gemini provides 60 requests per minute free, Google Sheets has generous limits, and Twilio's sandbox costs nothing for development.)
