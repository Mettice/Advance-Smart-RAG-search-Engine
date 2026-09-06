/**
 * ResearchMate — Client Frontend Application
 * Interacts with FastAPI backend endpoints: /stats, /index, /query
 */

const API_BASE = window.location.origin;

// DOM Elements
const chatViewport = document.getElementById('chat-viewport');
const chatContainer = document.getElementById('chat-container');
const promptInput = document.getElementById('prompt-input');
const submitBtn = document.getElementById('submit-btn');
const fileInput = document.getElementById('file-input');
const dropzoneBar = document.getElementById('dropzone-bar');
const activeDocsTray = document.getElementById('active-docs-tray');
const toastNotice = document.getElementById('toast-notice');
const toastMessage = document.getElementById('toast-message');
const totalChunksElem = document.getElementById('total-chunks');
const modelBadgeElem = document.getElementById('model-badge');

let isProcessing = false;
let indexedFiles = new Set();

// ==========================================================================
// Initialization & Backend Sync
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  fetchBackendStats();
  setupEventListeners();
  setupStarters();
});

async function fetchBackendStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (res.ok) {
      const data = await res.json();
      if (totalChunksElem) {
        totalChunksElem.textContent = `${data.total_chunks} chunks`;
      }
      if (modelBadgeElem && data.model) {
        modelBadgeElem.textContent = data.model;
      }
    }
  } catch (err) {
    console.warn('Backend stats endpoint not reachable yet.', err);
  }
}

// ==========================================================================
// Event Listeners
// ==========================================================================

function setupEventListeners() {
  // Input auto-resize & Enter to send
  promptInput.addEventListener('input', () => {
    promptInput.style.height = 'auto';
    promptInput.style.height = Math.min(promptInput.scrollHeight, 140) + 'px';
    submitBtn.disabled = !promptInput.value.trim() || isProcessing;
  });

  promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!submitBtn.disabled) {
        handleUserQuery();
      }
    }
  });

  submitBtn.addEventListener('click', handleUserQuery);

  // File Upload via Input or Dropzone
  dropzoneBar.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  // Drag & Drop Interactions
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzoneBar.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzoneBar.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzoneBar.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzoneBar.classList.remove('dragover');
    });
  });

  dropzoneBar.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });
}

function setupStarters() {
  document.querySelectorAll('.starter-card').forEach(card => {
    card.addEventListener('click', () => {
      const query = card.getAttribute('data-query');
      if (query && !isProcessing) {
        promptInput.value = query;
        promptInput.style.height = 'auto';
        promptInput.style.height = promptInput.scrollHeight + 'px';
        submitBtn.disabled = false;
        handleUserQuery();
      }
    });
  });
}

// ==========================================================================
// File Ingestion Pipeline
// ==========================================================================

async function uploadFile(file) {
  const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.md'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();

  if (!allowedExtensions.includes(ext)) {
    showToast(`Format not supported. Please upload: ${allowedExtensions.join(', ')}`, 'error');
    return;
  }

  showToast(`Uploading and embedding ${file.name}...`, 'success');
  dropzoneBar.style.opacity = '0.5';
  dropzoneBar.style.pointerEvents = 'none';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/index`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to index document');
    }

    const data = await res.json();
    showToast(`✓ Indexed ${data.filename} (${data.chunks_indexed} chunks)`, 'success');
    addActiveDocumentBadge(data.filename, data.chunks_indexed);
    fetchBackendStats();
  } catch (err) {
    showToast(`Upload failed: ${err.message}`, 'error');
  } finally {
    dropzoneBar.style.opacity = '1';
    dropzoneBar.style.pointerEvents = 'auto';
    fileInput.value = '';
  }
}

function addActiveDocumentBadge(filename, chunkCount) {
  indexedFiles.add(filename);
  
  // Remove existing badge for same filename if re-indexed
  const existing = document.getElementById(`doc-${filename.replace(/[^a-zA-Z0-9]/g, '_')}`);
  if (existing) existing.remove();

  const badge = document.createElement('div');
  badge.className = 'active-doc-badge';
  badge.id = `doc-${filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
  badge.innerHTML = `
    <span>📄 ${escapeHtml(filename)}</span>
    <span class="chunk-count">(${chunkCount} chunks)</span>
  `;
  activeDocsTray.appendChild(badge);
}

// ==========================================================================
// Query & Chat Logic
// ==========================================================================

async function handleUserQuery() {
  const question = promptInput.value.trim();
  if (!question || isProcessing) return;

  isProcessing = true;
  submitBtn.disabled = true;
  promptInput.value = '';
  promptInput.style.height = 'auto';

  // Remove welcome hero if present
  const welcomeHero = document.querySelector('.welcome-hero');
  if (welcomeHero) {
    welcomeHero.remove();
  }

  // 1. Render User Message
  appendUserMessage(question);
  scrollToBottom();

  // 2. Render Assistant Loading Card
  const assistantCard = createAssistantMessageCard();
  chatViewport.appendChild(assistantCard);
  scrollToBottom();

  const startTime = performance.now();

  try {
    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: 8 })
    });

    const elapsed = Math.round(performance.now() - startTime);

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to retrieve answer');
    }

    const data = await response.json();
    updateAssistantMessageCard(assistantCard, data.answer, data.sources, elapsed);
  } catch (err) {
    updateAssistantMessageCard(
      assistantCard,
      `⚠️ **Error:** ${err.message}. Please verify that API keys are configured in your \`.env\` file.`,
      [],
      0
    );
  } finally {
    isProcessing = false;
    submitBtn.disabled = !promptInput.value.trim();
    scrollToBottom();
  }
}

