from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import re

from lifelabel import analyze_reviews, get_price_alert

app = FastAPI()

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLInput(BaseModel):
    url: str


@app.post("/analyze_url")
def analyze_url(data: URLInput):

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    service = Service(driver_path)

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(data.url)
        time.sleep(5)

        # ---------- SAFE FIND ----------
        def safe_text(by, value):
            try:
                return driver.find_element(by, value).text.strip()
            except:
                return None

        # ---------- PRODUCT DETAILS ----------
        product_title = safe_text(By.ID, "productTitle")
        product_price = safe_text(By.CLASS_NAME, "a-price-whole") or safe_text(By.CLASS_NAME, "a-offscreen")
        product_rating = (
           safe_text(By.XPATH, "//span[@data-hook='rating-out-of-text']")
           or safe_text(By.CLASS_NAME, "a-icon-alt")
            or safe_text(By.XPATH, "//span[contains(text(),'out of 5')]")
        )
        if product_rating:
             m = re.search(r"(\d\.\d|\d)", product_rating)
             product_rating = m.group(1) if m else product_rating


        # ---------- REVIEWS ----------
        review_elements = driver.find_elements(By.XPATH, "//span[@data-hook='review-body']")
        reviews = [r.text.strip() for r in review_elements if r.text.strip()]
        reviews = reviews[:30]

        driver.quit()

        if not reviews:
            return {
                "product_title": product_title,
                "product_price": product_price,
                "product_rating": product_rating,
                "durability_score": 0,
                "return_risk": 0,
                "average_sentiment": 0,
                "advice": "No reviews found",
                "explain": {}
            }

        # ---------- ANALYSIS ----------
        result = analyze_reviews(reviews)
        # ---------- ANALYSIS ----------


# ---------- RATING INSIGHT (SAFE ADDITION) ----------
        try:
          if product_rating:
             rating_value = float(product_rating.split()[0])
             if rating_value < 4.0:
                 result["advice"] += " Average rating is below 4.0, indicating mixed customer experience."
        except:
             pass

        price_alert = get_price_alert(product_title, int(product_price.replace(",", "")) if product_price else None)
        result.update({
            "product_title": product_title,
            "product_price": product_price,
            "product_rating": product_rating,
            "price_alert": price_alert
        })

        result.update({
          "product_title": product_title,
          "product_price": product_price,
          "product_rating": product_rating,
          "reviews": reviews[:10]   # 🔥 evidence layer
         })

        return result


    except Exception as e:
        return {
            "error": str(e),
            "product_title": None,
            "product_price": None,
            "product_rating": None,
            "durability_score": 0,
            "return_risk": 0,
            "average_sentiment": 0,
            "advice": "Backend failed",
            "explain": {}
        }
