const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const statusEl = document.getElementById("status");

function setStatus(text) {
  statusEl.textContent = text;
}

function updateUi(authenticated) {
  loginBtn.disabled = authenticated;
  logoutBtn.disabled = !authenticated;
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
    setStatus("Signed in as: " + response.accountEmail);
  }
});

