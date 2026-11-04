// Telegram WebApp Initialization
const tg = window.Telegram?.WebApp || null;
if (tg) {
  tg.expand();
  tg.ready();
}

// Global App State
let currentUser = {
  id: tg?.initDataUnsafe?.user?.id || 1438313297,
  first_name: tg?.initDataUnsafe?.user?.first_name || "Mehmon",
  username: tg?.initDataUnsafe?.user?.username || "",
  unlocked_max_ticket: 3,
  vip_until: null,
  invited_count: 0
};

let allQuestions = [];
let currentQuiz = {
  mode: 'ticket', // 'ticket' | 'exam' | 'mistakes'
  ticketId: 1,
  questions: [],
  currentIndex: 0,
  answers: {}, // questionId: selectedIndex
  timerInterval: null,
  timeLeft: 20 * 60 // 20 minutes
};

let userMistakes = [];

// Visual SVG generator for road diagrams
function getDiagramSvg(type) {
  switch (type) {
    case 'sign_danger':
      return `<svg width="100" height="90" viewBox="0 0 100 90">
        <polygon points="50,10 90,80 10,80" fill="#ffffff" stroke="#ef4444" stroke-width="8" stroke-linejoin="round"/>
        <text x="50" y="68" font-size="34" font-weight="bold" fill="#000" text-anchor="middle">!</text>
      </svg>`;
    case 'crossroad_equal':
      return `<svg width="180" height="120" viewBox="0 0 180 120">
        <rect width="180" height="120" fill="#334155"/>
        <rect x="70" y="0" width="40" height="120" fill="#64748b"/>
        <rect x="0" y="40" width="180" height="40" fill="#64748b"/>
        <line x1="90" y1="0" x2="90" y2="40" stroke="#fff" stroke-dasharray="6,6" stroke-width="2"/>
        <line x1="90" y1="80" x2="90" y2="120" stroke="#fff" stroke-dasharray="6,6" stroke-width="2"/>
        <line x1="0" y1="60" x2="70" y2="60" stroke="#fff" stroke-dasharray="6,6" stroke-width="2"/>
        <line x1="110" y1="60" x2="180" y2="60" stroke="#fff" stroke-dasharray="6,6" stroke-width="2"/>
        <rect x="78" y="85" width="24" height="18" rx="4" fill="#3b82f6"/>
        <text x="90" y="98" fill="#fff" font-size="10" font-weight="bold" text-anchor="middle">A</text>
        <rect x="135" y="48" width="18" height="24" rx="4" fill="#ef4444"/>
        <text x="144" y="64" fill="#fff" font-size="10" font-weight="bold" text-anchor="middle">B</text>
      </svg>`;
    case 'speed_limit_60':
      return `<svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r="40" fill="#ffffff" stroke="#ef4444" stroke-width="8"/>
        <text x="45" y="55" font-size="28" font-weight="900" fill="#000" text-anchor="middle">60</text>
      </svg>`;
    case 'priority_main_road':
      return `<svg width="90" height="90" viewBox="0 0 90 90">
        <rect x="45" y="10" width="50" height="50" transform="rotate(45 45 10)" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
        <rect x="45" y="16" width="42" height="42" transform="rotate(45 45 16)" fill="#fbbf24"/>
      </svg>`;
    case 'sign_no_overtaking':
      return `<svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r="40" fill="#ffffff" stroke="#ef4444" stroke-width="8"/>
        <rect x="25" y="42" width="18" height="12" rx="2" fill="#ef4444"/>
        <rect x="47" y="42" width="18" height="12" rx="2" fill="#000"/>
      </svg>`;
    case 'traffic_light_yellow_flash':
      return `<svg width="60" height="120" viewBox="0 0 60 120">
        <rect width="60" height="120" rx="10" fill="#1e293b"/>
        <circle cx="30" cy="25" r="14" fill="#334155"/>
        <circle cx="30" cy="60" r="14" fill="#fbbf24" stroke="#fef08a" stroke-width="3"/>
        <circle cx="30" cy="95" r="14" fill="#334155"/>
      </svg>`;
    default:
      return `<svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r="38" fill="#e0e7ff" stroke="#3b82f6" stroke-width="4"/>
        <text x="45" y="55" font-size="34" font-weight="bold" fill="#3b82f6" text-anchor="middle">🚗</text>
      </svg>`;
  }
}

