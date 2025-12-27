document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const badge = document.getElementById("decisionBadge");
  const adviceDiv = document.getElementById("advice");
  const signalsBox = document.getElementById("signalsBox");

  badge.textContent = "Analyzing current product...";
  badge.className = "badge neutral";
  adviceDiv.textContent = "Fetching product details...";
  signalsBox.style.display = "none";

  try {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      const currentUrl = tabs[0].url;

      if (!currentUrl.includes("amazon")) {
        badge.textContent = "❌ Unsupported Page";
        badge.className = "badge avoid";
        adviceDiv.textContent = "Please open an Amazon product page.";
        return;
      }

      const response = await fetch("http://127.0.0.1:8000/analyze_url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: currentUrl }),
      });

      const result = await response.json();

      if (result.error || !result.product_title) {
        badge.textContent = "❌ Could not analyze";
        badge.className = "badge avoid";
        adviceDiv.textContent = result.error || "Product details not found.";
        return;
      }

      // ---------- PRODUCT DETAILS ----------
      document.getElementById("productBox").style.display = "block";
      document.getElementById("productTitle").textContent =
        result.product_title;
      document.getElementById("productPrice").textContent =
        result.product_price || "N/A";
      document.getElementById("productRating").textContent =
        result.product_rating || "N/A";

      const durability = Number(result.durability_score || 0);
      const returnRisk = Number(result.return_risk || 0);
      const sentiment = Number(result.average_sentiment || 0);
      const decision = result.decision_flag;

      // ---------- DURABILITY BAR ----------
      const durBar = document.getElementById("durabilityBar");
      durBar.style.width = durability + "%";
      durBar.textContent =
        durability >= 75
          ? "Strong Build 💪"
          : durability >= 60
          ? "Average Build 👍"
          : durability >= 45
          ? "Budget-Grade Build ⚠️"
          : "Weak Build ❌";
      durBar.style.backgroundColor =
        decision === "buy"
          ? "#4CAF50"
          : decision === "caution"
          ? "#FFC107"
          : "#F44336";

      // ---------- RETURN BAR ----------
      const retBar = document.getElementById("returnBar");
      retBar.style.width = returnRisk + "%";
      retBar.textContent =
        returnRisk >= 40
          ? `Very High ⚠️ ${returnRisk}%`
          : returnRisk >= 25
          ? `Moderate ⚠️ ${returnRisk}%`
          : "Low";
      retBar.style.backgroundColor =
        decision === "buy"
          ? "#4CAF50"
          : decision === "caution"
          ? "#FFC107"
          : "#F44336";

      // ---------- SENTIMENT BAR ----------
      const sentBar = document.getElementById("sentimentBar");
      const sentimentPercent = Math.round((sentiment + 1) * 50);
      sentBar.style.width = sentimentPercent + "%";
      sentBar.textContent =
        sentiment > 0.3
          ? "Mostly Positive 😊"
          : sentiment > 0
          ? "Slightly Positive 🙂"
          : sentiment < -0.3
          ? "Mostly Negative 😞"
          : sentiment < 0
          ? "Slightly Negative 😐"
          : "Neutral";
      sentBar.style.backgroundColor =
        decision === "buy"
          ? "#4CAF50"
          : decision === "caution"
          ? "#FFC107"
          : "#F44336";

      // ---------- BADGE ----------
      badge.textContent =
        decision === "buy"
          ? "🟢 BUY – Strongly Recommended"
          : decision === "caution"
          ? "🟡 CAUTION – Mixed Signals"
          : "🔴 AVOID – High Risk";
      badge.className = "badge " + decision;

      // ---------- ADVICE ----------
      adviceDiv.innerHTML = `<b>Why this decision?</b><br>• ${result.advice}`;

      // ---------- KEY REVIEW SIGNALS ----------
      let html = "<b>Key Review Signals</b>";
      const e = result.explain;

      if (e.top_severe_reviews.length)
        html += `<br>🔴 Severe: ${e.top_severe_reviews.join("<br>• ")}`;
      if (e.top_mild_reviews.length)
        html += `<br>🟡 Mild: ${e.top_mild_reviews.join("<br>• ")}`;
      if (e.top_return_reviews.length)
        html += `<br>🔁 Returns: ${e.top_return_reviews.join("<br>• ")}`;
      if (e.top_delivery_reviews.length)
        html += `<br>🚚 Delivery issues: ${e.top_delivery_reviews.join(
          "<br>• "
        )}`;
      if (e.top_positive_reviews.length)
        html += `<br><br>🟢 Positive: ${e.top_positive_reviews.join("<br>• ")}`;

      signalsBox.innerHTML = html;
      signalsBox.style.display = "block";
    });
  } catch (err) {
    badge.textContent = "❌ Error";
    badge.className = "badge avoid";
    adviceDiv.textContent = "Failed to analyze product.";
    console.error(err);
  }
});
