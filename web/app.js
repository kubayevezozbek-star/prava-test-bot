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
let currentUser = {
  id: tg?.initDataUnsafe?.user?.id || 1438313297,
  first_name: tg?.initDataUnsafe?.user?.first_name || "Foydalanuvchi",
  username: tg?.initDataUnsafe?.user?.username || "",
  is_vip: false,
  vip_until: null,
  unlocked_tickets: [1, 2, 3],
  total_tickets: 70
};

let allBilets = [];
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

// 1. Foydalanuvchi holatini ma'lumotlar bazasidan olish (Doimiy saqlanadi!)
async function loadUserData() {
  try {
    const res = await fetch(`/api/user_status?user_id=${currentUser.id}&first_name=${encodeURIComponent(currentUser.first_name)}&username=${encodeURIComponent(currentUser.username)}`);
    if (res.ok) {
      const data = await res.json();
      currentUser = {
        ...currentUser,
        is_vip: data.is_vip || false,
        vip_until: data.vip_until || null,
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

// 2. 1200 ta rasmiy savollarni yuklash
async function loadQuestions() {
  try {
    const res = await fetch('/api/questions');
    if (res.ok) {
      const data = await res.json();
      if (data.bilets && data.questions) {
        allBilets = data.bilets;
        allQuestions = data.questions;
      } else if (Array.isArray(data)) {
        allQuestions = data;
      }
      renderTickets();
    }
  } catch (e) {
    console.error("Questions load error:", e);
  }
}

// 3. Header panelini yangilash
function updateHeaderUI() {
  document.getElementById('user-name').innerText = currentUser.first_name;
  
  const badge = document.getElementById('user-badge');
  if (currentUser.is_vip) {
    badge.innerText = "👑 VIP (Barcha biletlar ochiq)";
    badge.style.background = "#fef3c7";
    badge.style.color = "#b45309";
  } else {
    const count = currentUser.unlocked_tickets ? currentUser.unlocked_tickets.length : 3;
    badge.innerText = `🟢 ${count} ta bilet ochiq`;
    badge.style.background = "#d1fae5";
    badge.style.color = "#065f46";
  }

  // Referral UI
  document.getElementById('ref-unlocked-count').innerText = currentUser.unlocked_tickets ? currentUser.unlocked_tickets.length : 3;
  document.getElementById('ref-vip-status').innerText = currentUser.is_vip ? "👑 VIP Faol" : "Oddiy";
  
  const botUser = "prava_test_AI_bot";
  const refLink = `https://t.me/${botUser}?start=ref_${currentUser.id}`;
  document.getElementById('ref-link-input').value = refLink;
}

// 4. Biletlar ro'yxatini chiqarish
function renderTickets() {
  const container = document.getElementById('tickets-grid');
  if (!container) return;
  container.innerHTML = '';

  const totalCount = allBilets.length > 0 ? allBilets.length : (currentUser.total_tickets || 60);
  document.getElementById('tickets-title').innerText = `📚 Biletlar (1 – ${totalCount})`;

  for (let i = 1; i <= totalCount; i++) {
    // Ruxsat tekshiruvi: VIP bo'lsa yoki unlocked_tickets ro'yxatida bo'lsa
    const isUnlocked = currentUser.is_vip || (currentUser.unlocked_tickets && currentUser.unlocked_tickets.includes(i));
    const card = document.createElement('div');
    card.className = `ticket-card ${isUnlocked ? 'unlocked' : 'locked'}`;

    let badgeClass = 'locked-badge';
    let badgeText = '🔒 QULFLANGAN';

    if (isUnlocked) {
      if (i <= 3) {
        badgeClass = 'free';
        badgeText = 'BEPUL';
      } else {
        badgeClass = 'passed';
        badgeText = 'OCHILGAN';
      }
    }

    card.innerHTML = `
      <div class="ticket-top">
        <span class="ticket-num">${i}-Bilet</span>
        <span class="ticket-status-icon">${isUnlocked ? '🟢' : '🔒'}</span>
      </div>
      <div class="ticket-desc">20 ta savol • 20 daqiqa</div>
      <span class="ticket-badge ${badgeClass}">${badgeText}</span>
    `;

    card.onclick = () => {
      if (isUnlocked) {
        startQuizForTicket(i);
      } else {
        openPaymentModal('vip_90', `👑 ${i}-Bilet va Barcha Biletlar (VIP)`, '30 000');
      }
    };

    container.appendChild(card);
  }
}

// 5. Muayyan bilet bo'yicha testni boshlash
function startQuizForTicket(ticketNumber) {
  const ticketQuestions = allQuestions.filter(q => (q.biletNumber === ticketNumber || q.ticket_id === ticketNumber));
  if (!ticketQuestions.length) {
    alert("Ushbu bilet savollari yuklanmoqda...");
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

// 6. Tasodifiy 20 talik Davlat Imtihoni rejimi
function startExamMode() {
  if (!allQuestions.length) {
    alert("Savollar bazasi yuklanmoqda...");
    return;
  }
  // Barcha savollardan 20 tasini tasodifiy olish
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

// 7. Savolni ekranga chiqarish (Haqiqiy rasm va variantlar)
function renderCurrentQuestion() {
  const q = currentQuiz.questions[currentQuiz.currentIndex];
  if (!q) return;

  document.getElementById('quiz-counter').innerText = `${currentQuiz.currentIndex + 1} / ${currentQuiz.questions.length}`;
  const pct = ((currentQuiz.currentIndex + 1) / currentQuiz.questions.length) * 100;
  document.getElementById('progress-fill').style.width = `${pct}%`;

  // Haqiqiy imtihon rasmini yuklash
  const mediaContainer = document.getElementById('question-media');
  const imgUrl = q.imageUrl || (q.image ? `/media/${q.image}` : null);

  if (imgUrl) {
    mediaContainer.style.display = 'flex';
    mediaContainer.innerHTML = `<img src="${imgUrl}" class="question-img" alt="Yo'l harakati holati" onerror="this.onerror=null; this.parentElement.style.display='none';" />`;
  } else {
    mediaContainer.style.display = 'none';
    mediaContainer.innerHTML = '';
  }

  // Savol matni
  document.getElementById('question-text').innerText = q.text || q.question;

  // Variantlar ro'yxati
  const list = document.getElementById('options-list');
  list.innerHTML = '';

  const letters = ['A', 'B', 'C', 'D'];
  const hasAnswered = currentQuiz.answers[q.id] !== undefined;
  const correctIdx = (q.correctOptionIndex !== undefined) ? q.correctOptionIndex : q.correct;

  const options = q.options || [];
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

  // AI va YHQ Qoidasi tushuntirish qutisi
  const aiBox = document.getElementById('ai-box');
  if (hasAnswered && q.explanation) {
    document.getElementById('ai-text').innerText = q.explanation;
    aiBox.style.display = 'block';
  } else {
    aiBox.style.display = 'none';
  }

  // Oldingi / Keyingi tugmalari
  document.getElementById('prev-btn').disabled = currentQuiz.currentIndex === 0;
  document.getElementById('next-btn').innerText = (currentQuiz.currentIndex === currentQuiz.questions.length - 1) ? 'Yakunlash 🏁' : 'Keyingisi ➡';
}

// 8. Variant tanlanganda
function selectOption(selectedIdx) {
  const q = currentQuiz.questions[currentQuiz.currentIndex];
  currentQuiz.answers[q.id] = selectedIdx;

  const correctIdx = (q.correctOptionIndex !== undefined) ? q.correctOptionIndex : q.correct;
  const isCorrect = (selectedIdx === correctIdx);

  // Xatolar tahlili uchun serverga yuborish
  fetch('/api/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUser.id,
      question_id: q.id,
      is_correct: isCorrect
    })
  }).catch(e => console.warn("API answer error:", e));

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

// 9. Testni yakunlash va natija
function finishQuiz() {
  clearInterval(currentQuiz.timerInterval);

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
  document.getElementById('result-status').innerText = passed ? "Imtihondan o'tdingiz!" : "Yana tayyorgarlik ko'ring";
  document.getElementById('result-msg').innerText = passed 
    ? "Ajoyib natija! Siz haqiqiy Davlat YHQ nazariy imtihoniga to'liq tayyorsiz." 
    : "Davlat imtihonidan o'tish uchun kamida 18 ta to'g'ri javob talab etiladi. Xatolar ustida ishlang!";

  // Test natijasini bazaga yozish
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
    }).catch(e => console.warn("Result save error:", e));
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

// 10. Taymer
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

// 11. Xatolar ustida ishlash
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
      <h4>${idx + 1}. ${q.text || q.question}</h4>
      <p>💡 <b>YHQ Qoidasi:</b> ${q.explanation || "Yo'l harakati qoidasini ko'rib chiqing."}</p>
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

// 12. Sahifalar almashinuvi
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

// 13. To'lov modali
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

// 14. Referal havolasini ulashish
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

// 15. Dastur yuklanishi
window.onload = async () => {
  await loadUserData();
  await loadQuestions();
};
