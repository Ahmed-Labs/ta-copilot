const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const statusEl = document.getElementById("status");
const pollingIndicator = document.getElementById("pollingIndicator");

function setStatus(text) {
  statusEl.textContent = text;
}

function setPollingActive(active) {
  if (!pollingIndicator) return;
  pollingIndicator.dataset.active = active ? "true" : "false";
}

function updateUi(authenticated) {
  if (authenticated) {
    loginBtn.style.display = "none";
    logoutBtn.disabled = false;
    setPollingActive(true);
  } else {
    loginBtn.style.display = "block";
    logoutBtn.disabled = true;
    setPollingActive(false);
  }
}

loginBtn.addEventListener("click", () => {
  setStatus("Opening Microsoft login...");
  chrome.runtime.sendMessage({ type: "LOGIN" }, (response) => {
    if (chrome.runtime.lastError) {
      setStatus("Login failed: " + chrome.runtime.lastError.message);
      updateUi(false);
      return;
    }
    if (response && response.ok) {
      const email = response.accountEmail || "unknown";
      setStatus("Signed in as: " + email + ". Polling inbox...");
      updateUi(true);
    } else {
      setStatus("Login failed.");
      updateUi(false);
    }
  });
});

logoutBtn.addEventListener("click", () => {
  chrome.runtime.sendMessage({ type: "LOGOUT" }, () => {
    setStatus("Signed out.");
    updateUi(false);
  });
});

// Initialize UI with current auth state from background
chrome.runtime.sendMessage({ type: "GET_AUTH_STATE" }, (response) => {
  const authed = response && response.authenticated;
  updateUi(authed);
  if (response && response.accountEmail) {
    setStatus("Signed in as: " + response.accountEmail + ". Polling inbox...");
  }
});

