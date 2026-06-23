const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const userIdInput = document.getElementById("userId");
const answerEl = document.getElementById("answer");
const authorsEl = document.getElementById("authors");

async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) {
    answerEl.textContent = "Please enter a message.";
    authorsEl.textContent = "";
    return;
  }

  answerEl.textContent = "Loading...";
  authorsEl.textContent = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        user_id: userIdInput.value.trim() || "frontend-user",
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Unknown request error");
    }

    answerEl.textContent = payload.answer || "(no answer)";
    authorsEl.textContent = (payload.authors || []).join("\n");
  } catch (error) {
    answerEl.textContent = `Request failed: ${error}`;
    authorsEl.textContent = "";
  }
}

sendBtn.addEventListener("click", sendMessage);
