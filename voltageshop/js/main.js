/* ============================================================
   Eufy HomeCare・智家看护 — Motion Engine
   GSAP + ScrollTrigger + Lenis
   ============================================================ */
gsap.registerPlugin(ScrollTrigger);

const isTouch = window.matchMedia('(hover:none)').matches;
const $  = (s, c = document) => c.querySelector(s);
const $$ = (s, c = document) => [...c.querySelectorAll(s)];

/* ------------------------------------------------------------
   1. Smooth scroll (Lenis)
------------------------------------------------------------ */
const lenis = new Lenis({ duration: 1.15, lerp: 0.09 });
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add((time) => lenis.raf(time * 1000));
gsap.ticker.lagSmoothing(0);

/* anchor links → lenis */
$$('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    const id = a.getAttribute('href');
    if (id.length > 1 && $(id)) { e.preventDefault(); lenis.scrollTo(id, { offset: -80 }); }
  });
});

/* ------------------------------------------------------------
   2. Preloader
------------------------------------------------------------ */
const preloader = $('#preloader');
const countEl = $('#loadCount');
const barEl = $('#loadBar');
let progress = 0;

const loadTimer = setInterval(() => {
  progress += Math.floor(Math.random() * 9) + 3;
  if (progress >= 100) { progress = 100; clearInterval(loadTimer); finishLoad(); }
  countEl.textContent = progress;
  gsap.to(barEl, { scaleX: progress / 100, duration: .3, ease: 'power2.out' });
}, 90);

function finishLoad() {
  gsap.timeline({ delay: .35 })
    .to('.preloader__inner', { y: -40, opacity: 0, duration: .6, ease: 'power3.in' })
    .to(preloader, { yPercent: -100, duration: .9, ease: 'power4.inOut' }, '-=.15')
    .set(preloader, { display: 'none' })
    .add(heroIntro, '-=.55');
}

/* 安全兜底：万一 setInterval 被极端环境（后台冻结 / bfcache 恢复 / 嵌入式浏览器）
   挂起，rAF 计时超过 6 秒强制结束 preloader，页面不会永久卡死 */
const safetyWatch = function () {
  if (preloader.style.display === 'none') { gsap.ticker.remove(safetyWatch); return; }
  safetyWatch.elapsed = (safetyWatch.elapsed || 0) + gsap.ticker.deltaMS;
  if (safetyWatch.elapsed > 6000) {
    clearInterval(loadTimer);
    progress = 100;
    finishLoad();
  }
};
gsap.ticker.add(safetyWatch);

/* ------------------------------------------------------------
   3. Custom cursor
------------------------------------------------------------ */
const dot = $('#cursorDot');
const ring = $('#cursorRing');
const mouse = { x: innerWidth / 2, y: innerHeight / 2 };
const ringPos = { x: mouse.x, y: mouse.y };

addEventListener('mousemove', (e) => {
  mouse.x = e.clientX; mouse.y = e.clientY;
  gsap.set(dot, { x: mouse.x, y: mouse.y });
});
gsap.ticker.add(() => {
  ringPos.x += (mouse.x - ringPos.x) * 0.16;
  ringPos.y += (mouse.y - ringPos.y) * 0.16;
  gsap.set(ring, { x: ringPos.x, y: ringPos.y });
});

document.addEventListener('mouseover', (e) => {
  const t = e.target.closest('[data-cursor]');
  if (!t) return;
  ring.classList.add(t.dataset.cursor === 'text' ? 'is-text' : 'is-hover');
});
document.addEventListener('mouseout', (e) => {
  if (e.target.closest('[data-cursor]')) ring.classList.remove('is-hover', 'is-text');
});

/* ------------------------------------------------------------
   4. Hero intro choreography
------------------------------------------------------------ */
function splitChars(el) {
  const text = el.textContent;
  el.textContent = '';
  text.split('').forEach(ch => {
    const span = document.createElement('span');
    span.className = 'char';
    span.textContent = ch === ' ' ? '\u00A0' : ch;
    el.appendChild(span);
  });
}
$$('[data-split]').forEach(el => {
  el.dataset.splitText = el.textContent;
  splitChars(el);
});

