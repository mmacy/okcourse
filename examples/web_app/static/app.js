// Resizable splitter between sidebar and content panel.
// Uses delta from pointerdown to avoid Brave's getBoundingClientRect farbling.
// Prevents native dragstart to stop pointercancel from aborting the drag.
(function () {
    function initSplitter() {
        var splitter = document.querySelector(".splitter");
        var grid = document.querySelector(".layout-grid");
        var sidebar = document.querySelector(".sidebar-panel");
        if (!splitter || !grid || !sidebar) return;

        var MIN_WIDTH = 220;
        var MAX_WIDTH = 520;
        var dragging = false;
        var startX, startWidth;

        // Block native drag-and-drop from firing pointercancel
        splitter.addEventListener("dragstart", function (e) { e.preventDefault(); });

        splitter.addEventListener("pointerdown", function (e) {
            if (e.button !== 0) return;
            e.preventDefault();
            dragging = true;
            startX = e.clientX;
            startWidth = sidebar.offsetWidth;
            splitter.classList.add("dragging");
            document.body.classList.add("splitter-dragging");
        });

        document.addEventListener("pointermove", function (e) {
            if (!dragging) return;
            e.preventDefault();
            var newWidth = startWidth + (e.clientX - startX);
            newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, newWidth));
            grid.style.setProperty("--sidebar-width", newWidth + "px");
        });

        document.addEventListener("pointerup", function () {
            if (!dragging) return;
            dragging = false;
            splitter.classList.remove("dragging");
            document.body.classList.remove("splitter-dragging");
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSplitter);
    } else {
        initSplitter();
    }
})();

// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", next);
    document.getElementById("theme-icon").textContent = next === "dark" ? "\u2600" : "\u263E";
    localStorage.setItem("theme", next);
}

// Restore saved theme
(function () {
    const saved = localStorage.getItem("theme");
    if (saved) {
        document.documentElement.setAttribute("data-theme", saved);
        const icon = document.getElementById("theme-icon");
        if (icon) icon.textContent = saved === "dark" ? "\u2600" : "\u263E";
    }
})();

// Update voices dropdown when TTS model changes
async function updateVoices(model) {
    try {
        const resp = await fetch(`/api/voices/${encodeURIComponent(model)}`);
        const data = await resp.json();
        const select = document.getElementById("tts_voice");
        const currentValue = select.value;
        select.innerHTML = "";
        for (const voice of data.voices) {
            const opt = document.createElement("option");
            opt.value = voice;
            opt.textContent = voice;
            if (voice === currentValue) opt.selected = true;
            select.appendChild(opt);
        }
    } catch (e) {
        console.error("Failed to update voices:", e);
    }
}

// Canonical tab order for sorting
var TAB_ORDER = ["outline", "lectures", "image", "audio", "summary"];

// Alpine.js component for course app state
function courseApp() {
    return {
        showProgress: false,
        messages: [],
        eventSource: null,
        tabs: [],
        activeTab: "",

        init() {
            window.addEventListener("beforeunload", () => {
                if (this.eventSource) this.eventSource.close();
            });
        },

        addTab(id, label) {
            if (!this.tabs.find(function (t) { return t.id === id; })) {
                this.tabs.push({ id: id, label: label });
                // Keep tabs in canonical order
                this.tabs.sort(function (a, b) {
                    return TAB_ORDER.indexOf(a.id) - TAB_ORDER.indexOf(b.id);
                });
            }
            this.activeTab = id;
        },

        startProgress() {
            this.showProgress = true;
            this.messages = [];

            if (this.eventSource) {
                this.eventSource.close();
            }

            this.eventSource = new EventSource("/api/progress");

            this.eventSource.onmessage = (event) => {
                this.messages.push(event.data);
                var container = document.getElementById("progress-messages");
                if (container) {
                    setTimeout(function () { container.scrollTop = container.scrollHeight; }, 50);
                }
            };

            this.eventSource.addEventListener("done", () => {
                this.eventSource.close();
                this.eventSource = null;
            });

            this.eventSource.onerror = () => {
                this.eventSource.close();
                this.eventSource = null;
            };
        },
    };
}

// Global helper so onclick handlers in HTMX-swapped partials can reach Alpine
function startProgress() {
    var el = document.querySelector("[x-data]");
    if (el && el._x_dataStack) {
        el._x_dataStack[0].startProgress();
    }
}

// After HTMX swaps content into a tab panel, detect data-tab-id and activate the tab
document.addEventListener("htmx:afterSettle", function (event) {
    var target = event.detail.target;
    if (!target) return;

    // Look for the data-tab-id marker in the swapped content
    var tabContent = target.querySelector("[data-tab-id]");
    if (!tabContent) return;

    var tabId = tabContent.dataset.tabId;
    var tabLabel = tabContent.dataset.tabLabel;

    // Reach into Alpine to add/activate the tab
    var el = document.querySelector("[x-data]");
    if (el && el._x_dataStack) {
        el._x_dataStack[0].addTab(tabId, tabLabel);
    }
});

// Swap button text to loading label with spinner on HTMX request start
document.addEventListener("htmx:beforeRequest", function (event) {
    var trigger = event.detail.elt;
    if (trigger && trigger.tagName === "BUTTON" && trigger.dataset.loadingText) {
        trigger.dataset.originalText = trigger.textContent;
        trigger.textContent = trigger.dataset.loadingText;
        trigger.dataset.loadingActive = "";
    }
});

// Restore button text and remove spinner when HTMX request completes
document.addEventListener("htmx:afterRequest", function (event) {
    var trigger = event.detail.elt;
    if (trigger && trigger.tagName === "BUTTON" && trigger.dataset.originalText) {
        trigger.textContent = trigger.dataset.originalText;
        delete trigger.dataset.originalText;
        delete trigger.dataset.loadingActive;
    }
});
