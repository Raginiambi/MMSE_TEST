// Base URL of your backend
const BASE_URL = 'http://127.0.0.1:5000';
let testCompleted = false; // ✅ ensures end logic runs only once


// --------------------- LOGIN ---------------------
function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  })
    .then(res => res.json())
    .then(data => {
      if (data.user) {
        const user = data.user;
        localStorage.setItem("user", JSON.stringify(data.user));
        if (user.role === 'main_host') {
          window.location.href = "admin_dashboard.html";
        } else {
          window.location.href = "profile.html";
        }
      } else {
        alert("Login failed: " + (data.error || "Unknown error"));
      }
    });
}

// function startTest() {
//   const user = JSON.parse(localStorage.getItem("user"));
//   if (!user) {
//     alert("Please log in first!");
//     window.location.href = "login.html";
//     return;
//   }

//   fetch(`${BASE_URL}/start_test/${user.id}`, {
//     method: "POST"
//   })
//     .then(res => res.json())
//     .then(data => {
//       // save session id for later answers
//       localStorage.setItem("testSessionId", data.test_session_id);
//       console.log("✅ Test session started:", data.test_session_id);

//       // now load first question
// showQuestion()
//   });
// }

let currentTestSessionId = null;  // ✅ Global variable


async function startTest(userId) {
    const res = await fetch(`${BASE_URL}/start_test/${userId}`, { method: "POST" });
    const data = await res.json();
    currentTestSessionId = data.test_session_id;
    localStorage.setItem("testSessionId", currentTestSessionId);  // ✅ persist in storage
    console.log("🆕 Test Session Started:", currentTestSessionId);
}



