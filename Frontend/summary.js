// window.onload = () => {
//   const summary = JSON.parse(localStorage.getItem('summary'));

//   if (summary) {
//     const mmse = summary.mmse_score || 0;
//     const facial = summary.facial_risk || 0;
//     const combined = summary.combined_risk || 0;

//     document.getElementById('mmse').innerText = mmse;
//     document.getElementById('facial').innerText = facial.toFixed(2);
//     document.getElementById('final').innerText = combined.toFixed(2);

//     // Animate risk bar
//     const riskBar = document.getElementById('riskBar');
//     const riskLabel = document.getElementById('riskLabel');

//     let color = "#22c55e";
//     let label = "Low Risk";

//     if (combined > 40 && combined <= 70) {
//       color = "#facc15";
//       label = "Moderate Risk";
//     } else if (combined > 70) {
//       color = "#ef4444";
//       label = "High Risk";
//     }

//     riskBar.style.backgroundColor = color;
//     setTimeout(() => {
//       riskBar.style.width = combined + "%";
//     }, 200);

//     riskLabel.innerText = label;
//     riskLabel.style.color = color;
//   } else {
//     document.body.innerHTML = "<h2>No summary data found. Please complete the test first.</h2>";
//   }
// };

// function redirectHome() {
//   localStorage.removeItem('summary');
//   window.location.href = "profile.html";
// }

window.onload = async () => {
  const summary = JSON.parse(localStorage.getItem('summary'));

  if (!summary) {
    document.body.innerHTML = "<h2>No summary data found. Please complete the test first.</h2>";
    return;
  }

  const userId = summary.user_id;
  const sessionId = summary.session_id;

  try {
    const response = await fetch(`http://127.0.0.1:5000/alzheimer_risk/${userId}/${sessionId}`);
    const data = await response.json();

    if (data.error) {
      document.body.innerHTML = `<h2>Error fetching risk: ${data.error}</h2>`;
      return;
    }

    const mmse = data.mmse_risk || 0;
    const facial = data.emotion_risk || 0;
    const combined = data.combined_risk || 0;

    document.getElementById('mmse').innerText = mmse.toFixed(2) + "%";
    document.getElementById('facial').innerText = facial.toFixed(2) + "%";
    document.getElementById('final').innerText = combined.toFixed(2) + "%";

    const riskBar = document.getElementById('riskBar');
    const riskLabel = document.getElementById('riskLabel');

    let color = "#22c55e";
    let label = "Low Risk";

    if (combined > 40 && combined <= 70) {
      color = "#facc15";
      label = "Moderate Risk";
    } else if (combined > 70) {
      color = "#ef4444";
      label = "High Risk";
    }

    riskBar.style.backgroundColor = color;
    setTimeout(() => {
      riskBar.style.width = combined + "%";
    }, 200);

    riskLabel.innerText = label;
    riskLabel.style.color = color;

  } catch (error) {
    console.error("Error loading Alzheimer’s risk:", error);
    document.body.innerHTML = `<h2>Failed to load Alzheimer’s data. Check backend connection.</h2>`;
  }
};

function redirectHome() {
  localStorage.removeItem('summary');
  window.location.href = "profile.html";
}