function heroIntro() {
  // 非首页（产品详情 / AI 升级页等）没有 Hero 轮播，
  // 仅淡入顶部导航即可，避免 GSAP 输出大量“选择器未找到”警告。
  if (!$('.hero__stage')) {
    gsap.timeline({ defaults: { ease: 'power4.out' } })
      .from('.header__inner', { y: -30, opacity: 0, duration: .8 });
    return;
  }
  const tl = gsap.timeline({ defaults: { ease: 'power4.out' } });
  tl.from('.hero__stage', { opacity: 0, duration: 1.2, ease: 'power2.out' })
    .from('.hero__slide.is-active img', { scale: 1.18, duration: 2, ease: 'power2.out' }, '-=1.2')
    .from('.hero__pill', { y: 26, opacity: 0, duration: .8 }, '-=.6')
    .from('.hero__title .line', { y: 130, duration: 1.1 }, '-=.55')
    .from('.hero__arrow--prev', { x: -20, opacity: 0, duration: .5 }, '-=.8')
    .from('.hero__arrow--next', { x: 20, opacity: 0, duration: .5 }, '<')
    .from('.hero__dot', { scale: 0, opacity: 0, stagger: .06, duration: .4 }, '-=.4')
    .from('.header__inner', { y: -30, opacity: 0, duration: .8 }, '-=1.1')
    .from('.brands__track span', { opacity: 0, y: 14, stagger: .05, duration: .5 }, '-=.5')
    .call(initHeroCarousel);
}

/* ===== Hero carousel ===== */
function initHeroCarousel() {
  const slides = $$('.hero__slide');
  const dotsWrap = $('#heroDots');
  const progressSpan = $('#heroProgress');
  const prevBtn = $('#heroPrev');
  const nextBtn = $('#heroNext');
  if (!slides.length) return;

  let current = 0;
  let autoplayTimer = null;
  let progressRAF = null;
  const DURATION = 5000;
  let progressStart = 0;

  // 生成指示点
  dotsWrap.innerHTML = slides.map((_, i) => `<button class="hero__dot${i === 0 ? ' is-active' : ''}" data-idx="${i}" aria-label="第 ${i + 1} 张"></button>`).join('');
  const dots = $$('.hero__dot', dotsWrap);

  function goTo(idx) {
    if (idx < 0) idx = slides.length - 1;
    if (idx >= slides.length) idx = 0;
    if (idx === current) return;

    // 纯 CSS 切换：旧 slide 移除 is-active，新 slide 添加
    slides[current].classList.remove('is-active');
    slides[idx].classList.add('is-active');

    // 指示点
    dots[current].classList.remove('is-active');
    dots[idx].classList.add('is-active');

    current = idx;
    restartAutoplay();
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  // 进度条
  function tickProgress(now) {
    if (!progressStart) progressStart = now;
    const elapsed = now - progressStart;
    const p = Math.min(elapsed / DURATION, 1);
    progressSpan.style.width = (p * 100) + '%';
    if (p < 1) {
      progressRAF = requestAnimationFrame(tickProgress);
    }
  }
  function startProgress() {
    progressStart = 0;
    cancelAnimationFrame(progressRAF);
    progressRAF = requestAnimationFrame(tickProgress);
  }
  function restartAutoplay() {
    clearTimeout(autoplayTimer);
    startProgress();
    autoplayTimer = setTimeout(next, DURATION);
  }

  prevBtn.addEventListener('click', prev);
  nextBtn.addEventListener('click', next);
  dots.forEach((d, i) => d.addEventListener('click', () => goTo(i)));

  // 鼠标悬停暂停
  const stage = $('#heroStage');
  stage.addEventListener('mouseenter', () => {
    clearTimeout(autoplayTimer);
    cancelAnimationFrame(progressRAF);
  });
  stage.addEventListener('mouseleave', restartAutoplay);

  // 键盘左右键
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') prev();
    if (e.key === 'ArrowRight') next();
  });

  restartAutoplay();
}

