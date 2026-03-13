// Backend API base URL (no trailing slash). Override via chrome.storage.local "apiBaseUrl" if needed.
const DEFAULT_API_BASE = "https://localhost:8000";
const COMPOSE_COPILOT_BTN_ID = "ta-copilot-compose-btn";
// Stable selectors: data-testid and aria-labels stay the same across accounts; avoid dynamic ids (e.g. editorParent_2).
const COMPOSE_SEND_CONTAINER_SELECTOR = 'div[data-testid="ComposeSendButton"]';
const COMPOSE_EDITOR_SELECTOR =
  'div[role="textbox"][aria-label="Message body"][contenteditable="true"]';

/** Finds the compose toolbar (container that has both Send and Discard). Works in main frame and iframes. */
function findComposeToolbar() {
  const byTestId = document.querySelector(COMPOSE_SEND_CONTAINER_SELECTOR);
  if (byTestId && byTestId.parentElement) return byTestId.parentElement;
  const discardBtn =
    document.querySelector('button[aria-label="Discard"]') ||
    document.getElementById("discardCompose");
  if (discardBtn && discardBtn.parentElement) return discardBtn.parentElement;
  const sendBtn = document.querySelector('button[aria-label="Send"]');
  if (sendBtn) {
    let el = sendBtn.closest('div[class*="OTADH"]') || sendBtn.parentElement;
    for (let i = 0; i < 8 && el; i++) {
      if (el.querySelector('button[aria-label="Discard"]')) return el;
      el = el.parentElement;
    }
  }
  return null;
}

function getEmailIdFromUrl() {
  const path = window.location.pathname || "";
  // e.g. /mail/inbox/id/AAQkAGI5... or /mail/view/id/...
  const match = path.match(/\/mail\/[^/]+\/id\/([^/]+)/);
  if (!match) return null;
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
}

function getApiBaseUrl(cb) {
  try {
    chrome.storage.local.get(["apiBaseUrl"], (items) => {
      cb(items.apiBaseUrl && items.apiBaseUrl.trim() ? items.apiBaseUrl.trim().replace(/\/$/, "") : DEFAULT_API_BASE);
    });
  } catch {
    cb(DEFAULT_API_BASE);
  }
}

function ensureComposeButtonStyles() {
  if (document.getElementById("ta-copilot-compose-btn-style")) return;
  const style = document.createElement("style");
  style.id = "ta-copilot-compose-btn-style";
  style.textContent = `
    #ta-copilot-compose-btn.ta-copilot-compose-btn {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #18181b;
      color: #e5e7eb;
      border: 1px solid #3f3f46;
      border-radius: 6px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 500;
      margin-left: 2px;
      cursor: pointer;
      transition: background-color 0.18s ease, border-color 0.18s ease;
    }
    #ta-copilot-compose-btn.ta-copilot-compose-btn:hover {
      background: #27272f;
      border-color: #52525b;
    }
    #ta-copilot-compose-btn.ta-copilot-compose-btn:active {
      background: #1f1f25;
      border-color: #3f3f46;
    }
    #ta-copilot-compose-btn.ta-copilot-compose-btn:focus-visible {
      outline: 2px solid #8b5cf6;
      outline-offset: 2px;
    }
  `;
  document.head.appendChild(style);
}

function createComposeCopilotButton() {
  if (document.getElementById(COMPOSE_COPILOT_BTN_ID)) return null;
  ensureComposeButtonStyles();
  const btn = document.createElement("button");
  btn.id = COMPOSE_COPILOT_BTN_ID;
  btn.className = "ta-copilot-compose-btn";
  btn.type = "button";
  btn.setAttribute("aria-label", "TA Copilot");
  btn.textContent = "TA Copilot";
  return btn;
}

function showReplyModal(suggestedReply) {
  const overlay = document.createElement("div");
  overlay.id = "ta-copilot-modal-overlay";
  overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:999999;display:flex;align-items:center;justify-content:center;padding:20px;";
  const box = document.createElement("div");
  box.style.cssText = "background:#1e1e2e;color:#e4e4e7;border-radius:12px;max-width:480px;width:100%;max-height:80vh;overflow:hidden;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5);font-family:system-ui,sans-serif;";
  box.innerHTML = `
    <div style="padding:16px 20px;border-bottom:1px solid #313244;">
      <strong style="font-size:15px;">TA Copilot – Suggested reply</strong>
    </div>
    <div style="padding:16px 20px;overflow-y:auto;max-height:50vh;white-space:pre-wrap;font-size:13px;line-height:1.5;">${escapeHtml(suggestedReply)}</div>
    <div style="padding:12px 20px;border-top:1px solid #313244;display:flex;justify-content:flex-end;gap:8px;">
      <button id="ta-copilot-modal-copy" style="padding:8px 16px;border-radius:8px;border:none;background:#7c3aed;color:#fff;cursor:pointer;font-size:13px;">Copy to clipboard</button>
      <button id="ta-copilot-modal-close" style="padding:8px 16px;border-radius:8px;border:1px solid #45475a;background:transparent;color:#e4e4e7;cursor:pointer;font-size:13px;">Close</button>
    </div>
  `;
  overlay.appendChild(box);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) closeModal(); });
  document.body.appendChild(overlay);

  document.getElementById("ta-copilot-modal-copy").addEventListener("click", () => {
    navigator.clipboard.writeText(suggestedReply).then(() => {
      const copyBtn = document.getElementById("ta-copilot-modal-copy");
      if (copyBtn) { copyBtn.textContent = "Copied!"; setTimeout(() => { copyBtn.textContent = "Copy to clipboard"; }, 1500); }
    });
  });
  document.getElementById("ta-copilot-modal-close").addEventListener("click", closeModal);
  function closeModal() {
    overlay.remove();
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showToast(message, isError = false) {
  const el = document.createElement("div");
  el.id = "ta-copilot-toast";
  el.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);padding:12px 20px;border-radius:8px;background:" + (isError ? "#f87171" : "#22c55e") + ";color:#fff;font-size:13px;font-family:system-ui,sans-serif;z-index:1000000;box-shadow:0 10px 25px rgba(0,0,0,0.2);";
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function injectComposeButton() {
  const parent = findComposeToolbar();
  if (!parent) return;
  if (document.getElementById(COMPOSE_COPILOT_BTN_ID)) return;

  attachComposeButton(parent);
}

function attachComposeButton(parent) {
  const existing = document.getElementById(COMPOSE_COPILOT_BTN_ID);
  const btn = existing || createComposeCopilotButton();
  if (!btn) return;

  if (!existing) {
    btn.addEventListener("click", () => {
      const editor =
        document.querySelector(COMPOSE_EDITOR_SELECTOR) ||
        document.querySelector('div[role="textbox"][aria-label="Message body"]');
      if (!editor) {
        showToast("Could not find compose editor.", true);
        return;
      }
      editor.innerHTML = "<div>Hello world</div>";
    });

    const discardButton = parent.querySelector('button[aria-label="Discard"]');
    if (discardButton && discardButton.parentElement) {
      discardButton.parentElement.insertBefore(btn, discardButton);
    } else {
      parent.appendChild(btn);
    }
  }
}

function run() {
  injectComposeButton();
  const observer = new MutationObserver(() => {
    injectComposeButton();
  });
  observer.observe(document.body, { childList: true, subtree: true });
  let lastPath = location.pathname;
  setInterval(() => {
    if (location.pathname !== lastPath) {
      lastPath = location.pathname;
      document.getElementById(COMPOSE_COPILOT_BTN_ID)?.remove();
      injectComposeButton();
    }
  }, 500);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", run);
} else {
  run();
}
