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
  total_tickets: 60
};

let globalQuizTimer = null;
let allBilets = [];
let allQuestions = [];
let selectedPickerTickets = new Set();

let currentQuiz = {
  mode: 'ticket', // 'ticket' | 'exam' | 'mistakes' | 'smart'
  ticketId: 1,
  questions: [],
  currentIndex: 0,
  answers: {},
  timeLeft: 20 * 60
};

let userMistakes = [];

// Til lug'ati (Translations)
const T = {
  uz: {
    btn_contact: "📞 Aloqa",
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
    loading: "Yuklanmoqda...",

    // Mistakes View
    mistakes_title: "🧠 Xatolar ustida ishlash (AI)",
    mistakes_desc: "Noto'g'ri yechilgan savollaringiz to'g'ri javob berguningizcha saqlanadi.",
    mistakes_count_label: "ta xato",
    mistakes_empty_title: "Hozircha xatoliklar yo'q!",
    mistakes_empty_desc: "Biletlarni yechib, bilimingizni sinab ko'ring.",
    mistakes_empty_btn: "Biletlarga o'tish",
    mistakes_solve_btn: "🔁 Faqat xatolarni qayta ishlash",

    // Referral View
    ref_title: "Do'stlarni taklif qiling!",
    ref_desc: "Har bir taklif qilingan do'stingiz uchun <b>navbatdagi 1 ta bilet bepul</b> va doimiy ochiladi.",
    ref_lbl_tickets: "Ochiq biletlar",
    ref_lbl_vip: "Obuna holati",
    ref_copy_btn: "Nusxalash",
    ref_share_btn: "📲 Telegram'da do'stlarga ulashish",
    ref_copy_alert: "Referral havolangiz nusxalandi! Do'stlaringizga yuboring.",
    ref_share_text: "🚗 Haydovchilik guvohnomasi (Prava) imtihoniga tayyorgarlik ko'rish uchun rasmiy test boti! Sinab ko'ring:",

    // Buy View
    buy_title: "💎 Tariflar va Xarid",
    buy_desc: "Kerakli xizmatni tanlang va to'lov qiling:",
    tarif1_title: "📚 Ixtiyoriy 3 ta bilet",
    tarif1_desc: "O'zingiz xohlagan 3 ta bilet (90 kun muddatga)",
    tarif1_price: "5 000 so'm",
    tarif1_btn: "Tanlash",
    tarif2_title: "🎟 1 martalik Imtihon",
    tarif2_desc: "1 marta 20 talik Davlat imtihoni topshirish",
    tarif2_price: "2 000 so'm",
    tarif2_btn: "Xarid",
    tarif3_title: "⚡ 30 kunlik Cheksiz Imtihon",
    tarif3_desc: "30 kun davomida istalgancha 20 talik test yechish",
    tarif3_price: "15 000 so'm",
    tarif3_btn: "Xarid",
    tarif4_badge: "To'liq to'plam",
    tarif4_title: "👑 VIP To'liq Kirish (90 kun)",
    tarif4_desc: "Barcha 60 ta bilet (1200 ta savol) + cheksiz 20 talik imtihonlar",
    tarif4_price: "30 000 so'm",
    tarif4_btn: "Xarid",

    // Picker Modal
    picker_modal_title: "📚 3 ta bilet tanlang",
    picker_modal_desc: "O'zingiz xohlagan <b>3 ta biletni</b> belgilang (90 kunga ochiladi):",
    picker_status: "ta bilet tanlandi",
    picker_confirm_btn: "Tanlangan biletlarni sotib olish (5 000 so'm)",
    picker_max_alert: "Siz ko'pi bilan 3 ta bilet tanlashingiz mumkin!",
    picker_chip_open: "Ochiq",

    // Exam Modal
    exam_modal_title: "⚡ Imtihon topshirish",
    exam_modal_desc: "20 talik Davlat imtihoni simulyatorini topshirish uchun quyidagi qulay variantlardan birini tanlang:",
    exam_m1_title: "🎟 1 martalik Imtihon",
    exam_m1_desc: "Bitta to'liq 20 talik sinov",
    exam_m2_title: "⚡ 30 kunlik Cheksiz",
    exam_m2_desc: "30 kun xohlagancha topshirish",
    exam_m3_badge: "Tavsiya",
    exam_m3_title: "👑 VIP To'liq Kirish",
    exam_m3_desc: "Hamma biletlar + cheksiz imtihon",
    exam_btn_select: "Tanlash",

    // Payment Modal
    pay_title: "To'lov ma'lumotlari",
    pay_card_label: "Karta raqam (UzCard / Humo):",
    pay_copy_btn: "Nusxalash",
    pay_holder: "Egasi: <b>K.E.</b>",
    pay_step1: "1. Kartaga <b id=\"modal-instruct-amount\">to'lov</b> o'tkazing.",
    pay_step2: "2. To'lov cheki skrinshotini botga rasm qilib yuboring.",
    pay_step3: "3. Administrator tasdiqlashi bilan xizmatingiz darhol ochiladi!",
    pay_submit_btn: "📸 Chekni botga yuborish",
    pay_card_alert: "Karta raqami nusxalandi!"
  },
  ru: {
    btn_contact: "📞 Связь",
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
    loading: "Загрузка...",

    // Mistakes View
    mistakes_title: "🧠 Работа над ошибками (AI)",
    mistakes_desc: "Вопросы, в которых вы ошиблись, сохраняются, пока вы не ответите правильно.",
    mistakes_count_label: "ошибок",
    mistakes_empty_title: "Ошибок пока нет!",
    mistakes_empty_desc: "Решайте билеты и проверяйте свои знания.",
    mistakes_empty_btn: "К билетам",
    mistakes_solve_btn: "🔁 Решать только ошибки",

    // Referral View
    ref_title: "Приглашайте друзей!",
    ref_desc: "За каждого приглашенного друга вам открывается <b>1 билет бесплатно</b> навсегда.",
    ref_lbl_tickets: "Открыто билетов",
    ref_lbl_vip: "Статус подписки",
    ref_copy_btn: "Копировать",
    ref_share_btn: "📲 Поделиться с друзьями в Telegram",
    ref_copy_alert: "Реферальная ссылка скопирована! Отправьте её друзьям.",
    ref_share_text: "🚗 Официальный бот для подготовки к экзамену по ПДД (Права)! Попробуйте:",

    // Buy View
    buy_title: "💎 Тарифы и покупка",
    buy_desc: "Выберите нужный тариф и оплатите:",
    tarif1_title: "📚 Любые 3 билета",
    tarif1_desc: "Любые 3 билета на ваш выбор (на 90 дней)",
    tarif1_price: "5 000 сум",
    tarif1_btn: "Выбрать",
    tarif2_title: "🎟 1 разовый экзамен",
    tarif2_desc: "1 прохождение официального экзамена (20 вопросов)",
    tarif2_price: "2 000 сум",
    tarif2_btn: "Купить",
    tarif3_title: "⚡ Безлимитный экзамен на 30 дней",
    tarif3_desc: "Сдавайте сколько угодно тестов в течение 30 дней",
    tarif3_price: "15 000 сум",
    tarif3_btn: "Купить",
    tarif4_badge: "Все включено",
    tarif4_title: "👑 VIP Полный доступ (90 дней)",
    tarif4_desc: "Все 60 билетов (1200 вопросов) + безлимитные экзамены",
    tarif4_price: "30 000 сум",
    tarif4_btn: "Купить",

    // Picker Modal
    picker_modal_title: "📚 Выберите 3 билета",
    picker_modal_desc: "Выберите любые <b>3 билета</b> (открываются на 90 дней):",
    picker_status: "билета выбрано",
    picker_confirm_btn: "Купить выбранные билеты (5 000 сум)",
    picker_max_alert: "Вы можете выбрать максимум 3 билета!",
    picker_chip_open: "Открыто",

    // Exam Modal
    exam_modal_title: "⚡ Сдача экзамена",
    exam_modal_desc: "Для прохождения официального 20-вопросного экзамена выберите тариф:",
    exam_m1_title: "🎟 1 разовый экзамен",
    exam_m1_desc: "Один полный тест из 20 вопросов",
    exam_m2_title: "⚡ 30 дней безлимит",
    exam_m2_desc: "30 дней без ограничений",
    exam_m3_badge: "Рекомендуем",
    exam_m3_title: "👑 VIP Полный доступ",
    exam_m3_desc: "Все билеты + безлимитные экзамены",
    exam_btn_select: "Выбрать",

    // Payment Modal
    pay_title: "Реквизиты для оплаты",
    pay_card_label: "Номер карты (UzCard / Humo):",
    pay_copy_btn: "Копировать",
    pay_holder: "Владелец: <b>K.E.</b>",
    pay_step1: "1. Переведите <b id=\"modal-instruct-amount\">сумму</b> на карту.",
    pay_step2: "2. Отправьте скриншот чека в бот.",
    pay_step3: "3. Администратор подтвердит и услуга откроется моментально!",
    pay_submit_btn: "📸 Отправить чек в бот",
    pay_card_alert: "Номер карты скопирован!"
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
  renderAiProgressCard();

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
  const setHTML = (id, html) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  };

  setText('btn-contact', t.btn_contact);
  setText('tickets-title', `${t.tickets_title} (1 – ${allBilets.length || 60})`);
  setText('tickets-info-tag', t.tickets_free_tag);
  setText('hero-title', t.hero_title);
  setText('hero-desc', t.hero_desc);
  setText('hero-btn', t.hero_btn);

  // Bottom Nav
  const navT = document.querySelector('#nav-tickets .nav-label');
  if (navT) navT.innerText = t.nav_tickets;
  const navM = document.querySelector('#nav-mistakes .nav-label');
  if (navM) navM.innerText = t.nav_mistakes;
  const navR = document.querySelector('#nav-referral .nav-label');
  if (navR) navR.innerText = t.nav_referral;
  const navB = document.querySelector('#nav-buy .nav-label');
  if (navB) navB.innerText = t.nav_vip;

  // Quiz buttons
  setText('quiz-back-btn', t.btn_back);
  setText('prev-btn', t.btn_prev);
  const nextBtn = document.getElementById('next-btn');
  if (nextBtn && currentQuiz.questions && currentQuiz.questions.length > 0) {
    nextBtn.innerText = (currentQuiz.currentIndex === currentQuiz.questions.length - 1) ? t.btn_finish : t.btn_next;
  }

  // Result actions
  setText('result-retry-btn', t.result_retry);
  setText('result-mistakes-btn', t.result_mistakes);
  setText('result-home-btn', t.result_home);

  // Mistakes View
  setText('mistakes-title', t.mistakes_title);
  setText('mistakes-desc', t.mistakes_desc);
  setText('mistakes-empty-title', t.mistakes_empty_title);
  setText('mistakes-empty-desc', t.mistakes_empty_desc);
  setText('mistakes-empty-btn', t.mistakes_empty_btn);
  setText('solve-mistakes-btn', t.mistakes_solve_btn);
  const countSpan = document.getElementById('mistakes-count');
  if (countSpan) countSpan.innerText = `${userMistakes.length} ${t.mistakes_count_label}`;

  // Referral View
  setText('ref-title', t.ref_title);
  setHTML('ref-desc', t.ref_desc);
  setText('ref-lbl-tickets', t.ref_lbl_tickets);
  setText('ref-lbl-vip', t.ref_lbl_vip);
  setText('ref-copy-btn', t.ref_copy_btn);
  setText('ref-share-btn', t.ref_share_btn);

  // Buy View
  setText('buy-title', t.buy_title);
  setText('buy-desc', t.buy_desc);
  setText('tarif1-title', t.tarif1_title);
  setText('tarif1-desc', t.tarif1_desc);
  setText('tarif1-price', t.tarif1_price);
  setText('tarif1-btn', t.tarif1_btn);
  setText('tarif2-title', t.tarif2_title);
  setText('tarif2-desc', t.tarif2_desc);
  setText('tarif2-price', t.tarif2_price);
  setText('tarif2-btn', t.tarif2_btn);
  setText('tarif3-title', t.tarif3_title);
  setText('tarif3-desc', t.tarif3_desc);
  setText('tarif3-price', t.tarif3_price);
  setText('tarif3-btn', t.tarif3_btn);
  setText('tarif4-badge', t.tarif4_badge);
  setText('tarif4-title', t.tarif4_title);
  setText('tarif4-desc', t.tarif4_desc);
  setText('tarif4-price', t.tarif4_price);
  setText('tarif4-btn', t.tarif4_btn);

  // Modals
  setText('picker-modal-title', t.picker_modal_title);
  setHTML('picker-modal-desc', t.picker_modal_desc);
  setText('picker-modal-price', t.tarif1_price);
  setText('exam-modal-title', t.exam_modal_title);
  setText('exam-modal-desc', t.exam_modal_desc);
  setText('exam-m1-title', t.exam_m1_title);
  setText('exam-m1-desc', t.exam_m1_desc);
  setText('exam-m1-btn', t.exam_btn_select);
  setText('exam-m2-title', t.exam_m2_title);
  setText('exam-m2-desc', t.exam_m2_desc);
  setText('exam-m2-btn', t.exam_btn_select);
  setText('exam-m3-badge', t.exam_m3_badge);
  setText('exam-m3-title', t.exam_m3_title);
  setText('exam-m3-desc', t.exam_m3_desc);
  setText('exam-m3-btn', t.exam_btn_select);

  setText('pay-card-label', t.pay_card_label);
  setText('pay-copy-btn', t.pay_copy_btn);
  setHTML('pay-card-holder', t.pay_holder);
  setHTML('pay-step-1', t.pay_step1);
  setText('pay-step-2', t.pay_step2);
  setText('pay-step-3', t.pay_step3);
  setText('pay-submit-btn', t.pay_submit_btn);
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
        total_tickets: data.total_tickets || 60,
        progress: data.progress || null
      };
      updateHeaderUI();
      renderTickets();
      renderAiProgressCard();
      loadMistakes();
    }
  } catch (e) {
    console.error("User data load error:", e);
    renderTickets();
  }
}

