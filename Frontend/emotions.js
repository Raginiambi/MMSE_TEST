const BASE_URL = "http://127.0.0.1:5000";

window.onload = async function() {
  // Extract session ID from URL (example: emotions.html?session_id=3)
  const urlParams = new URLSearchParams(window.location.search);
  const sessionId = urlParams.get("session_id");

  if (!sessionId) {
    alert("No session ID provided!");
    return;
  }

  document.getElementById("sessionTitle").textContent = `Session ID: ${sessionId}`;

  try {
    const res = await fetch(`${BASE_URL}/admin/emotions/${sessionId}`);
    const data = await res.json();

    if (res.status === 404) {
      alert("No emotion data found for this session.");
      return;
    }

    const ctx = document.getElementById("emotionChart").getContext("2d");
    new Chart(ctx, {
      type: "pie",
      data: {
        labels: Object.keys(data),
        datasets: [{
          data: Object.values(data),
          backgroundColor: [
            "#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#E91E63", "#00BCD4", "#FFEB3B"
          ],
        }],
      },
      options: {
        plugins: {
          title: {
            display: true,
            text: "Emotion Distribution",
            color: "white",
            font: { size: 18 }
          },
          legend: {
            labels: { color: "white" }
          }
        }
      }
    });
  } catch (err) {
    console.error("Error fetching emotions:", err);
    alert("Failed to load emotion data.");
  }
};
