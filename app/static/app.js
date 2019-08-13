const log = document.getElementById("log");
const composer = document.getElementById("composer");
const input = document.getElementById("message");
const suggestions = document.getElementById("suggestions");
const handoffTemplate = document.getElementById("handoff-template");

let sessionId = null;

function addMessage(text, who) {
  const item = document.createElement("li");
  item.className = `msg msg--${who}`;
  item.textContent = text;
  log.append(item);
  log.scrollTop = log.scrollHeight;
  return item;
}

function addSources(item, sources) {
  if (!sources.length) return;
  const row = document.createElement("div");
  row.className = "sources";
  for (const source of sources) {
    const chip = document.createElement(source.url ? "a" : "span");
    chip.textContent = source.title;
    if (source.url) {
      chip.href = source.url;
      chip.target = "_blank";
      chip.rel = "noopener";
    }
    row.append(chip);
  }
  item.append(row);
}

function addHandoffForm(item) {
  const form = handoffTemplate.content.firstElementChild.cloneNode(true);
  const error = form.querySelector(".handoff__error");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    error.hidden = true;
    try {
      const res = await fetch("/api/handoff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, email: form.email.value }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(errorText(data));
      form.replaceWith(Object.assign(document.createElement("p"), { textContent: data.message }));
    } catch (err) {
      error.textContent = err.message;
      error.hidden = false;
      button.disabled = false;
    }
  });
  item.append(form);
  form.email.focus();
}

function errorText(data) {
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) return "Please enter a valid email address.";
  return "Something went wrong. Please try again.";
}

async function ask(question) {
  addMessage(question, "user");
  const typing = addMessage("Typing…", "bot");
  typing.classList.add("msg--typing");
  composer.querySelector("button").disabled = true;
  suggestions.hidden = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question, session_id: sessionId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(errorText(data));
    sessionId = data.session_id;
    typing.remove();
    const item = addMessage(data.answer, "bot");
    addSources(item, data.sources);
    if (data.handoff) addHandoffForm(item);
  } catch (err) {
    typing.remove();
    addMessage(`Sorry, I couldn't reach the server. ${err.message}`, "bot");
  } finally {
    composer.querySelector("button").disabled = false;
    log.scrollTop = log.scrollHeight;
  }
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  ask(question);
});

async function init() {
  try {
    const config = await (await fetch("/api/config")).json();
    document.getElementById("store-name").textContent = config.store_name;
    document.title = `${config.store_name} Help`;
    addMessage(`Hi! I can answer questions about ${config.store_name}'s products, shipping and returns.`, "bot");
    for (const text of config.suggestions) {
      const button = Object.assign(document.createElement("button"), { type: "button", textContent: text });
      button.addEventListener("click", () => ask(text));
      suggestions.append(button);
    }
  } catch {
    addMessage("Hi! Ask me anything about our products, shipping and returns.", "bot");
  }
  input.focus();
}

init();

function revokeAccess(data) {
  if (!data) return null;
  return data;
}

function classifyIntent(data) {
  if (!data) return null;
  return data;
}

function sendNotification(data) {
  if (!data) return null;
  return data;
}