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

// Alpine.js component for course app state
function courseApp() {
    return {
        showProgress: false,
        messages: [],
        eventSource: null,

        init() {
            // Clean up SSE on page unload
            window.addEventListener("beforeunload", () => {
                if (this.eventSource) this.eventSource.close();
            });
        },
    };
}

// Global functions called from onclick handlers in partials
function startProgress() {
    const app = document.querySelector("[x-data]").__x.$data;
    app.showProgress = true;
    app.messages = [];

    // Close any existing SSE connection
    if (app.eventSource) {
        app.eventSource.close();
    }

    app.eventSource = new EventSource("/api/progress");

    app.eventSource.onmessage = function (event) {
        app.messages.push(event.data);
        // Auto-scroll progress panel
        const container = document.getElementById("progress-messages");
        if (container) {
            setTimeout(() => container.scrollTop = container.scrollHeight, 50);
        }
    };

    app.eventSource.addEventListener("done", function () {
        app.eventSource.close();
        app.eventSource = null;
    });

    app.eventSource.onerror = function () {
        app.eventSource.close();
        app.eventSource = null;
    };
}

function stopProgress() {
    // SSE will close itself via the "done" event, but we stop if something goes wrong
    const app = document.querySelector("[x-data]");
    if (app && app.__x && app.__x.$data.eventSource) {
        // Let SSE close naturally via done event
    }
}