/* ------------------------------------------------------------
   5. Header behaviour + scroll progress
------------------------------------------------------------ */
const header = $('#header');
let lastY = 0;
lenis.on('scroll', ({ scroll }) => {
  header.classList.toggle('is-scrolled', scroll > 30);
  if (scroll > lastY && scroll > 240) header.classList.add('is-hidden');
  else header.classList.remove('is-hidden');
  lastY = scroll;
});

/* ------------------------------------------------------------
   6. Scroll reveals
------------------------------------------------------------ */
/* generic fade-up */
$$('[data-reveal]').forEach((el, i) => {
  const delay = (i % 5) * 0.07;
  gsap.fromTo(el,
    { y: 60, opacity: 0 },
    {
      y: 0, opacity: 1, duration: 1, delay, ease: 'power3.out',
      scrollTrigger: { trigger: el, start: 'top 88%', once: true }
    });
});

/* image clip reveal */
$$('[data-reveal-img]').forEach(fig => {
  const img = fig.querySelector('img');
  gsap.timeline({ scrollTrigger: { trigger: fig, start: 'top 86%', once: true } })
    .from(fig, { clipPath: 'inset(10% 10% 10% 10%)', duration: 1, ease: 'power4.out' })
    .to(img, { scale: 1, duration: 1.25, ease: 'power4.out' }, 0);
});

/* split title char stagger */
$$('[data-split]').forEach(el => {
  gsap.from(el.querySelectorAll('.char'), {
    yPercent: 115, opacity: 0, rotate: 6,
    stagger: .035, duration: .8, ease: 'power4.out',
    scrollTrigger: { trigger: el, start: 'top 88%', once: true }
  });
});

/* ------------------------------------------------------------
   7. Brands marquee
------------------------------------------------------------ */
const brandsTrack = $('#brandsTrack');
if (brandsTrack) {
  const half = brandsTrack.scrollWidth / 2;
  gsap.to(brandsTrack, { x: -half, duration: 26, ease: 'none', repeat: -1, modifiers: { x: gsap.utils.unitize(x => parseFloat(x) % half) } });
}

/* ------------------------------------------------------------
   8. Parallax bits on scroll
------------------------------------------------------------ */
if ($('.agri__hero')) {
  gsap.to('.agri__hero img', {
    yPercent: -8, ease: 'none',
    scrollTrigger: { trigger: '.agri__panel', start: 'top bottom', end: 'bottom top', scrub: true }
  });
}
$$('.agri__thumbs img').forEach(img => {
  gsap.to(img, {
    yPercent: -10, ease: 'none',
    scrollTrigger: { trigger: '.agri__panel', start: 'top bottom', end: 'bottom top', scrub: true }
  });
});
/* 残留无人机板块已删除：元素存在时才做视差，避免 GSAP target not found 警告 */
if ($('.footer__drone')) {
  gsap.to('.footer__drone', {
    y: -26, rotate: -2, ease: 'none',
    scrollTrigger: { trigger: '.footer', start: 'top bottom', end: 'bottom bottom', scrub: 1 }
  });
}

/* ------------------------------------------------------------
   9. 3D tilt on product cards
------------------------------------------------------------ */
if (!isTouch) {
  $$('.tilt').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - .5;
      const py = (e.clientY - r.top) / r.height - .5;
      gsap.to(card, {
        rotateY: px * 10, rotateX: -py * 10, y: -6,
        duration: .5, ease: 'power2.out', transformPerspective: 900
      });
    });
    card.addEventListener('mouseleave', () => {
      gsap.to(card, { rotateX: 0, rotateY: 0, y: 0, duration: .8, ease: 'elastic.out(1,.7)' });
    });
  });
}

/* ------------------------------------------------------------
   10. Magnetic elements
------------------------------------------------------------ */
if (!isTouch) {
  $$('[data-magnetic]').forEach(el => {
    el.addEventListener('mousemove', (e) => {
      const r = el.getBoundingClientRect();
      const x = e.clientX - r.left - r.width / 2;
      const y = e.clientY - r.top - r.height / 2;
      gsap.to(el, { x: x * .3, y: y * .35, duration: .4, ease: 'power3.out' });
    });
    el.addEventListener('mouseleave', () => {
      gsap.to(el, { x: 0, y: 0, duration: .7, ease: 'elastic.out(1,.6)' });
    });
  });
}

