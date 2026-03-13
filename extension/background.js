const TENANT_ID = "common";
const CLIENT_ID = "0f964efa-01d5-446c-8e2f-07b13cc4f37b";
// Hard-coded webhook URL that Microsoft Graph will call directly.
// Replace this with your real webhook URL (e.g. your Lambda endpoint).
const FINAL_WEBHOOK_URL = "https://u2s7sdw8xg.execute-api.us-west-2.amazonaws.com/webhook/outlook";
const POLL_ALARM_NAME = "ta-copilot-poll-inbox";
// Chrome alarms effectively wake up at ~1 minute granularity.
// To get "more frequent" checks, we wake every minute and then do a short burst of
// additional polls while the service worker is awake.
const POLL_PERIOD_MINUTES = 1;
const FAST_POLL_INTERVAL_MS = 15000; // 15s
const FAST_POLL_COUNT = 3; // do 3 extra polls after each wake

// We use OAuth 2 implicit flow with chrome.identity.launchWebAuthFlow for simplicity.
// For production, consider using the auth code flow with PKCE instead.

async function getAuthUrl() {
  const redirectUri = chrome.identity.getRedirectURL("oauth2");
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: "token",
    redirect_uri: redirectUri,
    response_mode: "fragment",
    scope: "openid profile offline_access https://graph.microsoft.com/Mail.Read",
  });

  return `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/authorize?${params.toString()}`;
}

function parseFragment(fragment) {
  const params = new URLSearchParams(fragment.replace(/^#/, ""));
  const result = {};
  for (const [key, value] of params.entries()) {
    result[key] = value;
  }
  return result;
}

function decodeJwtPayload(token) {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64);
    return JSON.parse(json);
  } catch (_e) {
    return null;
  }
}

async function loginInteractive() {
  const authUrl = await getAuthUrl();

  return new Promise((resolve, reject) => {
    chrome.identity.launchWebAuthFlow(
      { url: authUrl, interactive: true },
      (redirectUrl) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        if (!redirectUrl) {
          reject(new Error("No redirect URL returned from auth flow"));
          return;
        }

        const fragment = redirectUrl.split("#")[1] || "";
        const tokenData = parseFragment(fragment);

        if (!tokenData.access_token) {
          reject(new Error("No access token returned"));
          return;
        }

        const expiresIn = Number(tokenData.expires_in || "3600");
        const expiresAt = Date.now() + expiresIn * 1000;
        const claims = decodeJwtPayload(tokenData.access_token);
        const email =
          (claims &&
            (claims.preferred_username ||
              claims.upn ||
              claims.email ||
              claims.unique_name)) ||
          null;

        chrome.storage.local.set(
          {
            graphAccessToken: tokenData.access_token,
            graphTokenExpiresAt: expiresAt,
            graphUserEmail: email,
          },
          () => resolve({ ...tokenData, email })
        );
      }
    );
  });
}

async function getStoredToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      ["graphAccessToken", "graphTokenExpiresAt"],
      (items) => {
        if (!items.graphAccessToken || !items.graphTokenExpiresAt) {
          resolve(null);
          return;
        }
        if (Date.now() >= items.graphTokenExpiresAt) {
          resolve(null);
          return;
        }
        resolve(items.graphAccessToken);
      }
    );
  });
}

async function getStoredEmail() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["graphUserEmail"], (items) => {
      resolve(items.graphUserEmail || null);
    });
  });
}

async function getAccessTokenEnsured() {
  const existing = await getStoredToken();
  if (existing) return existing;
  const tokenData = await loginInteractive();
  return tokenData.access_token;
}

function clearToken() {
  return new Promise((resolve) => {
    chrome.storage.local.remove(
      ["graphAccessToken", "graphTokenExpiresAt"],
      () => resolve()
    );
  });
}

async function setLastSeenReceivedDateTime(isoString) {
  return new Promise((resolve) => {
    chrome.storage.local.set(
      { lastSeenReceivedDateTime: isoString || null },
      () => resolve()
    );
  });
}

async function getLastSeenReceivedDateTime() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["lastSeenReceivedDateTime"], (items) => {
      resolve(items.lastSeenReceivedDateTime || null);
    });
  });
}

async function postMessageToWebhook(message) {
  const payload = {
    source: "ta-copilot-extension",
    receivedAt: new Date().toISOString(),
    message,
  };

  console.log("[ta-copilot] Posting message to webhook", {
    id: message.id,
    subject: message.subject,
  });

  const res = await fetch(FINAL_WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    console.error("[ta-copilot] Webhook POST failed", res.status, text);
    throw new Error(`Webhook POST failed: ${res.status}`);
  }

  console.log("[ta-copilot] Webhook POST succeeded", res.status);
}

