function chartDefaults() {
    if (!window.Chart) return;
    Chart.defaults.color = "#826958";
    Chart.defaults.borderColor = "rgba(168, 124, 84, 0.14)";
}

function createDashboardCharts() {
    if (!window.dashboardTrendData || !window.Chart) return;
    chartDefaults();
    const canvas = document.getElementById("dashboardTrendChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: window.dashboardTrendData.journal_dates,
            datasets: [
                {
                    label: "Stress",
                    data: window.dashboardTrendData.journal_stress,
                    borderColor: "#d98563",
                    backgroundColor: "rgba(217, 133, 99, 0.18)",
                    fill: true,
                    tension: 0.35,
                },
                {
                    label: "Sleep Hours",
                    data: window.dashboardTrendData.sleep_hours,
                    borderColor: "#97b199",
                    backgroundColor: "rgba(151, 177, 153, 0.12)",
                    tension: 0.35,
                },
            ],
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                },
            },
        },
    });
}

function initVoiceButtons() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const buttons = document.querySelectorAll(".mic-button");

    buttons.forEach((button) => {
        if (!SpeechRecognition) {
            button.disabled = true;
            button.textContent = "Voice input unavailable";
            return;
        }

        button.addEventListener("click", () => {
            const target = document.getElementById(button.dataset.target);
            const sourceInput = document.getElementById(button.dataset.sourceTarget);
            const languageSelect = document.getElementById(button.dataset.languageTarget);
            const recognition = new SpeechRecognition();
            recognition.lang = languageSelect ? languageSelect.value : "en-US";
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            button.textContent = "Listening...";
            recognition.start();

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                target.value = target.value ? `${target.value} ${transcript}` : transcript;
                if (sourceInput) {
                    sourceInput.value = "voice";
                }
            };

            recognition.onerror = () => {
                button.textContent = "Try voice input again";
            };

            recognition.onend = () => {
                button.textContent = "Start voice input";
            };
        });
    });
}

function initLocalAudioPlayer() {
    const input = document.getElementById("localAudioInput");
    const list = document.getElementById("localTrackList");
    const audio = document.getElementById("globalAudioPlayer");
    const titleNode = document.getElementById("playerTrackTitle");
    const metaNode = document.getElementById("playerTrackMeta");
    if (!input || !list || !audio) return;

    input.addEventListener("change", () => {
        list.innerHTML = "";
        Array.from(input.files || []).forEach((file) => {
            const item = document.createElement("button");
            item.type = "button";
            item.className = "soft-link";
            item.textContent = file.name;
            item.addEventListener("click", () => {
                audio.src = URL.createObjectURL(file);
                titleNode.textContent = file.name;
                metaNode.textContent = "Local upload";
                audio.play();
            });
            list.appendChild(item);
        });
    });
}

function initBreathingGame() {
    const startButton = document.getElementById("startBreathing");
    const claimButton = document.getElementById("claimBreathing");
    const orb = document.getElementById("breathingOrb");
    const text = document.getElementById("breathingText");
    if (!startButton || !claimButton || !orb || !text) return;

    startButton.addEventListener("click", () => {
        claimButton.disabled = true;
        let phase = 0;
        const phases = [
            { text: "Inhale slowly...", breatheIn: true },
            { text: "Hold softly...", breatheIn: true },
            { text: "Exhale gently...", breatheIn: false },
            { text: "One more slow breath complete.", breatheIn: false },
        ];

        function nextPhase() {
            if (phase >= phases.length) {
                claimButton.disabled = false;
                text.textContent = "Well done. You can claim your 10 coins now.";
                return;
            }
            const current = phases[phase];
            orb.classList.toggle("breathe-in", current.breatheIn);
            text.textContent = current.text;
            phase += 1;
            setTimeout(nextPhase, 1800);
        }

        nextPhase();
    });
}

function initChallengeAnswerForms() {
    document.querySelectorAll(".challenge-answer-form").forEach((form) => {
        const input = form.querySelector(".challenge-answer");
        const answer = (form.dataset.answer || "").toUpperCase();
        const claimButton = document.getElementById(form.dataset.claim);
        if (!input || !claimButton) return;

        input.addEventListener("input", () => {
            claimButton.disabled = input.value.trim().toUpperCase() !== answer;
        });
    });
}

function initMemoryGame() {
    const pads = Array.from(document.querySelectorAll(".memory-pad"));
    const playButton = document.getElementById("startMemory");
    const claimButton = document.getElementById("claimMemory");
    const status = document.getElementById("memoryStatus");
    if (!pads.length || !playButton || !claimButton || !status) return;

    const sequence = ["sun", "sky", "leaf"];
    let playerSequence = [];
    let acceptingInput = false;

    function pulsePad(key, delay) {
        const pad = pads.find((item) => item.dataset.pad === key);
        if (!pad) return;
        setTimeout(() => {
            pad.classList.add("active");
            setTimeout(() => pad.classList.remove("active"), 500);
        }, delay);
    }

    playButton.addEventListener("click", () => {
        playerSequence = [];
        claimButton.disabled = true;
        acceptingInput = false;
        status.textContent = "Watch closely...";
        sequence.forEach((key, index) => pulsePad(key, index * 700));
        setTimeout(() => {
            acceptingInput = true;
            status.textContent = "Now repeat the color order.";
        }, sequence.length * 700);
    });

    pads.forEach((pad) => {
        pad.addEventListener("click", () => {
            if (!acceptingInput) return;
            playerSequence.push(pad.dataset.pad);
            const currentIndex = playerSequence.length - 1;
            if (playerSequence[currentIndex] !== sequence[currentIndex]) {
                status.textContent = "Almost. Press play and try again.";
                acceptingInput = false;
                playerSequence = [];
                return;
            }
            if (playerSequence.length === sequence.length) {
                status.textContent = "Nice memory. You can claim your coins now.";
                claimButton.disabled = false;
                acceptingInput = false;
            }
        });
    });
}

