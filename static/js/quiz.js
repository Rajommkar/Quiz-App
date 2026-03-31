document.addEventListener("DOMContentLoaded", () => {
    const app = document.getElementById("testApp");
    if (!app) return;

    const storageKey = `mockprep-test-${app.dataset.testId}`;
    const timerValue = document.getElementById("timerValue");
    const questionPosition = document.getElementById("questionPosition");
    const questionTotal = document.getElementById("questionTotal");
    const questionText = document.getElementById("questionText");
    const questionMeta = document.getElementById("questionMeta");
    const optionsContainer = document.getElementById("optionsContainer");
    const quizProgress = document.getElementById("quizProgress");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const clearBtn = document.getElementById("clearBtn");
    const bookmarkBtn = document.getElementById("bookmarkBtn");
    const paletteGrid = document.getElementById("paletteGrid");
    const submitBtn = document.getElementById("submitBtn");
    const instructionsList = document.getElementById("instructionsList");

    const state = {
        test: null,
        currentIndex: 0,
        answers: {},
        review: {},
        seen: {},
        remainingSeconds: 0,
        intervalId: null,
        startedAt: Date.now(),
    };

    function saveState() {
        localStorage.setItem(storageKey, JSON.stringify({
            currentIndex: state.currentIndex,
            answers: state.answers,
            review: state.review,
            seen: state.seen,
            remainingSeconds: state.remainingSeconds,
            startedAt: state.startedAt,
        }));
    }

    function loadState() {
        const raw = localStorage.getItem(storageKey);
        if (!raw) return;
        try {
            const parsed = JSON.parse(raw);
            state.currentIndex = parsed.currentIndex || 0;
            state.answers = parsed.answers || {};
            state.review = parsed.review || {};
            state.seen = parsed.seen || {};
            state.remainingSeconds = parsed.remainingSeconds || 0;
            state.startedAt = parsed.startedAt || Date.now();
        } catch {
            localStorage.removeItem(storageKey);
        }
    }

    function formatTime(totalSeconds) {
        const mins = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
        const secs = Math.floor(totalSeconds % 60).toString().padStart(2, "0");
        return `${mins}:${secs}`;
    }

    function startTimer() {
        if (state.intervalId) clearInterval(state.intervalId);
        timerValue.textContent = formatTime(state.remainingSeconds);
        state.intervalId = setInterval(() => {
            state.remainingSeconds -= 1;
            if (state.remainingSeconds <= 0) {
                state.remainingSeconds = 0;
                timerValue.textContent = "00:00";
                clearInterval(state.intervalId);
                submitTest();
                return;
            }
            timerValue.textContent = formatTime(state.remainingSeconds);
            saveState();
        }, 1000);
    }

    function currentQuestion() {
        return state.test.questions[state.currentIndex];
    }

    function answerFor(questionKey) {
        return state.answers[questionKey] || "";
    }

    function renderPalette() {
        paletteGrid.innerHTML = state.test.questions.map((question, index) => {
            const classes = ["palette-btn"];
            if (index === state.currentIndex) classes.push("current");
            if (state.review[question.question_key]) classes.push("review");
            else if (answerFor(question.question_key)) classes.push("answered");
            return `<button type="button" class="${classes.join(" ")}" data-index="${index}">${index + 1}</button>`;
        }).join("");

        paletteGrid.querySelectorAll("[data-index]").forEach((button) => {
            button.addEventListener("click", () => {
                state.currentIndex = Number(button.dataset.index);
                renderQuestion();
            });
        });
    }

    function optionTemplate(key, value, selectedOption) {
        const selected = selectedOption === key ? "selected" : "";
        return `
            <div class="col-md-6">
                <button type="button" class="option-card ${selected} w-100 text-start" data-option="${key}">
                    <div class="d-flex gap-3"><strong>${key}</strong><span>${value}</span></div>
                </button>
            </div>
        `;
    }

    function renderQuestion() {
        const question = currentQuestion();
        state.seen[question.question_key] = true;
        questionPosition.textContent = state.currentIndex + 1;
        questionTotal.textContent = state.test.questions.length;
        questionText.textContent = question.text;
        questionMeta.textContent = `${question.section} • ${question.marks} mark(s) • -${question.negative_marks}`;
        quizProgress.style.width = `${((state.currentIndex + 1) / state.test.questions.length) * 100}%`;
        bookmarkBtn.textContent = state.review[question.question_key] ? "Marked for review" : "Mark for review";
        prevBtn.disabled = state.currentIndex === 0;
        nextBtn.textContent = state.currentIndex === state.test.questions.length - 1 ? "Save & finish" : "Save & next";

        optionsContainer.innerHTML = Object.entries(question.options)
            .map(([key, value]) => optionTemplate(key, value, answerFor(question.question_key)))
            .join("");

        optionsContainer.querySelectorAll("[data-option]").forEach((button) => {
            button.addEventListener("click", () => {
                state.answers[question.question_key] = button.dataset.option;
                saveState();
                renderQuestion();
            });
        });

        renderPalette();
        saveState();
    }

    function moveNext() {
        if (state.currentIndex >= state.test.questions.length - 1) {
            submitTest();
            return;
        }
        state.currentIndex += 1;
        renderQuestion();
    }

    async function submitTest() {
        if (state.intervalId) clearInterval(state.intervalId);
        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting...";
        nextBtn.disabled = true;
        const answers = state.test.questions.map((question) => ({
            question_key: question.question_key,
            selected_option: answerFor(question.question_key),
        }));
        const spentSeconds = (state.test.duration_minutes * 60) - state.remainingSeconds;
        const response = await fetch(app.dataset.submitUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ test_id: app.dataset.testId, answers, time_taken_seconds: spentSeconds }),
        });
        const result = await response.json();
        localStorage.removeItem(storageKey);
        window.location.href = result.redirect_url;
    }

    prevBtn.addEventListener("click", () => {
        if (state.currentIndex === 0) return;
        state.currentIndex -= 1;
        renderQuestion();
    });

    nextBtn.addEventListener("click", moveNext);

    clearBtn.addEventListener("click", () => {
        delete state.answers[currentQuestion().question_key];
        saveState();
        renderQuestion();
    });

    bookmarkBtn.addEventListener("click", () => {
        const key = currentQuestion().question_key;
        state.review[key] = !state.review[key];
        saveState();
        renderQuestion();
    });

    submitBtn.addEventListener("click", submitTest);

    async function init() {
        loadState();
        const response = await fetch(app.dataset.testApi);
        const test = await response.json();
        if (!response.ok) {
            window.location.href = test.redirect || "/";
            return;
        }
        state.test = test;
        instructionsList.innerHTML = test.instructions.map((item) => `<li>${item}</li>`).join("");
        if (!state.remainingSeconds) state.remainingSeconds = test.duration_minutes * 60;
        startTimer();
        renderQuestion();
    }

    init();
});
