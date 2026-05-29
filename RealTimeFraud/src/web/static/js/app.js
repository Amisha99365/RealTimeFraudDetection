const form = document.getElementById("txn-form");
const submitBtn = document.getElementById("submit-btn");
const resultBox = document.getElementById("result");
const errorBox = document.getElementById("error");
const recentBody = document.getElementById("recent-body");

const statScored = document.getElementById("stat-scored");
const statBlocked = document.getElementById("stat-blocked");
const statReviewed = document.getElementById("stat-reviewed");
const statAllowed = document.getElementById("stat-allowed");

function formatAmount(amount, currency) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: currency || "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "Analyzing..." : "Check Transaction";
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.add("visible");
}

function hideError() {
  errorBox.classList.remove("visible");
}

function renderResult(data) {
  const decision = data.decision;
  resultBox.className = `result visible ${decision}`;

  const riskPct = Math.round(data.risk_score * 100);
  const riskColor = decision === "allow" ? "#22c55e" : decision === "review" ? "#f59e0b" : "#ef4444";

  const rulesHtml = data.rules_triggered.length
    ? `<ul class="rules-list">${data.rules_triggered
        .map((r) => `<li><strong>${r.rule_id}</strong> — ${r.description} (score ${r.score})</li>`)
        .join("")}</ul>`
    : "<p style='color:var(--muted);margin:8px 0 0;'>No fraud rules triggered.</p>";

  resultBox.innerHTML = `
    <div class="decision-row">
      <div>
        <strong>Transaction ID:</strong> ${data.transaction_id.slice(0, 8)}...
      </div>
      <span class="decision-pill ${decision}">${decision}</span>
    </div>
    <p style="margin:10px 0 0;">${data.message}</p>
    <div class="risk-bar"><div class="risk-fill" style="width:${riskPct}%;background:${riskColor};"></div></div>
    <small style="color:var(--muted);">Risk score: ${riskPct}%</small>
    ${rulesHtml}
  `;
}

function renderStats(stats) {
  statScored.textContent = stats.total_scored;
  statBlocked.textContent = stats.total_blocked;
  statReviewed.textContent = stats.total_reviewed;
  statAllowed.textContent = stats.total_allowed;
}

function renderRecent(items) {
  if (!items.length) {
    recentBody.innerHTML = `<tr><td colspan="5" style="color:var(--muted);">No transactions yet. Submit one to begin.</td></tr>`;
    return;
  }

  recentBody.innerHTML = items
    .map(
      (item) => `
      <tr>
        <td>${item.user_id}</td>
        <td>${formatAmount(item.amount, item.currency)}</td>
        <td>${item.channel}</td>
        <td><span class="tag ${item.decision}">${item.decision}</span></td>
        <td>${Math.round(item.risk_score * 100)}%</td>
      </tr>`
    )
    .join("");
}

async function loadDashboard() {
  try {
    const [statsRes, recentRes] = await Promise.all([
      fetch("/api/v1/dashboard/stats"),
      fetch("/api/v1/dashboard/recent?limit=10"),
    ]);

    if (statsRes.ok) renderStats(await statsRes.json());
    if (recentRes.ok) renderRecent(await recentRes.json());
  } catch {
    // Dashboard stats are non-critical on first load
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();
  setLoading(true);

  const payload = {
    user_id: document.getElementById("user_id").value.trim(),
    amount: parseFloat(document.getElementById("amount").value),
    currency: document.getElementById("currency").value,
    channel: document.getElementById("channel").value,
    merchant_id: document.getElementById("merchant_id").value.trim() || null,
    device_id: document.getElementById("device_id").value.trim() || null,
    ip_address: document.getElementById("ip_address").value.trim() || null,
    country_code: document.getElementById("country_code").value.trim().toUpperCase() || null,
  };

  try {
    const response = await fetch("/api/v1/transactions/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Unable to analyze transaction.");
    }

    renderResult(data);
    await loadDashboard();
  } catch (err) {
    showError(err.message || "Something went wrong. Please try again.");
  } finally {
    setLoading(false);
  }
});

loadDashboard();
