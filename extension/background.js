const TENANT_ID = "common";
const CLIENT_ID = "0f964efa-01d5-446c-8e2f-07b13cc4f37b";
// Hard-coded webhook URL that Microsoft Graph will call directly.
// Replace this with your real webhook URL (e.g. your Lambda endpoint).
const FINAL_WEBHOOK_URL = "https://u2s7sdw8xg.execute-api.us-west-2.amazonaws.com/webhook/outlook";

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

async function createSubscription() {
  const accessToken = await getAccessTokenEnsured();

  // Subscriptions to new inbox messages, notifying our webhook URL.
  const expiration = new Date(Date.now() + 60 * 60 * 1000).toISOString(); // 1 hour from now
  const body = {
    changeType: "created",
    notificationUrl: FINAL_WEBHOOK_URL,
    resource: "me/mailFolders('Inbox')/messages",
    expirationDateTime: expiration,
    clientState: "ta-copilot",
  };

  console.log("[ta-copilot] Creating Graph subscription", {
    notificationUrl: FINAL_WEBHOOK_URL,
    resource: body.resource,
    expirationDateTime: body.expirationDateTime,
  });

  const res = await fetch("https://graph.microsoft.com/v1.0/subscriptions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    console.error("[ta-copilot] Graph subscription creation failed", res.status, errText);
    throw new Error(`Backend error: ${res.status} ${errText}`);
  }

  const data = await res.json();
  console.log("[ta-copilot] Graph subscription created", {
    id: data.id,
    expirationDateTime: data.expirationDateTime,
  });
  return data;
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  (async () => {
    try {
      if (message.type === "LOGIN") {
        const tokenData = await loginInteractive();
        const email = tokenData.email || null;
        let subscription = null;
        try {
          subscription = await createSubscription();
        } catch (e) {
          console.error(
            "[ta-copilot] Error during subscription creation on login",
            e
          );
        }
        console.log("[ta-copilot] Login completed", {
          email,
          hasSubscription: !!subscription,
          expirationDateTime: subscription
            ? subscription.expirationDateTime
            : undefined,
        });
        sendResponse({
          ok: true,
          accountEmail: email,
          expirationDateTime: subscription
            ? subscription.expirationDateTime
            : undefined,
        });
      } else if (message.type === "LOGOUT") {
        await clearToken();
        sendResponse({ ok: true });
      } else if (message.type === "CREATE_SUBSCRIPTION") {
        // Deprecated: subscription is now created automatically on login.
        sendResponse({ ok: false, error: "CREATE_SUBSCRIPTION is no longer used." });
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

