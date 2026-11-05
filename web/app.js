// Telegram WebApp Initialization
const tg = window.Telegram?.WebApp || null;
if (tg) {
  try {
    tg.expand();
    tg.ready();
  } catch (e) {
    console.warn("Telegram WebApp expand warning:", e);
  }
}

// Global App State
let currentLang = localStorage.getItem('prava_app_lang') || 'uz'; // 'uz' | 'ru'

let currentUser = {
  id: tg?.initDataUnsafe?.user?.id || 1438313297,
  first_name: tg?.initDataUnsafe?.user?.first_name || "Foydalanuvchi",
  username: tg?.initDataUnsafe?.user?.username || "",
  is_vip: false,
  vip_until: null,
  has_exam_pass: false,
  exam_pass_until: null,
  exam_attempts: 0,
  can_take_exam: false,
  unlocked_tickets: [1, 2, 3],
  total_tickets: 70
};

let allBilets = [];
let allQuestions = [];
let selectedPickerTickets = new Set();

let currentQuiz = {
  mode: 'ticket', // 'ticket' | 'exam' | 'mistakes'
  ticketId: 1,
  questions: [],
  currentIndex: 0,
  answers: {},
  timerInterval: null,
  timeLeft: 20 * 60
};

let userMistakes = [];

// Til lug'ati (Translations)
const T = {
  uz: {
    hero_title: "🚗 Rasmiy Davlat YHQ Testlari",
    hero_desc: "1200 ta rasmiy imtihon savollari va haqiqiy rasmlar",
    hero_btn: "⚡ 20 talik Tasodifiy Imtihon",
    tickets_title: "📚 Biletlar ro'yxati",
    tickets_free_tag: "1–3 biletlar BEPUL",
    ticket_num: "Bilet",
    ticket_desc: "20 ta savol • 20 daqiqa",
    badge_free: "BEPUL",
    badge_unlocked: "OCHILGAN",
    badge_locked: "🔒 QULFLANGAN",
    btn_back: "⬅ Chiqish",
    btn_prev: "⬅ Oldingisi",
    btn_next: "Keyingisi ➡",
    btn_finish: "Yakunlash 🏁",
    ai_title: "🤖 YHQ Qoidasi va Tushuntirish:",
    result_passed: "Muvaffaqiyatli topshirdingiz!",
    result_failed: "Yana tayyorgarlik ko'ring",
    result_msg_passed: "Ajoyib natija! Siz haqiqiy Davlat YHQ nazariy imtihoniga to'liq tayyorsiz.",
    result_msg_failed: "Davlat imtihonidan o'tish uchun kamida 18 ta to'g'ri javob talab etiladi. Xatolar ustida ishlang!",
    result_retry: "🔄 Qaytadan ishlash",
    result_mistakes: "🤖 Xatolar ustida ishlash",
    result_home: "Bosh sahifaga qaytish",
    nav_tickets: "Biletlar",
    nav_mistakes: "Xatolar",
    nav_referral: "Do'stlar",
    nav_vip: "Tariflar",
    badge_vip: "👑 VIP A'zo",
    badge_normal: "ta bilet ochiq",
    loading: "Yuklanmoqda..."
  },
  ru: {
    hero_title: "🚗 Официальные экзаменационные тесты ПДД",
    hero_desc: "1200 официальных экзаменационных билетов и реальные схемы",
    hero_btn: "⚡ Случайный экзамен (20 вопросов)",
    tickets_title: "📚 Список билетов",
    tickets_free_tag: "1–3 билеты БЕСПЛАТНО",
    ticket_num: "Билет",
    ticket_desc: "20 вопросов • 20 минут",
    badge_free: "БЕСПЛАТНО",
    badge_unlocked: "ОТКРЫТО",
    badge_locked: "🔒 ЗАКРЫТО",
    btn_back: "⬅ Выход",
    btn_prev: "⬅ Предыдущий",
    btn_next: "Следующий ➡",
    btn_finish: "Завершить 🏁",
    ai_title: "🤖 Пояснение ПДД:",
    result_passed: "Экзамен успешно сдан!",
    result_failed: "Попробуйте ещё раз",
    result_msg_passed: "Отличный результат! Вы полностью готовы к официальному экзамену ПДД.",
    result_msg_failed: "Для сдачи экзамена необходимо минимум 18 правильных ответов. Работайте над ошибками!",
    result_retry: "🔄 Пройти заново",
    result_mistakes: "🤖 Работа над ошибками",
    result_home: "На главную",
    nav_tickets: "Билеты",
    nav_mistakes: "Ошибки",
    nav_referral: "Друзья",
    nav_vip: "Тарифы",
    badge_vip: "👑 VIP Член",
    badge_normal: "билетов открыто",
    loading: "Загрузка..."
  }
};

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('prava_app_lang', lang);

  const uzBtn = document.getElementById('lang-uz');
  const ruBtn = document.getElementById('lang-ru');
  if (uzBtn) uzBtn.classList.toggle('active', lang === 'uz');
  if (ruBtn) ruBtn.classList.toggle('active', lang === 'ru');

  applyLanguageTexts();
  updateHeaderUI();
  renderTickets();

  if (currentQuiz.questions && currentQuiz.questions.length > 0) {
    renderCurrentQuestion();
  }
  if (userMistakes.length > 0) {
    renderMistakesUI();
  }
}

