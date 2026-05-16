const out = document.getElementById("out");
const clientError = document.getElementById("clientError");
const fileRows = document.getElementById("fileRows");
const successLink = document.getElementById("successLink");
const authStatus = document.getElementById("authStatus");
const logoutBtn = document.getElementById("logoutBtn");
const attributesModeBtn = document.getElementById("attributesModeBtn");
const constructorModeBtn = document.getElementById("constructorModeBtn");
const writeModeInput = document.getElementById("writeMode");
const argumentsLabel = document.getElementById("argumentsLabel");
const nodeTypeSelect = document.getElementById("nodeTypeSelect");

const API_PREFIX = document.body.dataset.apiPrefix;
const TOKEN_STORAGE_KEY = "aiida_restapi_access_token";
const constructorSupportCache = new Map();

function getWriteMode() {
  return writeModeInput.value;
}

function updateWriteModeUi() {
  const writeMode = getWriteMode();
  const isAttributes = writeMode === "attributes";

  attributesModeBtn.className = isAttributes ? "btn-primary" : "btn-secondary";
  constructorModeBtn.className = isAttributes ? "btn-secondary" : "btn-primary";
  argumentsLabel.textContent = isAttributes
    ? "Attributes (JSON)"
    : "Constructor arguments (JSON)";
}

function setWriteMode(writeMode) {
  writeModeInput.value = writeMode;
  updateWriteModeUi();
}

async function supportsConstructor(nodeType) {
  if (constructorSupportCache.has(nodeType)) {
    return constructorSupportCache.get(nodeType);
  }

  const token = getAccessToken();
  const endpoint =
    API_PREFIX +
    "/nodes/schema?type=" +
    encodeURIComponent(nodeType) +
    "&which=constructor";

  try {
    const resp = await fetch(endpoint, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {}),
      },
    });

    const supported = resp.ok;
    if (resp.status === 422 || resp.status === 404) {
      constructorSupportCache.set(nodeType, false);
      return false;
    }
    if (supported) {
      constructorSupportCache.set(nodeType, true);
      return true;
    }

    return true;
  } catch {
    return true;
  }
}

async function updateConstructorModeAvailability() {
  const nodeType = nodeTypeSelect.value;
  const supported = await supportsConstructor(nodeType);

  constructorModeBtn.hidden = !supported;

  if (!supported && getWriteMode() === "constructor") {
    setWriteMode("attributes");
  }
}

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

function setClientError(msg) {
  clientError.textContent = msg ? " " + msg : "";
}

function clearSuccessLink() {
  successLink.innerHTML = "";
}

function showNodeLink(nodeId) {
  const href = `${API_PREFIX}/nodes/${nodeId}`;
  const successMessage = document.createElement("div");
  successMessage.innerHTML = `<b>Success:</b> created node <a href="${href}" target="_blank" rel="noopener">${nodeId}</a>`;
  successLink.appendChild(successMessage);
}

function safeJsonParse(text) {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch (e) {
    return { ok: false, err: e };
  }
}

function isJsonObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
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

function normalizeRelPath(p) {
  return (p || "").trim().replace(/\\\\/g, "/");
}

function looksUnsafeRelPath(p) {
  const s = normalizeRelPath(p);
  if (!s) return true;
  if (s.startsWith("/")) return true;
  if (s.split("/").includes("..")) return true;
  if (s.split("/").some((seg) => seg.length === 0)) return true;
  return false;
}

function setRepositoryMetadataHash(metadata, target, hash) {
  const parts = normalizeRelPath(target).split("/").filter(Boolean);
  if (!parts.length) {
    throw new Error("Empty target path");
  }

  let current = metadata;
  for (let idx = 0; idx < parts.length; idx++) {
    const part = parts[idx];
    const isLeaf = idx === parts.length - 1;

    if (!Object.prototype.hasOwnProperty.call(current.o, part)) {
      current.o[part] = isLeaf ? { k: hash } : { o: {} };
    } else if (isLeaf) {
      current.o[part] = { k: hash };
    } else {
      const existing = current.o[part];
      if (!isJsonObject(existing) || !isJsonObject(existing.o)) {
        throw new Error(
          `Path conflict at '${parts.slice(0, idx + 1).join("/")}'`,
        );
      }
    }

    if (!isLeaf) {
      current = current.o[part];
    }
  }
}