// 2. Savollarni yuklash
let questionsLoadingPromise = null;

function loadQuestions() {
  if (!questionsLoadingPromise) {
    questionsLoadingPromise = fetch('/api/questions')
      .then(res => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          allQuestions = data;
          const bNums = [...new Set(allQuestions.map(q => q.biletNumber || q.ticket_id || 1))].sort((a,b) => a - b);
          allBilets = bNums.map(n => ({ number: n, title: (currentLang === 'ru') ? `Билет ${n}` : `${n}-Bilet` }));
        } else if (data && data.questions) {
          allQuestions = data.questions;
          allBilets = data.bilets || [];
        }
        applyLanguageTexts();
        renderTickets();
        return allQuestions;
      })
      .catch(e => {
        console.error("Questions load error:", e);
        questionsLoadingPromise = null;
        return [];
      });
  }
  return questionsLoadingPromise;
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
  const totalCount = allBilets.length > 0 ? allBilets.length : (currentUser.total_tickets || 60);
  
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
        <span class="ticket-num">${(currentLang === 'ru') ? `Билет ${i}` : `${i}-Bilet`}</span>
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
async function startQuizForTicket(ticketNumber) {
  if (!allQuestions || allQuestions.length === 0) {
    if (questionsLoadingPromise) {
      await questionsLoadingPromise;
    } else {
      await loadQuestions();
    }
  }

  const ticketQuestions = allQuestions.filter(q => (q.biletNumber === ticketNumber || q.ticket_id === ticketNumber));
  if (!ticketQuestions.length) {
    alert(T[currentLang].loading);
    return;
  }

  stopQuizTimer();
  currentQuiz = {
    mode: 'ticket',
    ticketId: ticketNumber,
    questions: ticketQuestions,
    currentIndex: 0,
    answers: {},
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

async function startExamMode() {
  if (!allQuestions || allQuestions.length === 0) {
    if (questionsLoadingPromise) {
      await questionsLoadingPromise;
    } else {
      await loadQuestions();
    }
  }
  if (!allQuestions.length) {
    alert(T[currentLang].loading);
    return;
  }
  const shuffled = [...allQuestions].sort(() => 0.5 - Math.random()).slice(0, 20);

  stopQuizTimer();
  currentQuiz = {
    mode: 'exam',
    ticketId: 0,
    questions: shuffled,
    currentIndex: 0,
    answers: {},
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
  })
  .then(res => res.json())
  .then(data => {
    if (data && data.progress) {
      currentUser.progress = data.progress;
      renderAiProgressCard();
    }
  })
  .catch(e => console.warn(e));

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
  stopQuizTimer();
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
  stopQuizTimer();
  currentQuiz.currentIndex = 0;
  currentQuiz.answers = {};
  showView('quiz');
  renderCurrentQuestion();
  startTimer();
}

function exitQuiz() {
  stopQuizTimer();
  showView('tickets');
}

function stopQuizTimer() {
  if (globalQuizTimer) {
    clearInterval(globalQuizTimer);
    globalQuizTimer = null;
  }
}

function startTimer() {
  stopQuizTimer();
  currentQuiz.timeLeft = 20 * 60;

  const updateDisplay = () => {
    const mins = Math.floor(currentQuiz.timeLeft / 60);
    const secs = currentQuiz.timeLeft % 60;
    const el = document.getElementById('quiz-timer');
    if (el) {
      el.innerText = `⏱ ${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }
  };

  updateDisplay();

  globalQuizTimer = setInterval(() => {
    currentQuiz.timeLeft--;
    if (currentQuiz.timeLeft <= 0) {
      stopQuizTimer();
      finishQuiz();
      return;
    }
    updateDisplay();
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
  stopQuizTimer();
  currentQuiz = {
    mode: 'mistakes',
    ticketId: 0,
    questions: userMistakes,
    currentIndex: 0,
    answers: {},
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
  stopQuizTimer();
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

  const totalCount = allBilets.length > 0 ? allBilets.length : (currentUser.total_tickets || 60);

  for (let i = 4; i <= totalCount; i++) {
    const isAlreadyUnlocked = currentUser.unlocked_tickets && currentUser.unlocked_tickets.includes(i);
    const chip = document.createElement('div');
    chip.className = 'picker-chip';
    chip.innerText = (currentLang === 'ru') ? `Билет ${i}` : `${i}-Bilet`;

    if (isAlreadyUnlocked) {
      chip.classList.add('disabled');
      chip.title = (currentLang === 'ru') ? "Открыт" : "Ochiq";
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
            alert(T[currentLang].picker_max_alert);
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

  const t = T[currentLang];
  if (statusEl) {
    statusEl.innerText = `${count} / 3 ${t.picker_status}`;
  }
  if (confirmBtn) {
    confirmBtn.disabled = (count === 0);
    confirmBtn.innerText = t.picker_confirm_btn;
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
  const title = (currentLang === 'ru') ? `📚 Выбранные билеты: ${ticketsStr}` : `📚 Tanlangan biletlar: ${ticketsStr}`;
  openPaymentModal(
    'tickets_3',
    title,
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
  const currency = (currentLang === 'ru') ? 'сум' : "so'm";
  document.getElementById('modal-title').innerText = title;
  document.getElementById('modal-price').innerText = `${price} ${currency}`;
  document.getElementById('modal-instruct-amount').innerText = `${price} ${currency}`;
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
  alert(T[currentLang].pay_card_alert);
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
  alert(T[currentLang].ref_copy_alert);
}

function shareRefLink() {
  const link = document.getElementById('ref-link-input').value;
  const text = encodeURIComponent(T[currentLang].ref_share_text);
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${text}`;
  if (tg) {
    tg.openTelegramLink(shareUrl);
  } else {
    window.open(shareUrl, '_blank');
  }
}

// 16. AI Tayyorgarlik va Natijalarni ko'rsatish
function renderAiProgressCard() {
  const p = currentUser.progress || {
    percent: 0,
    learned_count: 0,
    total_questions: allQuestions.length || 679,
    mistakes_count: 0,
    pass_prob: 15,
    level_uz: "Boshlang'ich",
    level_ru: "Начинающий",
    level_badge: "🔴"
  };

  const isRu = currentLang === 'ru';
  const levelText = isRu ? (p.level_ru || "Начинающий") : (p.level_uz || "Boshlang'ich");
  
  const badgeEl = document.getElementById('ai-level-badge');
  if (badgeEl) badgeEl.innerText = `${p.level_badge || '🟡'} ${levelText}`;

  const predEl = document.getElementById('ai-prediction-tag');
  if (predEl) predEl.innerText = isRu ? `🔮 Шанс сдачи: ${p.pass_prob || 15}%` : `🔮 O'tish ehtimoli: ${p.pass_prob || 15}%`;

  const pctValEl = document.getElementById('ai-percent-val');
  if (pctValEl) pctValEl.innerText = `${p.percent || 0}%`;

  const fillEl = document.getElementById('ai-bar-fill');
  if (fillEl) fillEl.style.width = `${Math.min(100, Math.max(0, p.percent || 0))}%`;

  const total = p.total_questions || (allQuestions.length || 679);
  const learnedEl = document.getElementById('ai-learned-text');
  if (learnedEl) {
    learnedEl.innerText = isRu ? `📚 ${p.learned_count || 0} / ${total} усвоено` : `📚 ${p.learned_count || 0} / ${total} o'rganildi`;
  }

  const mistakesEl = document.getElementById('ai-mistakes-text');
  if (mistakesEl) {
    mistakesEl.innerText = isRu ? `❌ ${p.mistakes_count || 0} ошибок` : `❌ ${p.mistakes_count || 0} ta xato`;
  }

  const btnTitle = document.getElementById('ai-btn-title');
  if (btnTitle) btnTitle.innerText = isRu ? "🧠 AI Умная тренировка" : "🧠 AI Aqlli Mashg'ulot";

  const btnSub = document.getElementById('ai-btn-sub');
  if (btnSub) btnSub.innerText = isRu ? "Слабые темы и новые вопросы (20 шт)" : "Zaif mavzular va yangi savollar (20 ta)";

  const pctTitle = document.getElementById('ai-percent-title');
  if (pctTitle) pctTitle.innerText = isRu ? "Готовность" : "Tayyorgarlik";
}

async function startAiSmartQuiz() {
  try {
    const res = await fetch(`/api/ai_smart_test?user_id=${currentUser.id}`);
    if (res.ok) {
      const questions = await res.json();
      if (questions && questions.length > 0) {
        stopQuizTimer();
        currentQuiz = {
          mode: 'smart',
          ticketId: 'ai_smart',
          questions: questions,
          currentIndex: 0,
          answers: {},
          timeLeft: 20 * 60
        };
        showView('quiz');
        renderCurrentQuestion();
        startTimer();
        return;
      }
    }
  } catch (e) {
    console.warn("AI Smart test fetch error:", e);
  }
  handleStartExamClick();
}

// 17. Yuklanish va Ishga tushirish
function initApp() {
  setLanguage(currentLang);
  loadUserData();
  loadQuestions();
  renderAiProgressCard();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

window.addEventListener('load', () => {
  if (!allQuestions || allQuestions.length === 0) {
    loadQuestions();
  }
});