/* ------------------------------------------------------------
   11. Cart system + fly-to-cart
------------------------------------------------------------ */
const cart = [];
const badge = $('#cartBadge');
const drawer = $('#cartDrawer');
const overlay = $('#cartOverlay');
const itemsEl = $('#cartItems');
const totalEl = $('#cartTotal');
const countTitle = $('#cartCountTitle');

function openCart() {
  drawer.classList.add('is-open');
  overlay.classList.add('is-open');
  lenis.stop();
}
function closeCart() {
  drawer.classList.remove('is-open');
  overlay.classList.remove('is-open');
  lenis.start();
}
$('#cartToggle').addEventListener('click', openCart);
$('#cartClose').addEventListener('click', closeCart);
overlay.addEventListener('click', closeCart);
addEventListener('keydown', (e) => { if (e.key === 'Escape') closeCart(); });

function renderCart() {
  const count = cart.reduce((s, i) => s + i.qty, 0);
  badge.textContent = count;
  countTitle.textContent = `(${count})`;
  gsap.fromTo(badge, { scale: 1.6 }, { scale: 1, duration: .4, ease: 'back.out(3)' });

  if (!cart.length) {
    itemsEl.innerHTML = '<p class="cart-empty">购物车还是空的，<br>快去挑选心仪的无人机吧！</p>';
  } else {
    itemsEl.innerHTML = cart.map((it, i) => `
      <div class="cart-line">
        <img class="cart-line__img" src="${it.img}" alt="${it.name}">
        <div class="cart-line__info">
          <h4>${it.name}</h4>
          <p>$${it.price.toLocaleString()}</p>
        </div>
        <div class="cart-line__qty">
          <button data-qty="${i}" data-dir="-1">−</button>
          <span>${it.qty}</span>
          <button data-qty="${i}" data-dir="1">+</button>
        </div>
      </div>`).join('');
  }
  const total = cart.reduce((s, i) => s + i.qty * i.price, 0);
  totalEl.textContent = '$' + total.toLocaleString();
}
itemsEl.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-qty]');
  if (!btn) return;
  const i = +btn.dataset.qty;
  cart[i].qty += +btn.dataset.dir;
  if (cart[i].qty <= 0) cart.splice(i, 1);
  renderCart();
});

function flyToCart(imgSrc, cb) {
  const img = document.createElement('img');
  img.className = 'fly-img';
  img.src = imgSrc;
  const start = imgSrc ? null : null;
  const target = $('#cartToggle').getBoundingClientRect();
  document.body.appendChild(img);
  const rect = img.getBoundingClientRect();
  gsap.set(img, { x: rect.left, y: rect.top });
  /* animate from the clicked card image position set inline */
  gsap.to(img, {
    x: target.left + target.width / 2 - 45,
    y: target.top + 8,
    scale: .12, rotate: 40, opacity: .7,
    duration: .9, ease: 'power3.in',
    onComplete: () => { img.remove(); cb && cb(); }
  });
}

$$('.add-to-cart').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const card = btn.closest('.product');
    const { name, price, img } = card.dataset;

    /* button feedback */
    gsap.fromTo(btn, { scale: .92 }, { scale: 1, duration: .5, ease: 'back.out(3)' });

    const clone = $('img', card).getBoundingClientRect();
    /* flying image starting at the card thumbnail */
    const fly = document.createElement('img');
    fly.className = 'fly-img';
    fly.src = img;
    document.body.appendChild(fly);
    gsap.set(fly, { left: clone.left, top: clone.top, width: clone.width, height: clone.height });
    const t = $('#cartToggle').getBoundingClientRect();
    gsap.to(fly, {
      left: t.left + t.width / 2 - 20,
      top: t.top + 6,
      width: 40, height: 40, opacity: .6, rotate: 30,
      duration: .85, ease: 'power3.in',
      onComplete: () => {
        fly.remove();
        const existing = cart.find(i => i.name === name);
        if (existing) existing.qty++;
        else cart.push({ name, price: +price, img, qty: 1 });
        renderCart();
      }
    });
  });
});
renderCart();