async function listRecentInboxMessages(accessToken) {
  // Start with a simple query that works broadly.
  const url =
    "https://graph.microsoft.com/v1.0/me/mailFolders('Inbox')/messages" +
    "?$top=10" +
    "&$orderby=receivedDateTime desc" +
    "&$select=id,subject,receivedDateTime,from,bodyPreview,webLink";

  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    console.error("[ta-copilot] Graph list messages failed", res.status, text);
    throw new Error(`Graph list messages failed: ${res.status}`);
  }

  return res.json();
}

async function fetchMessageById(accessToken, id) {
  const url =
    `https://graph.microsoft.com/v1.0/me/messages/${encodeURIComponent(id)}` +
    "?$select=id,subject,receivedDateTime,from,toRecipients,ccRecipients,body,bodyPreview,webLink,internetMessageId";

  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    console.error("[ta-copilot] Graph fetch message failed", res.status, text);
    throw new Error(`Graph fetch message failed: ${res.status}`);
  }

  return res.json();
}

async function pollInboxOnce() {
  const token = await getStoredToken();
  if (!token) {
    console.log("[ta-copilot] Poll skipped: no valid token");
    return;
  }

  const lastSeen = await getLastSeenReceivedDateTime();
  console.log("[ta-copilot] Polling inbox", { lastSeen });

  const listing = await listRecentInboxMessages(token);
  const items = (listing && listing.value) || [];

  if (items.length === 0) {
    console.log("[ta-copilot] No messages returned from Graph");
    return;
  }

  // Items are sorted desc by receivedDateTime.
  const newest = items[0].receivedDateTime || null;

  const newItems = lastSeen
    ? items.filter((m) => m.receivedDateTime && m.receivedDateTime > lastSeen)
    : items.slice(0, 1); // first run: only send the newest message

  console.log("[ta-copilot] Poll results", {
    totalFetched: items.length,
    newCount: newItems.length,
    newestReceivedDateTime: newest,
  });

  // Process from oldest -> newest to preserve ordering.
  const ordered = [...newItems].sort((a, b) =>
    String(a.receivedDateTime).localeCompare(String(b.receivedDateTime))
  );

  for (const item of ordered) {
    try {
      const full = await fetchMessageById(token, item.id);
      await postMessageToWebhook(full);
    } catch (e) {
      console.error("[ta-copilot] Failed to publish message", item.id, e);
    }
  }

  // Advance cursor to newest we observed (even if webhook failed for some items).
  if (newest) {
    await setLastSeenReceivedDateTime(newest);
    console.log("[ta-copilot] Updated lastSeenReceivedDateTime", newest);
  }
}

async function startBackgroundPolling() {
  console.log("[ta-copilot] Starting background polling", {
    alarm: POLL_ALARM_NAME,
    periodMinutes: POLL_PERIOD_MINUTES,
    fastPollIntervalMs: FAST_POLL_INTERVAL_MS,
    fastPollCount: FAST_POLL_COUNT,
  });
  chrome.alarms.create(POLL_ALARM_NAME, { periodInMinutes: POLL_PERIOD_MINUTES });
  // Kick an immediate poll so you don't have to wait for the first alarm tick.
  try {
    await pollInboxOnce();
  } catch (e) {
    console.error("[ta-copilot] Immediate poll failed", e);
  }
}

function runFastPollBurst() {
  for (let i = 1; i <= FAST_POLL_COUNT; i++) {
    setTimeout(() => {
      pollInboxOnce().catch((e) =>
        console.error("[ta-copilot] Fast poll error", { attempt: i }, e)
      );
    }, FAST_POLL_INTERVAL_MS * i);
  }
}

async function stopBackgroundPolling() {
  console.log("[ta-copilot] Stopping background polling", { alarm: POLL_ALARM_NAME });
  await chrome.alarms.clear(POLL_ALARM_NAME);
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  (async () => {
    try {
      if (message.type === "LOGIN") {
        const tokenData = await loginInteractive();
        const email = tokenData.email || null;
        await startBackgroundPolling();
        console.log("[ta-copilot] Login completed", { email });
        sendResponse({ ok: true, accountEmail: email });
      } else if (message.type === "LOGOUT") {
        await clearToken();
        await stopBackgroundPolling();
        sendResponse({ ok: true });
      } else if (message.type === "GET_AUTH_STATE") {
        const token = await getStoredToken();
        const email = await getStoredEmail();
        sendResponse({
          authenticated: !!token,
          accountEmail: email,
        });
      } else {
        sendResponse({ ok: false, error: "Unknown message type" });
      }
    } catch (err) {
      sendResponse({ ok: false, error: String(err.message || err) });
    }
  })();

  return true; // keep the message channel open for async response
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm && alarm.name === POLL_ALARM_NAME) {
    pollInboxOnce().catch((e) => console.error("[ta-copilot] Poll alarm error", e));
    runFastPollBurst();
  }
});

chrome.runtime.onInstalled.addListener(() => {
  // If the user is already signed in, resume polling after install/update.
  pollInboxOnce()
    .then(async () => {
      const token = await getStoredToken();
      if (token) {
        await startBackgroundPolling();
      }
    })
    .catch(() => {
      // ignore
    });
});