function initFocusGame() {
    const zone = document.getElementById("focusZone");
    const claimButton = document.getElementById("claimFocus");
    const status = document.getElementById("focusStatus");
    if (!zone || !claimButton || !status) return;

    let count = 0;
    function spawnDot() {
        if (count >= 12) {
            status.textContent = "You reached 12. Claim your 10 coins.";
            claimButton.disabled = false;
            return;
        }

        const dot = document.createElement("button");
        dot.type = "button";
        dot.className = "focus-dot";
        dot.style.left = `${Math.random() * 80 + 5}%`;
        dot.style.top = `${Math.random() * 70 + 10}%`;
        dot.addEventListener("click", () => {
            count += 1;
            status.textContent = `${count} of 12 dots caught.`;
            dot.remove();
            spawnDot();
        });
        zone.appendChild(dot);
    }

    zone.innerHTML = "";
    for (let i = 0; i < 3; i += 1) {
        spawnDot();
    }
}

function initInteractivePolish() {
    const interactiveNodes = document.querySelectorAll(
        "button, .main-nav a, .panel-head a, .soft-link, .onboarding-card, .mood-patch, .sleep-segment, .feed-card, .summary-card, .panel"
    );

    interactiveNodes.forEach((node, index) => {
        node.classList.add("reveal-up");
        node.style.animationDelay = `${Math.min(index * 18, 240)}ms`;
    });

    document.querySelectorAll("button, .main-nav a, .panel-head a, .soft-link").forEach((node) => {
        node.addEventListener("pointerenter", () => {
            node.style.willChange = "transform";
        });

        node.addEventListener("pointerleave", () => {
            node.style.willChange = "auto";
        });

        node.addEventListener("click", (event) => {
            const rect = node.getBoundingClientRect();
            const ripple = document.createElement("span");
            ripple.className = "ripple";
            ripple.style.left = `${event.clientX - rect.left}px`;
            ripple.style.top = `${event.clientY - rect.top}px`;
            node.appendChild(ripple);
            setTimeout(() => ripple.remove(), 650);
        });
    });

    const activePath = window.location.pathname;
    document.querySelectorAll(".main-nav a").forEach((link) => {
        const url = new URL(link.href, window.location.origin);
        if (url.pathname === activePath) {
            link.classList.add("active-link");
        }
    });
}

function initFirstTimeTour() {
    const steps = window.firstTimeTour;
    const modal = document.querySelector("[data-tour-modal]");
    if (!steps || !modal) return;

    const titleNode = modal.querySelector("[data-tour-title]");
    const copyNode = modal.querySelector("[data-tour-copy]");
    const stepNode = modal.querySelector("[data-tour-step]");
    const totalNode = modal.querySelector("[data-tour-total]");
    const prevButton = modal.querySelector("[data-tour-prev]");
    const nextButton = modal.querySelector("[data-tour-next]");
    const finishForm = document.querySelector("[data-tour-finish]");

    let currentIndex = 0;
    let activeTarget = null;
    totalNode.textContent = `of ${steps.length}`;

    function clearActiveTarget() {
        if (activeTarget) {
            activeTarget.classList.remove("tour-target-active");
            activeTarget = null;
        }
    }

    function renderStep(index) {
        clearActiveTarget();
        const step = steps[index];
        if (!step) return;

        titleNode.textContent = step.title;
        copyNode.textContent = step.copy;
        stepNode.textContent = `${index + 1}`;
        prevButton.disabled = index === 0;

        const target = document.querySelector(step.target);
        if (target) {
            activeTarget = target;
            activeTarget.classList.add("tour-target-active");
            activeTarget.scrollIntoView({ behavior: "smooth", block: "center" });
        }

        const isLast = index === steps.length - 1;
        nextButton.hidden = isLast;
        finishForm.hidden = !isLast;
    }

    prevButton.addEventListener("click", () => {
        if (currentIndex > 0) {
            currentIndex -= 1;
            renderStep(currentIndex);
        }
    });

    nextButton.addEventListener("click", () => {
        if (currentIndex < steps.length - 1) {
            currentIndex += 1;
            renderStep(currentIndex);
        }
    });

    finishForm?.addEventListener("submit", () => {
        clearActiveTarget();
    });

    renderStep(currentIndex);
}

createDashboardCharts();
initVoiceButtons();
initLocalAudioPlayer();
initBreathingGame();
initChallengeAnswerForms();
initMemoryGame();
initFocusGame();
initInteractivePolish();
initFirstTimeTour();
