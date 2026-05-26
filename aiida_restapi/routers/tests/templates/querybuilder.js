const out = document.getElementById("out");
const clientError = document.getElementById("clientError");
const authStatus = document.getElementById("authStatus");
const logoutBtn = document.getElementById("logoutBtn");

const API_PREFIX = document.body.dataset.apiPrefix;
const TOKEN_STORAGE_KEY = "aiida_restapi_access_token";

function getAccessToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

function setAccessToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  updateAuthUi();
}

function clearAccessToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  updateAuthUi();
}

function updateAuthUi() {
  const token = getAccessToken();
  authStatus.textContent = token
    ? "Authenticated (token stored)"
    : "Not authenticated";
  logoutBtn.disabled = !token;
}

async function readResponse(resp) {
  const contentType = resp.headers.get("content-type") || "";
  const text = await resp.text();
  return { contentType, text };
}

function isJsonContentType(contentType) {
  return (
    contentType.includes("application/json") || /\+json\b/i.test(contentType)
  );
}

function setClientError(msg) {
  clientError.textContent = msg ? " " + msg : "";
}

document.getElementById("clearBtn").addEventListener("click", () => {
  out.textContent = "";
  setClientError("");
});

document.getElementById("authBtn").addEventListener("click", async () => {
  setClientError("");

  const email = document.getElementById("authEmail").value.trim();
  const password = document.getElementById("authPassword").value;

  const ENDPOINT = API_PREFIX + "/auth/token";
  out.textContent = "Authenticating at: " + ENDPOINT + "\n";

  try {
    const resp = await fetch(ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json",
      },
      body: new URLSearchParams({ username: email, password }),
    });

    const { contentType, text } = await readResponse(resp);

    let bodyJson = null;
    if (contentType.includes("application/json")) {
      try {
        bodyJson = JSON.parse(text);
      } catch {}
    }

    if (!resp.ok) {
      out.textContent += "\nAuth failed:\n" + text;
      return;
    }

    if (!bodyJson || !bodyJson.access_token) {
      out.textContent +=
        "\nAuth response did not include access_token:\n" + text;
      return;
    }

    setAccessToken(bodyJson.access_token);
    out.textContent += "\nAuth OK. Token stored in localStorage.\n";
  } catch (err) {
    out.textContent = "Auth request error: " + err;
  }
});

logoutBtn.addEventListener("click", () => {
  clearAccessToken();
  setClientError("");
});

document.getElementById("sendBtn").addEventListener("click", async () => {
  setClientError("");
  const queryText = document.getElementById("query").value;
  const flatCheckbox = document.getElementById("flatCheckbox");
  const fullCheckbox = document.getElementById("fullCheckbox");

  let parsed;
  try {
    parsed = JSON.parse(queryText);
  } catch (e) {
    setClientError("Invalid JSON in query: " + e);
    return;
  }

  let ENDPOINT =
    API_PREFIX +
    "/querybuilder" +
    (flatCheckbox.checked ? "?flat=true" : "") +
    (fullCheckbox.checked
      ? (flatCheckbox.checked ? "&" : "?") + "full=true"
      : "");

  out.textContent = "Sending to: " + ENDPOINT + "\n";

  try {
    const token = getAccessToken();
    const resp = await fetch(ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {}),
      },
      body: JSON.stringify(parsed),
    });
    const { contentType, text } = await readResponse(resp);
    let bodyText = text;
    let bodyJson = null;
    if (isJsonContentType(contentType)) {
      try {
        bodyJson = JSON.parse(text);
        bodyText = JSON.stringify(bodyJson, null, 2);
      } catch {}
    }
    out.textContent =
      "POST /querybuilder" +
      "\n" +
      "Status: " +
      resp.status +
      " " +
      resp.statusText +
      "\n" +
      "Response Content-Type: " +
      contentType +
      "\n\n" +
      bodyText;
  } catch (err) {
    out.textContent = "Request error: " + err;
  }
});

updateAuthUi();