// Fetch user status from backend API
async function loadUserData() {
  try {
    const res = await fetch(`/api/user_status?user_id=${currentUser.id}&first_name=${encodeURIComponent(currentUser.first_name)}&username=${encodeURIComponent(currentUser.username)}`);
    if (res.ok) {
      const data = await res.json();
      currentUser = { ...currentUser, ...data };
      updateHeaderUI();
      renderTickets();
      loadMistakes();
    }
  } catch (e) {
    console.error("User data load error:", e);
    renderTickets();
  }
}

// Fetch all questions
async function loadQuestions() {
  try {
    const res = await fetch('/api/questions');
    if (res.ok) {
      allQuestions = await res.json();
    }
  } catch (e) {
    console.error("Questions load error:", e);
  }
}

// Update Top Bar
function updateHeaderUI() {
  document.getElementById('user-name').innerText = currentUser.first_name;
  const max = currentUser.unlocked_max_ticket;
  const badgeText = max >= 10 ? "⭐ Barcha biletlar ochiq" : `🟢 1–${max} biletlar ochiq`;
  document.getElementById('user-badge').innerText = badgeText;

  // Referral UI
  document.getElementById('ref-invited-count').innerText = currentUser.invited_count || 0;
  document.getElementById('ref-earned-tickets').innerText = `+${Math.max(0, currentUser.unlocked_max_ticket - 3)}`;
  
  const botUser = window.BOT_USERNAME || "prava_yhq_test_bot";
  const refLink = `https://t.me/${botUser}?start=ref_${currentUser.id}`;
  document.getElementById('ref-link-input').value = refLink;
}

// Render Tickets
function renderTickets() {
  const container = document.getElementById('tickets-grid');
  container.innerHTML = '';
  const max = currentUser.unlocked_max_ticket;

  for (let i = 1; i <= 10; i++) {
    const isUnlocked = i <= max;
    const card = document.createElement('div');
    card.className = `ticket-card ${isUnlocked ? 'unlocked' : 'locked'}`;
    
    card.innerHTML = `
      <div class="ticket-top">
        <span class="ticket-num">${i}-Bilet</span>
        <span class="ticket-status-icon">${isUnlocked ? '🟢' : '🔒'}</span>
      </div>
      <div class="ticket-desc">20 ta savol • 20 daqiqa</div>
      <span class="ticket-badge ${isUnlocked ? (i <= 3 ? 'free' : 'passed') : 'locked-badge'}">
        ${isUnlocked ? (i <= 3 ? 'BEPUL' : 'OCHILGAN') : 'QULFLANGAN'}
      </span>
    `;

    card.onclick = () => {
      if (isUnlocked) {
        startQuizForTicket(i);
      } else {
        openPaymentForTicket(i);
      }
    };

    container.appendChild(card);
  }
}

// Start Quiz for Specific Ticket
function startQuizForTicket(ticketId) {
  const ticketQuestions = allQuestions.filter(q => q.ticket_id === ticketId);
  if (!ticketQuestions.length) return;

  currentQuiz = {
    mode: 'ticket',
    ticketId: ticketId,
    questions: ticketQuestions,
    currentIndex: 0,
    answers: {},
    timerInterval: null,
    timeLeft: 20 * 60
  };

  showView('quiz');
  renderCurrentQuestion();
  startTimer();
}

// Start Exam Mode (20 random questions)
function startExamMode() {
  if (!allQuestions.length) return;
  const shuffled = [...allQuestions].sort(() => 0.5 - Math.random()).slice(0, 20);

  currentQuiz = {
    mode: 'exam',
    ticketId: 0,
    questions: shuffled,
    currentIndex: 0,
    answers: {},
    timerInterval: null,
    timeLeft: 20 * 60
  };

  showView('quiz');
  renderCurrentQuestion();
  startTimer();
}