function createFileRow() {
  const row = document.createElement("div");
  row.className = "file-row";

  const colFile = document.createElement("div");
  colFile.className = "col";
  const fileLabel = document.createElement("label");
  fileLabel.textContent = "File";
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  colFile.appendChild(fileLabel);
  colFile.appendChild(fileInput);

  const colPath = document.createElement("div");
  colPath.className = "col grow";
  const pathLabel = document.createElement("label");
  pathLabel.textContent = "Target path (optional, relative)";
  const pathInput = document.createElement("input");
  pathInput.type = "text";
  pathInput.className = "path-input";
  pathInput.placeholder = "e.g. sub/a.txt";
  colPath.appendChild(pathLabel);
  colPath.appendChild(pathInput);

  const colHash = document.createElement("div");
  colHash.className = "col grow";
  const hashLabel = document.createElement("label");
  hashLabel.textContent = "Hash";
  const hashInput = document.createElement("input");
  hashInput.type = "text";
  hashInput.className = "hash-input";
  hashInput.placeholder = "e.g. sha256 hash";
  colHash.appendChild(hashLabel);
  colHash.appendChild(hashInput);

  const colBtns = document.createElement("div");
  colBtns.className = "col";
  const btnSpacer = document.createElement("label");
  btnSpacer.textContent = " ";
  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "btn-danger";
  removeBtn.textContent = "Remove";
  colBtns.appendChild(btnSpacer);
  colBtns.appendChild(removeBtn);

  removeBtn.onclick = () => {
    row.remove();
    setClientError("");
  };

  fileInput.onchange = () => {
    setClientError("");
    if (fileInput.files && fileInput.files.length === 1) {
      const f = fileInput.files[0];
      if (!pathInput.value) pathInput.value = f.name;
    }
  };

  pathInput.oninput = () => setClientError("");
  hashInput.oninput = () => setClientError("");

  row.appendChild(colFile);
  row.appendChild(colPath);
  row.appendChild(colHash);
  row.appendChild(colBtns);

  return row;
}

function ensureAtLeastOneRow() {
  if (!fileRows.children.length) {
    fileRows.appendChild(createFileRow());
  }
}

function gatherRows() {
  const items = [];
  for (const row of fileRows.children) {
    const fileInput = row.querySelector('input[type="file"]');
    const pathInput = row.querySelector(".path-input");
    const hashInput = row.querySelector(".hash-input");
    const file =
      fileInput && fileInput.files && fileInput.files.length
        ? fileInput.files[0]
        : null;
    const relPath = normalizeRelPath(pathInput ? pathInput.value : "");
    const hash = (hashInput ? hashInput.value : "").trim();
    if (!file) continue;

    items.push({ file, relPath, hash });
  }
  return items;
}

document.getElementById("addFileBtn").addEventListener("click", () => {
  fileRows.appendChild(createFileRow());
});

attributesModeBtn.addEventListener("click", () => {
  setWriteMode("attributes");
});

constructorModeBtn.addEventListener("click", () => {
  setWriteMode("constructor");
});

nodeTypeSelect.addEventListener("change", () => {
  void updateConstructorModeAvailability();
});

document.getElementById("clearBtn").addEventListener("click", () => {
  out.textContent = "";
  setClientError("");
  clearSuccessLink();
});

