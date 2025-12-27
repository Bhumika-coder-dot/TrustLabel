# LifeLabel – Amazon Review Analysis Tool

LifeLabel is a student project that analyzes Amazon product reviews to help users decide whether to Buy, Caution, or Avoid a product.

## Features

- Sentiment analysis of reviews
- Durability & return risk detection
- Decision advice (BUY / CAUTION / AVOID)
- Chrome extension frontend
- Selenium-based scraping (local only)

## Important Note

Amazon blocks scraping on cloud servers.
This project is intended to run locally using Selenium.

## Tech Stack

- FastAPI (Backend)
- Selenium (Scraping)
- NLTK (Sentiment)
- Chrome Extension (Frontend)

## How to Run (Local)

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```