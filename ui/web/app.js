// --- State ---
let currentPaper = null;
let searchResults = [];

// --- DOM refs ---
const $ = (sel) => document.querySelector(sel);
const searchForm = $("#search-form");
const searchInput = $("#search-input");
const searchBtn = $("#search-btn");
const status = $("#status");
const resultsDiv = $("#results");
const detailsPanel = $("#details-panel");
const savedBody = $("#saved-body");
const savedTable = $("#saved-table");
const savedEmpty = $("#saved-empty");
const progressContainer = $("#progress");
const progressFill = $("#progress-fill");
const progressLabel = $("#progress-label");

// --- Tabs ---
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
    tab.classList.add("active");
    $(`#tab-${tab.dataset.tab}`).classList.add("active");
    if (tab.dataset.tab === "saved") loadSaved();
  });
});

// --- Search ---
function setProgress(percent, label) {
  progressContainer.hidden = false;
  progressFill.style.width = `${percent}%`;
  progressLabel.textContent = label;
}

function hideProgress() {
  progressContainer.hidden = true;
  progressFill.style.width = "0%";
  progressLabel.textContent = "";
}

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = searchInput.value.trim();
  if (!query) return;

  searchBtn.disabled = true;
  searchInput.disabled = true;
  status.textContent = "";
  resultsDiv.innerHTML = "";
  setProgress(5, "Starting search...");

  try {
    const res = await fetch("/api/search/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) throw new Error(`Search failed: ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop();

      let eventType = null;
      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ") && eventType) {
          const data = JSON.parse(line.slice(6));
          if (eventType === "progress") {
            setProgress(data.percent, data.label);
          } else if (eventType === "result") {
            setProgress(100, "Done");
            searchResults = data.top_results || [];
            status.textContent = `${searchResults.length} results  |  Top relevance: ${data.quality_score.toFixed(4)}`;
            renderResults();
          }
          eventType = null;
        }
      }
    }
  } catch (err) {
    status.textContent = "";
    alert(err.message);
  } finally {
    searchBtn.disabled = false;
    searchInput.disabled = false;
    setTimeout(hideProgress, 1000);
  }
});

async function renderResults() {
  const savedList = await fetch("/api/saved").then((r) => r.json());
  const savedIds = new Set(savedList.map((a) => a.id));

  resultsDiv.innerHTML = searchResults
    .map((paper, i) => {
      const title = paper.meta?.title || "Untitled";
      const id = paper.id || "N/A";
      const score = (paper.score || 0).toFixed(4);
      const abstract = paper.text || "";
      const snippet = abstract.length > 180 ? abstract.slice(0, 180) + "..." : abstract;
      const savedBadge = savedIds.has(id) ? '<span class="badge-saved">saved</span>' : "";
      return `
        <div class="paper-card" data-index="${i}">
          <div class="paper-card-title">
            <h3>${esc(title)}</h3>
            ${savedBadge}
          </div>
          <p class="meta">arXiv: ${esc(id)}  |  Relevance: ${score}</p>
          <p class="snippet">${esc(snippet)}</p>
        </div>`;
    })
    .join("");

  resultsDiv.querySelectorAll(".paper-card").forEach((card) => {
    card.addEventListener("click", () => {
      openDetails(searchResults[parseInt(card.dataset.index)]);
    });
  });
}

// --- Details panel ---
async function openDetails(paper) {
  currentPaper = paper;
  const title = paper.meta?.title || "Untitled";
  const id = paper.id || "N/A";
  const score = (paper.score || 0).toFixed(4);

  $("#details-title").textContent = title;
  $("#details-meta").textContent = `arXiv: ${id}  |  Relevance: ${score}`;
  $("#details-abstract").textContent = paper.text || "No abstract available.";
  $("#details-pdf").href = `https://arxiv.org/pdf/${id}`;

  const saveBtn = $("#details-save");
  const check = await fetch(`/api/saved/${id}/check`).then((r) => r.json());
  if (check.saved) {
    saveBtn.textContent = "Saved";
    saveBtn.className = "btn-saved";
    saveBtn.disabled = true;
  } else {
    saveBtn.textContent = "Save Article";
    saveBtn.className = "btn-primary";
    saveBtn.disabled = false;
  }

  detailsPanel.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeDetails() {
  detailsPanel.hidden = true;
  document.body.style.overflow = "";
  renderResults();
}

$("#details-back").addEventListener("click", closeDetails);

$("#details-save").addEventListener("click", async () => {
  if (!currentPaper) return;
  const btn = $("#details-save");
  btn.disabled = true;

  await fetch("/api/saved", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(currentPaper),
  });

  btn.textContent = "Saved";
  btn.className = "btn-saved";
});

// Keyboard: Escape / Backspace / Alt+Left to close details
document.addEventListener("keydown", (e) => {
  if (detailsPanel.hidden) return;
  if (e.key === "Escape" || e.key === "Backspace" || (e.altKey && e.key === "ArrowLeft")) {
    e.preventDefault();
    closeDetails();
  }
});

// --- Saved articles ---
async function loadSaved() {
  const articles = await fetch("/api/saved").then((r) => r.json());
  if (articles.length === 0) {
    savedTable.hidden = true;
    savedEmpty.hidden = false;
    return;
  }
  savedTable.hidden = false;
  savedEmpty.hidden = true;

  savedBody.innerHTML = articles
    .slice()
    .reverse()
    .map(
      (a) => `
      <tr>
        <td>${esc(a.title || "Untitled")}</td>
        <td>${esc(a.id)}</td>
        <td>${(a.score || 0).toFixed(4)}</td>
        <td>
          <div class="actions">
            <button class="btn-link" onclick="window.open('https://arxiv.org/pdf/${esc(a.id)}','_blank')">PDF</button>
            <button class="btn-danger" onclick="removeSaved('${esc(a.id)}')">Remove</button>
          </div>
        </td>
      </tr>`
    )
    .join("");
}

async function removeSaved(id) {
  await fetch(`/api/saved/${id}`, { method: "DELETE" });
  loadSaved();
}

// Make removeSaved available globally for inline onclick
window.removeSaved = removeSaved;

// --- Util ---
function esc(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}