// --------------------- REGISTER ---------------------
function register() {
  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const age = document.getElementById("age").value;
  const gender = document.getElementById("gender").value;
  const Location = document.getElementById("location").value;
  

  fetch(`${BASE_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, age, gender })
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message);
      window.location.href = "login.html";
    });
}

// --------------------- PROFILE ---------------------
function loadProfile() {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user) {
    window.location.href = "login.html";
    return;
  }

  document.getElementById("profile").innerHTML = `
    <p><strong>Name:</strong> ${user.name}</p>
    <p><strong>Email:</strong> ${user.email}</p>
    <p><strong>Age:</strong> ${user.age}</p>
    <p><strong>Gender:</strong> ${user.gender}</p>
    
  `;
}

// --------------------- MMSE TEST ---------------------
let mmseQuestions = [];
let currentIndex = 0;
let startTime = null;

async function loadMMSETest() {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user) {
    alert("Please log in first!");
    window.location.href = "login.html";
    return;
  }

  // Confirm consent for recording
  const consent = confirm("We will record a short video of your face during the test for research/analysis. Do you consent?");
  if (!consent) return;

  // Start camera recording first
  await startCameraRecording();

  // Start test session
  const res = await fetch(`${BASE_URL}/start_test/${user.id}`, { method: "POST" });
  const data = await res.json();
  const testSessionId = data.test_session_id;

  if (!testSessionId) {
    alert("Failed to start test session");
    return;
  }

  localStorage.setItem("testSessionId", testSessionId);
  currentTestSessionId = testSessionId;

  // Fetch questions
  try {
    const questionsRes = await fetch(`${BASE_URL}/questions`);
    const questionsData = await questionsRes.json();
    mmseQuestions = questionsData;
    currentIndex = 0;

    // Show first question
    showQuestion();
  } catch (err) {
    console.error("Failed to load questions:", err);
    alert("Could not load test questions.");
  }
}


// async function loadMMSETest() {

//   const user = JSON.parse(localStorage.getItem("user"));
//   if (!user) {
//     alert("Please log in first!");
//     window.location.href = "login.html";
//     return;
//   }

//   // ✅ Start test session before loading questions
//    await startCameraRecording();  
//   await startTest(user.id);
//   fetch(`${BASE_URL}/questions`)
//     .then(res => res.json())
//     .then(data => {
//       mmseQuestions = data;
//       currentIndex = 0;
//       showQuestion(); // will now use renderQuestion
//     });
// }

async function showQuestion() {
  // if (currentIndex >= mmseQuestions.length) {
  //   alert("Test completed!");
  //   window.location.href = "summary.html";
  //   return;
  // }
  if (currentIndex >= mmseQuestions.length) {
  if (testCompleted) stopCameraRecordingAndUpload(); // ✅ prevent multiple executions
  testCompleted = true;

  console.log("✅ All questions completed");

  try {
    console.log("⏹️ Stopping camera recording...");
    await stopCameraRecordingAndUpload();
    console.log("🎥 Video upload done, redirecting...");

    const testSessionId = localStorage.getItem("testSessionId");
    if (testSessionId) {
      // Optional: tell backend test has ended
      await fetch(`${BASE_URL}/end_test/${testSessionId}`, { method: "POST" });
    }

    alert("Test completed successfully!");
    window.location.href = `summary.html?session_id=${testSessionId}`;
  } catch (err) {
    console.error("❌ Error ending test:", err);
    const testSessionId = localStorage.getItem("testSessionId");
    alert("Test completed, but upload failed or redirection error.");
    window.location.href = `summary.html?session_id=${testSessionId}`;
  }

  return; // stop further execution
}


  //  await startCameraRecording();

  const question = mmseQuestions[currentIndex];
  startTime = Date.now();

  // Call the dynamic renderer
  renderQuestion(question);
}

// async function submitAnswer() {
//   const answer = document.getElementById("answerInput").value;
//   const user = JSON.parse(localStorage.getItem("user"));
//   const questionId = mmseQuestions[currentIndex].id;
//   const timeTaken = ((Date.now() - startTime) / 1000).toFixed(2);

  

//   const testSessionId = currentTestSessionId || localStorage.getItem("testSessionId");
//    if (!user || !testSessionId) {
//     alert("No active test session. Please restart the test.");
//     return;
//   }


//   const response = await fetch(`${BASE_URL}/submit_answer`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({
//       user_id: user.id,
//       question_id: questionId,
//       answer: answer,
//       time_taken: timeTaken,
//      test_session_id: testSessionId
//     })
//   }).then(res => res.json())
//     .then(() => {
//       currentIndex++;
//        if (currentIndex >= mmseQuestions.length) {
//          stopCameraRecordingAndUpload();
//     console.log("✅ Test completed! Preparing summary...");
//   console.log("Summary saved:", localStorage.getItem("summary"));
//   window.location.href = "summary.html";
  
//   } else {
//     showQuestion();
//   }
//     });
// }

async function submitAnswer() {
  let answer = document.getElementById("answerInput").value;
  const user = JSON.parse(localStorage.getItem("user"));
  const questionId = mmseQuestions[currentIndex].id;
  const timeTaken = ((Date.now() - startTime) / 1000).toFixed(2);

  const testSessionId = currentTestSessionId || localStorage.getItem("testSessionId");
  if (!user || !testSessionId) {
    alert("No active test session. Please restart the test.");
    return;
  }

  
  const textInput = document.getElementById("answerInput");
  const selectedOption = document.querySelector('input[name="options"]:checked');

    if (textInput) {
    answer = textInput.value.trim();
    if (answer === "") {
      textInput.style.border = "2px solid red";
      alert("⚠️ Please enter your answer before continuing.");
      return;
    }
  } 
  // If question is MCQ-based
  else if (selectedOption) {
    answer = selectedOption.value;
  } 
  else {
    alert("⚠️ Please select an option before continuing.");
    return;
  }

  try {
    await fetch(`${BASE_URL}/submit_answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: user.id,
        question_id: questionId,
        answer: answer,
        time_taken: timeTaken,
        test_session_id: testSessionId,
      }),
    });

    currentIndex++;

    if (currentIndex >= mmseQuestions.length) {
      console.log("✅ Test completed! Stopping camera and uploading...");
      // ✅ Await ensures upload completes before redirect
      await stopCameraRecordingAndUpload();

      console.log("✅ Upload finished, now redirecting...");
      window.location.href = "summary.html";
    } else {
      showQuestion();
    }
  } catch (err) {
    console.error("❌ Error submitting answer:", err);
    alert("Something went wrong while submitting your answer. Please try again.");
  }
}




function loadScoreHistory() {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user) return window.location.href = "login.html";

  fetch(`${BASE_URL}/score_history/${user.id}`)
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("summary-container");
      if (data.length === 0) {
        container.innerHTML = "<p>No history found.</p>";
        return;
      }

      let html = `<table border="1"><tr><th>Question</th><th>Answer</th><th>Score</th><th>Time Taken</th><th>Date</th></tr>`;
      data.forEach(row => {
        html += `<tr>
          <td>${row.question_text}</td>
          <td>${row.answer}</td>
          <td>${row.score_awarded}</td>
          <td>${row.time_taken_seconds}s</td>
          <td>${new Date(row.submitted_at).toLocaleString()}</td>
        </tr>`;
      });
      html += `</table>`;
      container.innerHTML = html;
    });
}