function applyLanguageTexts() {
  const t = T[currentLang];
  const setText = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
  };

  setText('tickets-title', `${t.tickets_title} (1 – ${allBilets.length || 70})`);
  setText('tickets-info-tag', t.tickets_free_tag);
  
  const heroH2 = document.querySelector('.hero-text h2');
  if (heroH2) heroH2.innerText = t.hero_title;
  const heroP = document.querySelector('.hero-text p');
  if (heroP) heroP.innerText = t.hero_desc;
  const heroBtn = document.querySelector('.hero-btn');
  if (heroBtn) heroBtn.innerText = t.hero_btn;

  const navT = document.querySelector('#nav-tickets .nav-label');
  if (navT) navT.innerText = t.nav_tickets;
  const navM = document.querySelector('#nav-mistakes .nav-label');
  if (navM) navM.innerText = t.nav_mistakes;
  const navR = document.querySelector('#nav-referral .nav-label');
  if (navR) navR.innerText = t.nav_referral;
  const navB = document.querySelector('#nav-buy .nav-label');
  if (navB) navB.innerText = t.nav_vip;

  const backBtn = document.querySelector('.back-btn');
  if (backBtn) backBtn.innerText = t.btn_back;
  const prevBtn = document.getElementById('prev-btn');
  if (prevBtn) prevBtn.innerText = t.btn_prev;
}

// 1. Foydalanuvchi holatini ma'lumotlar bazasidan olish
async function loadUserData() {
  try {
    const res = await fetch(`/api/user_status?user_id=${currentUser.id}&first_name=${encodeURIComponent(currentUser.first_name)}&username=${encodeURIComponent(currentUser.username)}`);
    if (res.ok) {
      const data = await res.json();
      currentUser = {
        ...currentUser,
        is_vip: data.is_vip || false,
        vip_until: data.vip_until || null,
        has_exam_pass: data.has_exam_pass || false,
        exam_pass_until: data.exam_pass_until || null,
        exam_attempts: data.exam_attempts || 0,
        can_take_exam: data.can_take_exam || false,
        unlocked_tickets: Array.isArray(data.unlocked_tickets) ? data.unlocked_tickets : [1, 2, 3],
        total_tickets: data.total_tickets || 70
      };
      updateHeaderUI();
      renderTickets();
      loadMistakes();
    }
  } catch (e) {
    console.error("User data load error:", e);
    renderTickets();
  }
}