/* ---- Global addToCart (used by detail.html) ---- */
window.addToCart = function({ name, price, img, qty = 1 }, triggerEl) {
  const clone = triggerEl && triggerEl.closest('.product')
    ? triggerEl.closest('.product').querySelector('img').getBoundingClientRect()
    : (() => { const n = document.createElement('img'); n.src = img; document.body.appendChild(n); const r = n.getBoundingClientRect(); n.remove(); return r; })();
  gsap.fromTo(triggerEl, { scale: .92 }, { scale: 1, duration: .5, ease: 'back.out(3)' });
  const fly = document.createElement('img');
  fly.className = 'fly-img';
  fly.src = img;
  document.body.appendChild(fly);
  gsap.set(fly, { left: clone.left, top: clone.top, width: clone.width, height: clone.height });
  const t = $('#cartToggle').getBoundingClientRect();
  gsap.to(fly, {
    left: t.left + t.width / 2 - 20,
    top: t.top + 6,
    width: 40, height: 40, opacity: .6, rotate: 30,
    duration: .85, ease: 'power3.in',
    onComplete: () => {
      fly.remove();
      const existing = cart.find(i => i.name === name);
      if (existing) existing.qty += qty;
      else cart.push({ name, price: +price, img, qty });
      renderCart();
    }
  });
};

/* ---- Product card → detail page navigation (event delegation) ---- */
document.body.addEventListener('click', (e) => {
  const card = e.target.closest('.product[data-product-id]');
  if (!card) return;
  if (e.target.closest('.add-to-cart')) return; // 加购按钮单独处理
  const pid = card.dataset.productId;
  if (!pid) return;
  window.location.href = `product.html?id=${pid}`;
});
// 给产品卡加指针光标（已有 product 的 cursor 样式在 hover 时也需要）
document.querySelectorAll('.product[data-product-id]').forEach(c => c.style.cursor = 'pointer');

/* ------------------------------------------------------------
   12. Nav active state on scroll
------------------------------------------------------------ */
const navMap = [
  ['#hero', '首页'], ['#arrivals', '商品列表'], ['#movie', '产品页'],
  ['#agriculture', '关于我们'], ['#footer', '博客资讯']
];
navMap.forEach(([id, label]) => {
  // 仅当页面存在对应板块时才注册 scroll-spy，
  // 否则 GSAP 回退到 document 会错误激活导航、并产生“Element not found”警告
  if (!$(id)) return;
  ScrollTrigger.create({
    trigger: id, start: 'top 120px', end: 'bottom 120px',
    onToggle: (self) => {
      if (!self.isActive) return;
      $$('.nav__link').forEach(l => l.classList.toggle('is-active', l.textContent === label));
    }
  });
});

/* ------------------------------------------------------------
   13. Subscribe form
------------------------------------------------------------ */
$('#subscribeForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const msg = $('#subscribeMsg');
  const input = e.target.querySelector('input');
  msg.textContent = `✓ 订阅成功！${input.value} 已加入订阅列表。`;
  gsap.fromTo(msg, { y: 10, opacity: 0 }, { y: 0, opacity: 1, duration: .6, ease: 'power3.out' });
  input.value = '';
});

/* ------------------------------------------------------------
   14. Promo watermark drift on scroll
------------------------------------------------------------ */
$$('.promo__card').forEach(card => {
  const wm = card.querySelector('.promo__watermark');
  gsap.to(wm, {
    x: -60, ease: 'none',
    scrollTrigger: { trigger: card, start: 'top bottom', end: 'bottom top', scrub: true }
  });
});

/* ------------------------------------------------------------
   15. Footer headline hover shine
------------------------------------------------------------ */
$$('.footer__headline h2').forEach(h => {
  h.addEventListener('mouseenter', () => gsap.to(h, { x: 14, color: '#c9c1ff', duration: .5, ease: 'power3.out' }));
  h.addEventListener('mouseleave', () => gsap.to(h, { x: 0, color: '#fff', duration: .6, ease: 'power3.out' }));
});

/* finish */
ScrollTrigger.refresh();