async function renderQuestion(question) {

  const container = document.getElementById('question-area');
  container.innerHTML = `<h3 id="question-text">Q${question.id}: ${question.question_text}</h3>`;

  // Clear previous answer input
  let inputHTML = '';

  // Handle types
  switch (question.answer_type) {


    case 'image_choice':
      inputHTML = `<div id="image-options">`;
      question.options.forEach((imgSrc, idx) => {
        inputHTML += `
          <img src="images/${imgSrc}" 
               alt="Option ${idx}" 
               class="choice-img"
               onclick="selectImageOption(this, '${imgSrc}')">
        `;
      });
      inputHTML += `</div><input type="hidden" id="answerInput">`;
      break;
    
    case 'img_sequence':
      inputHTML = `
        <div class="image-row">
          <img src="images/apple.avif" class="sequence_img" alt="Apple">
          <img src="images/chair.jpeg" class="sequence_img" alt="Chair">
          <img src="images/pencil.avif" class="sequence_img" alt="Pencil">
        </div>
        <input type="text" id="answerInput" 
               class="answer-box" 
               placeholder="Type in order">
      `;
      break;
 case 'img_show':
  if (question.image) {
    // Case A: Single image with options
    inputHTML = `
      <div class="image-row">
        <img src="images/${question.image}" class="question-img" alt="Question Image">
      </div>
    `;

    inputHTML += `<div id="mcq-options" class="mcq-container">`;
    question.options.forEach(opt => {
      inputHTML += `
        <div class="mcq-option" onclick="selectMCQOption(this, '${opt}')">
          ${opt}
        </div>`;
    });
    inputHTML += `</div><input type="hidden" id="answerInput">`;

  } else {
    // Case B: Sequence recall (your old logic)
    inputHTML = `<div class="image-row">`;
    question.options.forEach(imgSrc => {
      inputHTML += `<img src="images/${imgSrc}" class="sequence_img" alt="Sequence Object">`;
    });
    inputHTML += `</div>`;

    // Generate random sequences
    let sequences = [
      question.options,
      [question.options[1], question.options[2], question.options[0]],
      [question.options[2], question.options[0], question.options[1]],
      [question.options[2], question.options[1], question.options[0]]
    ].sort(() => Math.random() - 0.5);

    inputHTML += `<div id="mcq-options" class="mcq-container">`;
    sequences.forEach(seq => {
      let displayName = seq.map(s => s.split('.')[0]).join(", ");
      let value = seq.join(",");
      inputHTML += `
        <div class="mcq-option" onclick="selectMCQOption(this, '${value}')">
          ${displayName}
        </div>`;
    });
    inputHTML += `</div><input type="hidden" id="answerInput">`;
  }
  break;


    case 'multiple_choice':
      inputHTML = `<div id="mcq-options" class="mcq-container">`;
      question.options.forEach((opt, idx) => {
      inputHTML += `
      <div class="mcq-option" onclick="selectMCQOption(this, '${opt}')">
        ${opt}
      </div>`;
  });
  inputHTML += `</div>`;
  inputHTML += `<input type="hidden" id="answerInput">`; 
  break;

    case 'img_with_mcq':
  // Hardcode or fetch the image for this question
  inputHTML = `
    <div class="image-row">
      <img src="images/pencil.avif" class="question-img" alt="Pencil">
    </div>
  `;

  inputHTML += `<div id="mcq-options" class="mcq-container">`;
  question.options.forEach(opt => {
    inputHTML += `
      <div class="mcq-option" onclick="selectMCQOption(this, '${opt}')">
        ${opt}
      </div>`;
  });
  inputHTML += `</div><input type="hidden" id="answerInput">`;
  break;


    default:
      inputHTML = `<input type="text" id="answerInput" class="answer-box" placeholder="Your answer here">`;
      break;
  }

  // Add Submit Button
  inputHTML += `<br><button onclick="submitAnswer()" class="submit-btn">Submit</button>`;
  container.innerHTML += inputHTML;
}
function selectMCQOption(element, value) {
  // remove previous active state
  document.querySelectorAll('.mcq-option').forEach(opt => opt.classList.remove('selected'));
  
  // add active state
  element.classList.add('selected');
  
  // set hidden input
  document.getElementById("answerInput").value = value;
}
function selectImageOption(element, value) {
  document.getElementById('answerInput').value = value;

  // Highlight selection
  document.querySelectorAll(".choice-img").forEach(img => img.classList.remove('selected'));
  element.classList.add('selected');
}

// --- recording globals ---
let mediaRecorder = null;
let recordedChunks = [];
let localStream = null;