// 2. Savollarni yuklash
async function loadQuestions() {
  try {
    const res = await fetch('/api/questions');
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        allQuestions = data;
        const bNums = [...new Set(allQuestions.map(q => q.biletNumber || q.ticket_id || 1))].sort((a,b) => a - b);
        allBilets = bNums.map(n => ({ number: n, title: `${n}-Bilet` }));
      } else if (data && data.questions) {
        allQuestions = data.questions;
        allBilets = data.bilets || [];
      }
      applyLanguageTexts();
      renderTickets();
    }
  } catch (e) {
    console.error("Questions load error:", e);
  }
}

// 3. Header panelini yangilash
function updateHeaderUI() {
  const nameEl = document.getElementById('user-name');
  if (nameEl) nameEl.innerText = currentUser.first_name;
  
  const t = T[currentLang];
  const badge = document.getElementById('user-badge');

  if (badge) {
    if (currentUser.is_vip) {
      badge.innerText = t.badge_vip;
      badge.style.background = "#fef3c7";
      badge.style.color = "#b45309";
    } else {
      const count = currentUser.unlocked_tickets ? currentUser.unlocked_tickets.length : 3;
      badge.innerText = `🟢 ${count} ${t.badge_normal}`;
      badge.style.background = "#d1fae5";
      badge.style.color = "#065f46";
    }
  }

  // Referral UI
  const refCount = document.getElementById('ref-unlocked-count');
  if (refCount) refCount.innerText = currentUser.unlocked_tickets ? currentUser.unlocked_tickets.length : 3;
  const refVip = document.getElementById('ref-vip-status');
  if (refVip) refVip.innerText = currentUser.is_vip ? "👑 VIP" : (currentUser.has_exam_pass ? "⚡ Imtihon" : "Oddiy");
  
  const botUser = "prava_test_AI_bot";
  const refLink = `https://t.me/${botUser}?start=ref_${currentUser.id}`;
  const refInput = document.getElementById('ref-link-input');
  if (refInput) refInput.value = refLink;
}

// 4. Biletlar ro'yxatini chiqarish
function renderTickets() {
  const container = document.getElementById('tickets-grid');
  if (!container) return;
  container.innerHTML = '';

  const t = T[currentLang];
  const totalCount = allBilets.length > 0 ? allBilets.length : (currentUser.total_tickets || 70);
  
  const titleEl = document.getElementById('tickets-title');
  if (titleEl) titleEl.innerText = `${t.tickets_title} (1 – ${totalCount})`;

  for (let i = 1; i <= totalCount; i++) {
    const isUnlocked = currentUser.is_vip || (currentUser.unlocked_tickets && currentUser.unlocked_tickets.includes(i));
    const card = document.createElement('div');
    card.className = `ticket-card ${isUnlocked ? 'unlocked' : 'locked'}`;

    let badgeClass = 'locked-badge';
    let badgeText = t.badge_locked;

    if (isUnlocked) {
      if (i <= 3) {
        badgeClass = 'free';
        badgeText = t.badge_free;
      } else {
        badgeClass = 'passed';
        badgeText = t.badge_unlocked;
      }
    }

    card.innerHTML = `
      <div class="ticket-top">
        <span class="ticket-num">${i}-${t.ticket_num}</span>
        <span class="ticket-status-icon">${isUnlocked ? '🟢' : '🔒'}</span>
      </div>
      <div class="ticket-desc">${t.ticket_desc}</div>
      <span class="ticket-badge ${badgeClass}">${badgeText}</span>
    `;

    card.onclick = () => {
      if (isUnlocked) {
        startQuizForTicket(i);
      } else {
        // Qulflangan bilet bosilganda 3 ta bilet tanlash oynasini ochamiz!
        openTicketPickerModal(i);
      }
    };

    container.appendChild(card);
  }
}

