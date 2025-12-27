import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import json
import os

nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

PRICE_HISTORY_FILE = "price_history.json"

# -----------------------------
# Price alert feature
# -----------------------------
def get_price_alert(product_title, current_price):
    if not current_price:
        return ""
    if os.path.exists(PRICE_HISTORY_FILE):
        with open(PRICE_HISTORY_FILE, "r") as f:
            price_data = json.load(f)
    else:
        price_data = {}
    historical_prices = price_data.get(product_title, [])
    if len(historical_prices) == 0:
        alert = f"First recorded price: ₹{current_price}✅"
    else:
        avg_price = sum(historical_prices) / len(historical_prices)
        diff_percent = round(((current_price - avg_price) / avg_price) * 100, 2)
        if diff_percent <= -5:
            alert = f"Price is {abs(diff_percent)}% below average – Good Deal 💰"
        elif diff_percent >= 5:
            alert = f"Price is {diff_percent}% above average – Consider waiting ⚠️"
        else:
            alert = "Price is around average."
    try:
        historical_prices.append(current_price)
        price_data[product_title] = historical_prices[-20:]
        with open(PRICE_HISTORY_FILE, "w") as f:
            json.dump(price_data, f)
    except Exception as e:
        print("Error updating price history:", e)
    return alert

# -----------------------------
# Review analysis
# -----------------------------
def analyze_reviews(reviews, product_rating=None):
    total_reviews = len(reviews)
    if total_reviews == 0:
        return {
            "durability_score": 0,
            "return_risk": 0,
            "average_sentiment": 0,
            "confidence": "Low",
            "advice": "No reviews available to analyze.",
            "explain": {}
        }

    # Keywords
    severe_words = ["broke", "broken", "cracked", "stopped working", "completely damaged", "dead", "torn", "defective"]
    mild_words = ["thin", "average quality", "not premium", "ok for price", "budget", "comfortable", "tight", "loose", "satisfactory"]
    return_words = ["return", "returned", "refund", "replacement", "exchange"]
    delivery_words = ["delivery", "shipping", "courier", "late", "arrogant", "rude", "damaged in transit"]

    # Review containers
    severe_reviews = []
    mild_reviews = []
    return_reviews = []
    delivery_reviews = []
    positive_reviews = []

    severe_hits = 0
    mild_hits = 0
    return_hits = 0
    sentiment_total = 0

    # Analyze each review
    for review in reviews:
        text = review.lower()
        sentiment_score = sia.polarity_scores(text)["compound"]
        sentiment_total += sentiment_score

        if any(word in text for word in severe_words):
            severe_hits += 1
            severe_reviews.append(review)
        elif any(word in text for word in mild_words):
            mild_hits += 1
            mild_reviews.append(review)

        if any(word in text for word in return_words):
            return_hits += 1
            return_reviews.append(review)

        if any(word in text for word in delivery_words):
            delivery_reviews.append(review)

        # Positive reviews: sentiment must be clearly positive (>0.1)
        if sentiment_score > 0.1 and not any(word in text for word in severe_words + mild_words + return_words + delivery_words):
            positive_reviews.append(review)

    # Scores
    durability_score = 85 - severe_hits*15 - mild_hits*3
    durability_score = max(30, min(90, round(durability_score)))
    return_risk = round((return_hits / total_reviews) * 100, 2)
    avg_sentiment = round(sentiment_total / total_reviews, 2)

    # Confidence
    confidence = "Low"
    signal_strength = 0
    if avg_sentiment >= 0.25: signal_strength += 1
    if return_risk < 20: signal_strength += 1
    if durability_score >= 60: signal_strength += 1
    if total_reviews >= 20: signal_strength += 1
    if signal_strength >= 3: confidence = "High"
    elif signal_strength == 2: confidence = "Medium"

    # Advice engine
    advice = []
    if durability_score < 45:
        advice.append("Multiple users reported serious durability issues.")
    elif durability_score < 65:
        advice.append("Some users mentioned concerns about long-term durability.")

    if return_risk >= 40:
        advice.append("High number of return or replacement complaints detected.")
    elif return_risk >= 25:
        advice.append("Moderate return-related issues were found.")

    if avg_sentiment < -0.2:
        advice.append("Overall customer sentiment is strongly negative.")
    elif avg_sentiment < 0:
        advice.append("Customer sentiment is slightly negative.")

    # Rating-based advice
    if product_rating:
        try:
            if float(product_rating) < 4.0:
                advice.append("Average rating is below 4.0, indicating mixed customer experience.")
        except:
            pass

    # General advice if no serious issues
    if not advice:
        if avg_sentiment >= 0.4 and durability_score >= 70 and return_risk <= 10:
            advice.append("Customers consistently praise quality, comfort, and overall satisfaction.")
        elif avg_sentiment >= 0.2:
            advice.append("Feedback is generally positive, but enthusiasm is moderate rather than strong.")
        else:
            advice.append("Most users are satisfied, though opinions vary slightly by personal preference.")

    # Final decision
    if durability_score >= 68 and avg_sentiment >= 0.3 and return_risk <= 15:
        decision_flag = "buy"
    elif durability_score < 50 or avg_sentiment < -0.1 or return_risk >= 35:
        decision_flag = "avoid"
    else:
        decision_flag = "caution"

    advice_text = " ".join(advice)

    # Explainable signals
    explain = {
        "top_severe_reviews": severe_reviews[:3],
        "top_mild_reviews": mild_reviews[:3],
        "top_return_reviews": return_reviews[:3],
        "top_delivery_reviews": delivery_reviews[:3],
        "top_positive_reviews": positive_reviews[:3]
    }

    return {
        "durability_score": durability_score,
        "return_risk": return_risk,
        "average_sentiment": avg_sentiment,
        "confidence": confidence,
        "advice": advice_text,
        "decision_flag": decision_flag,
        "explain": explain
    }