// Render Current Question
function renderCurrentQuestion() {
  const q = currentQuiz.questions[currentQuiz.currentIndex];
  if (!q) return;

  document.getElementById('quiz-counter').innerText = `${currentQuiz.currentIndex + 1} / ${currentQuiz.questions.length}`;
  const pct = ((currentQuiz.currentIndex + 1) / currentQuiz.questions.length) * 100;
  document.getElementById('progress-fill').style.width = `${pct}%`;

  // Road SVG Diagram
  document.getElementById('question-media').innerHTML = getDiagramSvg(q.image);
  document.getElementById('question-text').innerText = q.question;

  // Render Options
  const list = document.getElementById('options-list');
  list.innerHTML = '';

  const letters = ['A', 'B', 'C', 'D'];
  const hasAnswered = currentQuiz.answers[q.id] !== undefined;

  q.options.forEach((opt, idx) => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.innerHTML = `<span class="option-marker">${letters[idx]}</span> <span>${opt}</span>`;

    if (hasAnswered) {
      const selected = currentQuiz.answers[q.id];
      if (idx === q.correct) {
        btn.classList.add('correct');
      } else if (idx === selected) {
        btn.classList.add('wrong');
      }
      btn.disabled = true;
    } else {
      btn.onclick = () => selectOption(idx);
    }

    list.appendChild(btn);
  });

  // AI Explanation Box
  const aiBox = document.getElementById('ai-box');
  if (hasAnswered) {
    const selected = currentQuiz.answers[q.id];
    const isCorrect = selected === q.correct;
    document.getElementById('ai-text').innerText = q.explanation;
    aiBox.style.display = 'block';
  } else {
    aiBox.style.display = 'none';
  }

  // Prev / Next Buttons
  document.getElementById('prev-btn').disabled = currentQuiz.currentIndex === 0;
  document.getElementById('next-btn').innerText = (currentQuiz.currentIndex === currentQuiz.questions.length - 1) ? 'Yakunlash 🏁' : 'Keyingisi ➡';
}

// Option Selected
function selectOption(selectedIdx) {
  const q = currentQuiz.questions[currentQuiz.currentIndex];
  currentQuiz.answers[q.id] = selectedIdx;

  const isCorrect = selectedIdx === q.correct;

  // Send to backend for smart mistake tracking
  fetch('/api/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUser.id,
      question_id: q.id,
      is_correct: isCorrect
    })
  });

  renderCurrentQuestion();
}

function nextQuestion() {
  if (currentQuiz.currentIndex < currentQuiz.questions.length - 1) {
    currentQuiz.currentIndex++;
    renderCurrentQuestion();
  } else {
    finishQuiz();
  }
}

function prevQuestion() {
  if (currentQuiz.currentIndex > 0) {
    currentQuiz.currentIndex--;
    renderCurrentQuestion();
  }
}

// Finish Quiz & Show Result
function finishQuiz() {
  clearInterval(currentQuiz.timerInterval);

  let correctCount = 0;
  currentQuiz.questions.forEach(q => {
    if (currentQuiz.answers[q.id] === q.correct) {
      correctCount++;
    }
  });

  const total = currentQuiz.questions.length;
  const passed = correctCount >= (total === 20 ? 18 : Math.round(total * 0.9));

  document.getElementById('result-score').innerText = `${correctCount} / ${total}`;
  document.getElementById('result-icon').innerText = passed ? '🎉' : '⚠️';
  document.getElementById('result-status').innerText = passed ? 'Imtihondan o\'tdingiz!' : 'Yana tayyorgarlik ko\'ring';
  document.getElementById('result-msg').innerText = passed 
    ? "Ajoyib natija! Siz haqiqiy Davlat YHQ imtihoniga to'liq tayyorsiz." 
    : "Davlat imtihonidan o'tish uchun kamida 18 ta to'g'ri javob kerak. Xatolaringiz ustida ishlang!";

  // Save result to backend
  if (currentQuiz.mode === 'ticket') {
    fetch('/api/test_result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.id,
        ticket_id: currentQuiz.ticketId,
        score: correctCount,
        total: total
      })
    });
  }

  showView('result');
}

function restartCurrentQuiz() {
  currentQuiz.currentIndex = 0;
  currentQuiz.answers = {};
  showView('quiz');
  renderCurrentQuestion();
  startTimer();
}

function exitQuiz() {
  clearInterval(currentQuiz.timerInterval);
  showView('tickets');
}