// 5. Muayyan bilet bo'yicha testni boshlash
function startQuizForTicket(ticketNumber) {
  const ticketQuestions = allQuestions.filter(q => (q.biletNumber === ticketNumber || q.ticket_id === ticketNumber));
  if (!ticketQuestions.length) {
    alert(T[currentLang].loading);
    return;
  }

  currentQuiz = {
    mode: 'ticket',
    ticketId: ticketNumber,
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

// 6. 20 talik Imtihonni topshirish
function handleStartExamClick() {
  if (currentUser.can_take_exam) {
    // 1 ta urinishni sarflash
    fetch('/api/consume_exam', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: currentUser.id })
    }).catch(e => console.warn(e));

    startExamMode();
  } else {
    // Imtihon ruxsatini xarid qilish oynasini ochish
    openExamAccessModal();
  }
}

function startExamMode() {
  if (!allQuestions.length) {
    alert(T[currentLang].loading);
    return;
  }
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

// 7. Savolni ekranga chiqarish
function renderCurrentQuestion() {
  const q = currentQuiz.questions[currentQuiz.currentIndex];
  if (!q) return;

  const t = T[currentLang];

  document.getElementById('quiz-counter').innerText = `${currentQuiz.currentIndex + 1} / ${currentQuiz.questions.length}`;
  const pct = ((currentQuiz.currentIndex + 1) / currentQuiz.questions.length) * 100;
  document.getElementById('progress-fill').style.width = `${pct}%`;

  const mediaContainer = document.getElementById('question-media');
  const imgUrl = q.imageUrl || (q.image ? `/media/${q.image}` : null);

  if (imgUrl) {
    mediaContainer.style.display = 'flex';
    mediaContainer.innerHTML = `<img src="${imgUrl}" class="question-img" alt="Yo'l harakati holati" onerror="this.onerror=null; this.parentElement.style.display='none';" />`;
  } else {
    mediaContainer.style.display = 'none';
    mediaContainer.innerHTML = '';
  }

  const qText = (currentLang === 'ru') ? (q.text_ru || q.text) : (q.text_uz || q.text);
  document.getElementById('question-text').innerText = qText;

  const list = document.getElementById('options-list');
  list.innerHTML = '';

  const letters = ['A', 'B', 'C', 'D'];
  const hasAnswered = currentQuiz.answers[q.id] !== undefined;
  const correctIdx = (q.correctOptionIndex !== undefined) ? q.correctOptionIndex : q.correct;

  const options = (currentLang === 'ru') ? (q.options_ru || q.options || []) : (q.options_uz || q.options || []);
  options.forEach((optText, idx) => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.innerHTML = `<span class="option-marker">${letters[idx] || (idx + 1)}</span> <span>${optText}</span>`;

    if (hasAnswered) {
      const selected = currentQuiz.answers[q.id];
      if (idx === correctIdx) {
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

  const aiBox = document.getElementById('ai-box');
  const qExp = (currentLang === 'ru') ? (q.explanation_ru || q.explanation) : (q.explanation_uz || q.explanation);
  
  if (hasAnswered && qExp) {
    const aiTitle = document.querySelector('.ai-title');
    if (aiTitle) aiTitle.innerHTML = `<b>${t.ai_title}</b>`;
    document.getElementById('ai-text').innerText = qExp;
    aiBox.style.display = 'block';
  } else {
    aiBox.style.display = 'none';
  }

  document.getElementById('prev-btn').disabled = currentQuiz.currentIndex === 0;
  document.getElementById('next-btn').innerText = (currentQuiz.currentIndex === currentQuiz.questions.length - 1) ? t.btn_finish : t.btn_next;
}

// 8. Variant tanlanganda
function selectOption(selectedIdx) {
  const q = currentQuiz.questions[currentQuiz.currentIndex];
  currentQuiz.answers[q.id] = selectedIdx;

  const correctIdx = (q.correctOptionIndex !== undefined) ? q.correctOptionIndex : q.correct;
  const isCorrect = (selectedIdx === correctIdx);

  fetch('/api/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUser.id,
      question_id: q.id,
      is_correct: isCorrect
    })
  }).catch(e => console.warn(e));

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

// 9. Testni yakunlash
function finishQuiz() {
  clearInterval(currentQuiz.timerInterval);
  const t = T[currentLang];

  let correctCount = 0;
  currentQuiz.questions.forEach(q => {
    const correctIdx = (q.correctOptionIndex !== undefined) ? q.correctOptionIndex : q.correct;
    if (currentQuiz.answers[q.id] === correctIdx) {
      correctCount++;
    }
  });

  const total = currentQuiz.questions.length;
  const passed = correctCount >= (total === 20 ? 18 : Math.round(total * 0.9));

  document.getElementById('result-score').innerText = `${correctCount} / ${total}`;
  document.getElementById('result-icon').innerText = passed ? '🎉' : '⚠️';
  document.getElementById('result-status').innerText = passed ? t.result_passed : t.result_failed;
  document.getElementById('result-msg').innerText = passed ? t.result_msg_passed : t.result_msg_failed;

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
    }).catch(e => console.warn(e));
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

// 10. Xatolar ustida ishlash
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
  const t = T[currentLang];
  const countSpan = document.getElementById('mistakes-count');
  const emptyDiv = document.getElementById('mistakes-empty');
  const listDiv = document.getElementById('mistakes-list');
  const btn = document.getElementById('solve-mistakes-btn');

  if (countSpan) countSpan.innerText = `${userMistakes.length} ta xato`;

  if (userMistakes.length === 0) {
    if (emptyDiv) emptyDiv.style.display = 'block';
    if (listDiv) listDiv.innerHTML = '';
    if (btn) btn.style.display = 'none';
    return;
  }

  if (emptyDiv) emptyDiv.style.display = 'none';
  if (btn) btn.style.display = 'block';
  if (listDiv) listDiv.innerHTML = '';

  userMistakes.forEach((q, idx) => {
    const item = document.createElement('div');
    item.className = 'mistake-item';
    const qText = (currentLang === 'ru') ? (q.text_ru || q.text) : (q.text_uz || q.text);
    const qExp = (currentLang === 'ru') ? (q.explanation_ru || q.explanation) : (q.explanation_uz || q.explanation);

    item.innerHTML = `
      <h4>${idx + 1}. ${qText}</h4>
      <p>💡 <b>${t.ai_title}</b> ${qExp || "..."}</p>
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

// 11. Sahifalar almashinuvi
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
  const el = document.getElementById(`view-${viewName}`);
  if (el) el.classList.add('active');
}

// 12. 3 ta bilet tanlash modali
function openTicketPickerModal(preselectNum = null) {
  selectedPickerTickets.clear();
  if (preselectNum && !currentUser.unlocked_tickets.includes(preselectNum)) {
    selectedPickerTickets.add(preselectNum);
  }

  const grid = document.getElementById('picker-grid');
  grid.innerHTML = '';

  const totalCount = allBilets.length > 0 ? allBilets.length : (currentUser.total_tickets || 70);

  for (let i = 4; i <= totalCount; i++) {
    const isAlreadyUnlocked = currentUser.unlocked_tickets && currentUser.unlocked_tickets.includes(i);
    const chip = document.createElement('div');
    chip.className = 'picker-chip';
    chip.innerText = `${i}-Bilet`;

    if (isAlreadyUnlocked) {
      chip.classList.add('disabled');
      chip.title = "Ochiq";
    } else {
      if (selectedPickerTickets.has(i)) {
        chip.classList.add('selected');
      }

      chip.onclick = () => {
        if (selectedPickerTickets.has(i)) {
          selectedPickerTickets.delete(i);
          chip.classList.remove('selected');
        } else {
          if (selectedPickerTickets.size >= 3) {
            alert("Siz ko'pi bilan 3 ta bilet tanlashingiz mumkin!");
            return;
          }
          selectedPickerTickets.add(i);
          chip.classList.add('selected');
        }
        updatePickerStatus();
      };
    }

    grid.appendChild(chip);
  }

  updatePickerStatus();
  document.getElementById('ticket-picker-modal').classList.add('active');
}

function updatePickerStatus() {
  const count = selectedPickerTickets.size;
  const statusEl = document.getElementById('picker-status');
  const confirmBtn = document.getElementById('picker-confirm-btn');

  if (statusEl) {
    statusEl.innerText = `${count} / 3 ta bilet tanlandi`;
  }
  if (confirmBtn) {
    confirmBtn.disabled = (count === 0);
  }
}

function closeTicketPickerModal() {
  document.getElementById('ticket-picker-modal').classList.remove('active');
}

function confirmTicketSelection() {
  const arr = Array.from(selectedPickerTickets).sort((a,b) => a - b);
  if (!arr.length) return;

  const ticketsStr = arr.join(", ");
  closeTicketPickerModal();
  openPaymentModal(
    'tickets_3',
    `📚 Tanlangan biletlar: ${ticketsStr}`,
    '5 000',
    ticketsStr
  );
}

// 13. Imtihon ruxsati modali
function openExamAccessModal() {
  document.getElementById('exam-access-modal').classList.add('active');
}

function closeExamAccessModal() {
  document.getElementById('exam-access-modal').classList.remove('active');
}

// 14. To'lov modali
async function syncSelectedPayment(pkgKey, title, price, extraDetails) {
  const numericPrice = parseInt(String(price).replace(/\s+/g, '')) || 5000;
  if (currentUser && currentUser.id) {
    try {
      await fetch('/api/select_payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.id,
          payment_type: pkgKey,
          details: title,
          ticket_numbers: extraDetails || '',
          amount: numericPrice
        })
      });
    } catch (e) {
      console.warn("syncSelectedPayment error:", e);
    }
  }
}

function openPaymentModal(pkgKey, title, price, extraDetails = '') {
  document.getElementById('modal-title').innerText = title;
  document.getElementById('modal-price').innerText = `${price} so'm`;
  document.getElementById('modal-instruct-amount').innerText = `${price} so'm`;
  document.getElementById('payment-modal').classList.add('active');

  // Tanlangan biletlar yoki tarifni saqlab qo'yish va serverga yuborish
  window.currentSelectedPayment = {
    pkgKey: pkgKey,
    title: title,
    price: price,
    extra: extraDetails
  };

  syncSelectedPayment(pkgKey, title, price, extraDetails);
}

function closePaymentModal() {
  document.getElementById('payment-modal').classList.remove('active');
}

function copyCardNumber() {
  const card = document.getElementById('modal-card').innerText;
  navigator.clipboard.writeText(card.replace(/\s+/g, ''));
  alert("Karta raqami nusxalandi!");
}

async function closeModalAndGoToBot() {
  if (window.currentSelectedPayment) {
    const p = window.currentSelectedPayment;
    await syncSelectedPayment(p.pkgKey, p.title, p.price, p.extra);
  }
  closePaymentModal();
  if (tg) {
    tg.close();
  }
}

// 15. Referal ulashish
function copyRefLink() {
  const input = document.getElementById('ref-link-input');
  input.select();
  navigator.clipboard.writeText(input.value);
  alert("Referral havolangiz nusxalandi! Do'stlaringizga yuboring.");
}

function shareRefLink() {
  const link = document.getElementById('ref-link-input').value;
  const text = encodeURIComponent("🚗 Haydovchilik guvohnomasi (Prava) imtihoniga tayyorgarlik ko'rish uchun rasmiy test boti! Sinab ko'ring:");
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${text}`;
  if (tg) {
    tg.openTelegramLink(shareUrl);
  } else {
    window.open(shareUrl, '_blank');
  }
}

// 16. Yuklanish
window.onload = async () => {
  setLanguage(currentLang);
  await loadUserData();
  await loadQuestions();
};
