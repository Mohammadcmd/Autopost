const scanScreen = document.getElementById("scan-screen");
const reviewScreen = document.getElementById("review-screen");
const postScreen = document.getElementById("post-screen");

const scanForm = document.getElementById("scan-form");
const scanPathInput = document.getElementById("scan-path");
const scanStatus = document.getElementById("scan-status");
const sessionList = document.getElementById("session-list");

const cardStack = document.getElementById("card-stack");
const reviewProgress = document.getElementById("review-progress");
const keepBtn = document.getElementById("keep-btn");
const deleteBtn = document.getElementById("delete-btn");
const undoBtn = document.getElementById("undo-btn");

const keptPhotosEl = document.getElementById("kept-photos");
const captionBox = document.getElementById("caption-box");
const regenerateBtn = document.getElementById("regenerate-btn");
const postBtn = document.getElementById("post-btn");
const postResult = document.getElementById("post-result");

let currentEventId = null;
let photos = [];
let currentIndex = 0;
let history = [];

function showScreen(screen) {
  for (const s of [scanScreen, reviewScreen, postScreen]) {
    s.classList.toggle("hidden", s !== screen);
  }
}

async function api(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json();
}

async function loadSessions() {
  const sessions = await api("/api/sessions");
  sessionList.innerHTML = "";
  for (const session of sessions) {
    for (const event of session.events) {
      const li = document.createElement("li");
      li.textContent = `${event.event_date} — ${event.photo_count} photos` +
        (event.website_event_name ? ` — ${event.website_event_name}` : "") +
        ` (${event.post_status})`;
      li.addEventListener("click", () => startReview(event.id));
      sessionList.appendChild(li);
    }
  }
}

scanForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  scanStatus.textContent = "Scanning…";
  try {
    const session = await api("/api/sessions/scan", {
      method: "POST",
      body: JSON.stringify({ path: scanPathInput.value }),
    });
    scanStatus.textContent = `Found ${session.events.length} event(s).`;
    await loadSessions();
    if (session.events.length > 0) {
      startReview(session.events[0].id);
    }
  } catch (err) {
    scanStatus.textContent = `Error: ${err.message}`;
  }
});

async function startReview(eventId) {
  currentEventId = eventId;
  photos = await api(`/api/events/${eventId}/photos`);
  currentIndex = 0;
  history = [];
  showScreen(reviewScreen);
  renderCard();
}

function renderCard() {
  if (currentIndex >= photos.length) {
    finishReview();
    return;
  }
  const photo = photos[currentIndex];
  reviewProgress.textContent = `Photo ${currentIndex + 1} of ${photos.length}`;
  cardStack.innerHTML = "";
  const img = document.createElement("img");
  img.src = `/api/photos/${photo.id}/image`;
  img.alt = "Edited photo";
  cardStack.appendChild(img);
}

async function decide(decision) {
  if (currentIndex >= photos.length) return;
  const photo = photos[currentIndex];
  await api(`/api/photos/${photo.id}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
  photo.decision = decision;
  history.push(currentIndex);
  currentIndex += 1;
  renderCard();
}

async function undo() {
  if (history.length === 0) return;
  currentIndex = history.pop();
  const photo = photos[currentIndex];
  await api(`/api/photos/${photo.id}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision: "pending" }),
  });
  photo.decision = "pending";
  renderCard();
}

keepBtn.addEventListener("click", () => decide("keep"));
deleteBtn.addEventListener("click", () => decide("delete"));
undoBtn.addEventListener("click", () => undo());

document.addEventListener("keydown", (e) => {
  if (reviewScreen.classList.contains("hidden")) return;
  if (e.key === "ArrowRight") decide("keep");
  if (e.key === "ArrowLeft") decide("delete");
  if (e.key.toLowerCase() === "u") undo();
});

async function finishReview() {
  showScreen(postScreen);
  const kept = photos.filter((p) => p.decision === "keep");
  keptPhotosEl.innerHTML = "";
  for (const photo of kept) {
    const img = document.createElement("img");
    img.src = `/api/photos/${photo.id}/image`;
    keptPhotosEl.appendChild(img);
  }

  const captionData = await api(`/api/events/${currentEventId}/caption`);
  captionBox.value = captionData.caption;
  postResult.textContent = "";
}

captionBox.addEventListener("change", async () => {
  await api(`/api/events/${currentEventId}/caption`, {
    method: "PUT",
    body: JSON.stringify({ caption: captionBox.value }),
  });
});

regenerateBtn.addEventListener("click", async () => {
  regenerateBtn.disabled = true;
  regenerateBtn.textContent = "Regenerating…";
  try {
    const captionData = await api(`/api/events/${currentEventId}/caption/regenerate`, {
      method: "POST",
    });
    captionBox.value = captionData.caption;
  } catch (err) {
    postResult.textContent = `Error: ${err.message}`;
  } finally {
    regenerateBtn.disabled = false;
    regenerateBtn.textContent = "↻ Regenerate caption";
  }
});

postBtn.addEventListener("click", async () => {
  postResult.textContent = "Posting…";
  try {
    const result = await api(`/api/events/${currentEventId}/post`, { method: "POST" });
    postResult.textContent = JSON.stringify(result, null, 2);
  } catch (err) {
    postResult.textContent = `Error: ${err.message}`;
  }
});

loadSessions();