// Called when user clicks Start Test on profile page
async function beginMMSETest() {
  const user = JSON.parse(localStorage.getItem("user"));
  if (!user) {
    alert("Please log in first!");
    window.location.href = "login.html";
    return;
  }

  const consent = confirm("We will record a short video of your face during the test for research/analysis. Do you consent?");
  if (!consent) return;

  try {
    const res = await fetch(`${BASE_URL}/start_test/${user.id}`, { method: "POST" });
    const data = await res.json();
    if (data.test_session_id) {
      localStorage.setItem("testSessionId", data.test_session_id);
      window.location.href = "mmse_test.html";
    } else {
      alert("Failed to start test");
    }
  } catch (err) {
    console.error("start_test error", err);
    alert("Could not start test session");
  }
}

async function startCameraRecording() {
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  } catch (err) {
    console.error("getUserMedia error:", err);
    alert("Camera access is required to record. Please allow camera & microphone.");
    return;
  }

  const preview = document.getElementById("preview");
  if (preview) {
    preview.style.display = "block";
    preview.srcObject = localStream;
    await preview.play().catch(() => {});
  }

  recordedChunks = [];
  const options = { mimeType: "video/webm;codecs=vp8" };
  mediaRecorder = new MediaRecorder(localStream, options);

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) recordedChunks.push(e.data);
  };

  mediaRecorder.start();
  console.log("🎥 Recording started...");
}


async function stopCameraRecordingAndUpload() {
  return new Promise((resolve) => {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      console.warn("No active recording to stop");
      return resolve(); // Resolve immediately if nothing to stop
    }

    mediaRecorder.onstop = async () => {
      console.log("🎞️ Recording stopped. Preparing upload...");
      const blob = new Blob(recordedChunks, { type: "video/webm" });

      try {
        await uploadSessionVideo(blob);
        console.log("✅ Video uploaded successfully!");
      } catch (err) {
        console.error("❌ Upload failed:", err);
      }

      // stop camera
      if (localStream) {
        localStream.getTracks().forEach((track) => track.stop());
        localStream = null;
      }

      resolve(); // ✅ Make sure promise resolves no matter what
    };

    // In case the recorder never fires 'onstop', set a fallback timer
    setTimeout(() => {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        console.warn("⏱️ Forcing stopCameraRecordingAndUpload() resolve (timeout)");
        mediaRecorder.stop();
      }
    }, 5000); // fallback after 5s

    console.log("🛑 Stopping recording...");
    mediaRecorder.stop();
  });
}


// Upload the video blob to Flask endpoint
async function uploadSessionVideo(blob) {
  const testSessionId = localStorage.getItem("testSessionId");
  if (!testSessionId) {
    console.error("uploadSessionVideo: missing testSessionId");
    return;
  }

  const form = new FormData();
  form.append("video", blob, `session_${testSessionId}.webm`);
  form.append("test_session_id", testSessionId);

  try {
    const res = await fetch(`${BASE_URL}/upload_session_video`, {
      method: "POST",
      body: form
    });
    const data = await res.json();
    console.log("upload_session_video response:", data);
  } catch (err) {
    console.error("uploadSessionVideo failed:", err);
  }
}



function submitImageAnswer(selectedImage, questionId) {
  const user = JSON.parse(localStorage.getItem("user"));


  const payload = {
    user_id: user.id,
    question_id: questionId,
    answer: selectedImage,
    time_taken: 3, // adjust with actual timer if used
    
  };

  fetch("http://127.0.0.1:5000/submit_answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(data => {
    console.log("Answer submitted:", data);
    loadNextQuestion(); // or however you're loading next one
  });
}

async function calculateAlzheimerRisk(userId, sessionId) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/alzheimer_risk/${userId}/${sessionId}`);
        const data = await response.json();
        if (data.alzheimer_risk_percent !== undefined) {
            const risk = data.alzheimer_risk_percent;
            document.getElementById("riskPercent").innerText = `Alzheimer Risk: ${risk}%`;

            // Color coding
            let color = "green";
            if (risk > 60) color = "red";
            else if (risk > 30) color = "orange";
            document.getElementById("riskPercent").style.color = color;
        } else {
            console.error("Error fetching risk:", data.error);
        }
    } catch (err) {
        console.error("Exception:", err);
    }
}

async function submitTestAndVideo(userId, sessionId, answers, videoFile) {
    // 1️⃣ Submit all answers
    for (let answer of answers) {
        await fetch('http://127.0.0.1:5000/submit_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({...answer, user_id: userId, test_session_id: sessionId})
        });
    }

    // 2️⃣ Upload video
    let formData = new FormData();
    formData.append('video', videoFile);
    formData.append('test_session_id', sessionId);

    await fetch('http://127.0.0.1:5000/upload_session_video', {
        method: 'POST',
        body: formData
    });

    // 3️⃣ Fetch and display Alzheimer risk
    calculateAlzheimerRisk(userId, sessionId);
}