// Timer
function startTimer() {
  clearInterval(currentQuiz.timerInterval);
  currentQuiz.timeLeft = 20 * 60;

  currentQuiz.timerInterval = setInterval(() => {
    currentQuiz.timeLeft--;
    if (currentQuiz.timeLeft <= 0) {
      clearInterval(currentQuiz.timerInterval);
      finishQuiz();
      return;
    }

    const mins = Math.floor(currentQuiz.timeLeft / 60);
    const secs = currentQuiz.timeLeft % 60;
    document.getElementById('quiz-timer').innerText = `⏱ ${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }, 1000);
}

// Load Mistakes
async function loadMistakes() {
  try {
    const res = await fetch(`/api/mistakes?user_id=${currentUser.id}`);
    if (res.ok) {
      userMistakes = await res.json();
      renderMistakesUI();
    }
  } catch (e) {
    console.error("Mistakes load error:", e);
  }
}

function renderMistakesUI() {
  const countSpan = document.getElementById('mistakes-count');
  const emptyDiv = document.getElementById('mistakes-empty');
  const listDiv = document.getElementById('mistakes-list');
  const btn = document.getElementById('solve-mistakes-btn');

  countSpan.innerText = `${userMistakes.length} ta xato`;

  if (userMistakes.length === 0) {
    emptyDiv.style.display = 'block';
    listDiv.innerHTML = '';
    btn.style.display = 'none';
    return;
  }

  emptyDiv.style.display = 'none';
  btn.style.display = 'block';
  listDiv.innerHTML = '';

  userMistakes.forEach((q, idx) => {
    const item = document.createElement('div');
    item.className = 'mistake-item';
    item.innerHTML = `
      <h4>${idx + 1}. ${q.question}</h4>
      <p>💡 <b>YHQ Qoidasi:</b> ${q.explanation}</p>
    `;
    listDiv.appendChild(item);
  });
}

function startMistakesPractice() {
  if (!userMistakes.length) return;
  currentQuiz = {
    mode: 'mistakes',
    ticketId: 0,
    questions: userMistakes,
    currentIndex: 0,
    answers: {},
    timerInterval: null,
    timeLeft: 20 * 60
  };

  showView('quiz');
  renderCurrentQuestion();
  startTimer();
}

function openMistakesView() {
  switchTab('mistakes');
}

// Navigation Tabs
function switchTab(tab) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  if (tab === 'tickets') {
    document.getElementById('view-tickets').classList.add('active');
    document.getElementById('nav-tickets').classList.add('active');
  } else if (tab === 'mistakes') {
    document.getElementById('view-mistakes').classList.add('active');
    document.getElementById('nav-mistakes').classList.add('active');
    loadMistakes();
  } else if (tab === 'referral') {
    document.getElementById('view-referral').classList.add('active');
    document.getElementById('nav-referral').classList.add('active');
  } else if (tab === 'buy') {
    document.getElementById('view-buy').classList.add('active');
    document.getElementById('nav-buy').classList.add('active');
  }
}

function showView(viewName) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(`view-${viewName}`).classList.add('active');
}

// Payment Modal Logic
function openPaymentForTicket(ticketNum) {
  if (ticketNum >= 4 && ticketNum <= 6) {
    openPaymentModal('pack_4_6', '4–6 biletlar (60 ta savol)', '5 000');
  } else if (ticketNum >= 7 && ticketNum <= 10) {
    openPaymentModal('pack_7_10', '7–10 biletlar (80 ta savol)', '10 000');
  } else {
    openPaymentModal('pack_11_14', '11–14 biletlar', '10 000');
  }
}

function openPaymentModal(pkgKey, title, price) {
  document.getElementById('modal-title').innerText = title;
  document.getElementById('modal-price').innerText = `${price} so'm`;
  document.getElementById('payment-modal').classList.add('active');
}

function closePaymentModal() {
  document.getElementById('payment-modal').classList.remove('active');
}

function copyCardNumber() {
  const card = document.getElementById('modal-card').innerText;
  navigator.clipboard.writeText(card.replace(/\s+/g, ''));
  alert("Karta raqami nusxalandi!");
}

function closeModalAndGoToBot() {
  closePaymentModal();
  if (tg) {
    tg.close();
  }
}

// Referral Share & Copy
function copyRefLink() {
  const input = document.getElementById('ref-link-input');
  input.select();
  navigator.clipboard.writeText(input.value);
  alert("Referral havolangiz nusxalandi! Do'stlaringizga yuboring.");
}

function shareRefLink() {
  const link = document.getElementById('ref-link-input').value;
  const text = encodeURIComponent("🚗 Haydovchilik guvohnomasi (Prava) imtihoniga tayyorgarlik ko'rish uchun ajoyib bot! Sinab ko'ring:");
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${text}`;
  if (tg) {
    tg.openTelegramLink(shareUrl);
  } else {
    window.open(shareUrl, '_blank');
  }
}

// Init
window.onload = async () => {
  await loadQuestions();
  await loadUserData();
};