// ==========================================================================
// Message Rendering
// ==========================================================================

function appendUserMessage(text) {
  const row = document.createElement('div');
  row.className = 'message-row user';
  row.innerHTML = `
    <div class="user-bubble">
      ${escapeHtml(text)}
    </div>
  `;
  chatViewport.appendChild(row);
}

function createAssistantMessageCard() {
  const row = document.createElement('div');
  row.className = 'message-row assistant';
  row.innerHTML = `
    <div class="assistant-card">
      <div class="assistant-header">
        <div class="assistant-info">
          <div class="assistant-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
          <span class="assistant-name">ResearchMate Assistant</span>
        </div>
        <span class="assistant-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
      <div class="message-content">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  return row;
}

function updateAssistantMessageCard(cardRow, rawAnswer, sources, elapsedMs) {
  const contentDiv = cardRow.querySelector('.message-content');
  contentDiv.innerHTML = formatMarkdown(rawAnswer);

  const card = cardRow.querySelector('.assistant-card');

  // Render Citations / Sources
  if (sources && sources.length > 0) {
    const sourcesContainer = document.createElement('div');
    sourcesContainer.className = 'sources-container';

    let sourcesHtml = `
      <div class="sources-heading">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        Grounded Citations
      </div>
      <div class="sources-list">
    `;

    sources.forEach((src, i) => {
      sourcesHtml += `
        <div class="source-pill" onclick="alert('Referenced document: ${escapeHtml(src)}')">
          <span>[${i + 1}]</span>
          <span>${escapeHtml(src)}</span>
        </div>
      `;
    });

    sourcesHtml += `</div>`;
    sourcesContainer.innerHTML = sourcesHtml;
    card.appendChild(sourcesContainer);
  }

  // Telemetry details
  if (elapsedMs > 0) {
    const telemetry = document.createElement('div');
    telemetry.className = 'message-telemetry';
    telemetry.innerHTML = `
      <span class="telemetry-item">⚡ ${elapsedMs}ms response</span>
      <span>•</span>
      <span class="telemetry-item">🎯 ChromaDB Vector Search</span>
    `;
    card.appendChild(telemetry);
  }
}

// ==========================================================================
// Helpers & Utilities
// ==========================================================================

function scrollToBottom() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showToast(message, type = 'success') {
  toastMessage.textContent = message;
  toastNotice.className = `toast-notice ${type} show`;
  setTimeout(() => {
    toastNotice.classList.remove('show');
  }, 4000);
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Lightweight Markdown Formatter
 */
function formatMarkdown(text) {
  if (!text) return '';
  let formatted = escapeHtml(text);

  // Fenced Code Blocks (```code```)
  formatted = formatted.replace(/```([a-z]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code>${code}</code></pre>`;
  });

  // Inline Code (`code`)
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold (**bold**)
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Unordered list items (- item or * item)
  formatted = formatted.replace(/^\s*[-*]\s+(.*)$/gm, '<li>$1</li>');
  formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // Numbered list items (1. item)
  formatted = formatted.replace(/^\s*\d+\.\s+(.*)$/gm, '<li>$1</li>');

  // Paragraph breaks
  formatted = formatted.replace(/\n\n/g, '</p><p>');
  formatted = `<p>${formatted}</p>`;

  // Clean empty paragraphs
  formatted = formatted.replace(/<p>\s*<\/p>/g, '');

  return formatted;
}
