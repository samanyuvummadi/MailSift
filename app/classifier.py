import re
from typing import Literal
from pydantic import BaseModel, Field
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class EmailClassification(BaseModel):
    category: Literal["Work", "School", "Job Opportunities", "Verification Codes", "Other"]
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., max_length=200)

def classify_email(subject: str, snippet: str, sender: str) -> EmailClassification:
    # Fast path logic for Verification Codes
    if re.search(r"\b(verification code|one-time password|otp|2fa|login code)\b", subject + " " + snippet, re.IGNORECASE):
        return EmailClassification(
            category="Verification Codes",
            rating=4,
            confidence=0.99,
            reasoning="Matched standard OTP/verification keyword pattern."
        )

    prompt = f"""
    You are an expert executive email triage assistant.
    Analyze the email details below and assign a Category and Priority Rating (1 to 5 stars).

    Email Sender: {sender}
    Email Subject: {subject}
    Email Excerpt: {snippet}

    Classification Guidelines:
    - Categories: "Work", "School", "Job Opportunities", "Verification Codes", "Other"
    - Rating scale:
        5 Stars: Immediate urgent action required, direct job interview/offers, critical system alerts, tight school deadlines.
        4 Stars: Important work/school communications, verification codes, time-sensitive inquiries.
        3 Stars: Standard general communications from colleagues, recruiters, or professors.
        2 Stars: Newsletters, general updates, social updates.
        1 Star: Automated marketing, low-priority promos, transactional receipts.
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You classify emails into precise categories and ratings."},
            {"role": "user", "content": prompt}
        ],
        response_format=EmailClassification,
        temperature=0.1,
    )

    return response.choices[0].message.parsed