document.getElementById("authBtn").addEventListener("click", async () => {
  setClientError("");
  clearSuccessLink();

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
    if (isJsonContentType(contentType)) {
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
  clearSuccessLink();
});

document.getElementById("sendBtn").addEventListener("click", async () => {
  setClientError("");
  clearSuccessLink();

  const labelInput = document.getElementById("label");
  const descriptionInput = document.getElementById("description");
  const extrasTextarea = document.getElementById("extras");
  const argumentsTextarea = document.getElementById("arguments");

  const nodeType = nodeTypeSelect.value;
  const writeMode = getWriteMode();
  let params = {
    node_type: nodeType,
  };

  const label = labelInput.value.trim();
  const description = descriptionInput.value.trim();
  if (label) {
    params.label = label;
  }
  if (description) {
    params.description = description;
  }

  const extrasText = extrasTextarea.value.trim();
  if (extrasText) {
    const parsedExtras = safeJsonParse(extrasText);
    if (!parsedExtras.ok) {
      setClientError("Invalid JSON in extras: " + parsedExtras.err);
      return;
    }
    if (!isJsonObject(parsedExtras.value)) {
      setClientError("Extras JSON must be an object.");
      return;
    }
    params.extras = parsedExtras.value;
  }

  const argumentsText = argumentsTextarea.value.trim();
  if (argumentsText) {
    const parsedArguments = safeJsonParse(argumentsText);
    if (!parsedArguments.ok) {
      setClientError("Invalid JSON in arguments: " + parsedArguments.err);
      return;
    }
    if (!isJsonObject(parsedArguments.value)) {
      setClientError("Arguments JSON must be an object.");
      return;
    }

    if (writeMode === "attributes") {
      params.attributes = parsedArguments.value;
    } else {
      params.args = parsedArguments.value;
    }
  }

  const rows = gatherRows();
  const hasFiles = rows.length > 0;

  if (hasFiles && writeMode !== "attributes") {
    setClientError(
      "File upload test page currently only supports attributes mode.",
    );
    return;
  }

  let ENDPOINT = API_PREFIX + "/nodes";
  if (!hasFiles && writeMode === "constructor") {
    ENDPOINT = API_PREFIX + "/nodes/constructor";
  } else if (hasFiles) {
    ENDPOINT += "/file-upload";
  }

  out.textContent = "Sending to: " + ENDPOINT + "\n";

  try {
    let resp;
    const token = getAccessToken();

    if (!hasFiles) {
      resp = await fetch(ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(token ? { Authorization: "Bearer " + token } : {}),
        },
        body: JSON.stringify(params),
      });
    } else {
      const fd = new FormData();

      const targets = new Set();
      const anyHashProvided = rows.some(({ hash }) => Boolean(hash));
      const repositoryMetadata = anyHashProvided ? { o: {} } : null;
      for (const { file, relPath, hash } of rows) {
        const target = relPath ? relPath : file.name;

        if (looksUnsafeRelPath(target)) {
          setClientError("Unsafe target path: " + target);
          return;
        }
        if (targets.has(target)) {
          setClientError("Duplicate target path: " + target);
          return;
        }
        targets.add(target);

        if (repositoryMetadata) {
          try {
            setRepositoryMetadataHash(repositoryMetadata, target, hash || "");
          } catch (err) {
            setClientError("Invalid repository metadata path: " + err);
            return;
          }
        }

        if (relPath) {
          const renamed = new File([file], target, {
            type: file.type,
            lastModified: file.lastModified,
          });
          fd.append("files", renamed, target);
        } else {
          fd.append("files", file, file.name);
        }
      }

      if (repositoryMetadata) {
        params.repository_metadata = repositoryMetadata;
      }
      fd.append("params", JSON.stringify(params));

      resp = await fetch(ENDPOINT, {
        method: "POST",
        headers: {
          Accept: "application/json",
          ...(token ? { Authorization: "Bearer " + token } : {}),
        },
        body: fd,
      });
    }

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
      "POST " +
      ENDPOINT +
      "\n" +
      "Representation: " +
      (hasFiles ? "multipart/form-data" : "application/json") +
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

    if (resp.ok && bodyJson) {
      const nodeId =
        bodyJson.id ??
        bodyJson.pk ??
        bodyJson.uuid ??
        bodyJson.node_id ??
        (bodyJson.data &&
          (bodyJson.data.id ?? bodyJson.data.pk ?? bodyJson.data.uuid));

      if (nodeId !== undefined && nodeId !== null && String(nodeId).length) {
        showNodeLink(String(nodeId));
      }
    }
  } catch (err) {
    out.textContent = "Request error: " + err;
  }
});

ensureAtLeastOneRow();
updateWriteModeUi();
updateAuthUi();
void updateConstructorModeAvailability();
