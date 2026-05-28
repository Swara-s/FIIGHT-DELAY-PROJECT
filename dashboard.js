async function loadDashboard() {
    const response = await fetch("/api/dashboard-data");
    const data = await response.json();

    document.getElementById("totalPred").innerText = data.stats.total_predictions;
    document.getElementById("delayedCount").innerText = data.stats.delayed_count;
    document.getElementById("onTimeCount").innerText = data.stats.on_time_count;
    document.getElementById("delayPercent").innerText = `${data.stats.delay_percent}%`;

    const airlineLabels = Object.keys(data.airline_analysis);
    const airlineValues = Object.values(data.airline_analysis);
    const weatherLabels = Object.keys(data.weather_analysis);
    const weatherValues = Object.values(data.weather_analysis);
    const trendLabels = Object.keys(data.trend_analysis);
    const trendValues = Object.values(data.trend_analysis);

    new Chart(document.getElementById("airlineChart"), {
        type: "bar",
        data: {
            labels: airlineLabels,
            datasets: [{ label: "Predictions", data: airlineValues, backgroundColor: "#0d6efd" }]
        }
    });

    new Chart(document.getElementById("weatherChart"), {
        type: "pie",
        data: {
            labels: weatherLabels,
            datasets: [{ data: weatherValues, backgroundColor: ["#0d6efd", "#ffc107", "#20c997", "#dc3545"] }]
        }
    });

    new Chart(document.getElementById("trendChart"), {
        type: "line",
        data: {
            labels: trendLabels,
            datasets: [{ label: "Predictions Over Time", data: trendValues, borderColor: "#6610f2", fill: false, tension: 0.3 }]
        }
    });
}

async function retrainModel() {
    const result = await fetch("/api/retrain-model", { method: "POST" });
    const payload = await result.json();
    alert(payload.message || payload.error);
}

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
    const retrainBtn = document.getElementById("retrainBtn");
    if (retrainBtn) {
        retrainBtn.addEventListener("click", retrainModel);
    }
});
