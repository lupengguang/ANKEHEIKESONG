/* ============================================================
   AI 智能升级介绍页 — ai-upgrade.js
   1. Hero 入场动画（等待 preloader 结束后播放）
   2. 滚动淡入揭示（IntersectionObserver）
   ============================================================ */

(function () {
  'use strict';

  /* ----------------------------------------------------------
     1. Hero 入场动画
     脚本在 body 末尾加载，此时 preloader 仍遮挡屏幕，
     可安全地先把 hero 内容设为隐藏，避免动画前闪烁。
  ---------------------------------------------------------- */
  const preloader = document.getElementById('preloader');

  gsap.set('.ai-hero__badge', { opacity: 0, y: 24 });
  gsap.set('.ai-hero__title .line', { opacity: 0, y: 60 });
  gsap.set('.ai-hero__sub', { opacity: 0, y: 26 });
  gsap.set('.ai-hero__actions', { opacity: 0, y: 26 });
  gsap.set('.ai-hero__visual', { opacity: 0, scale: .82 });

  /** 播放 Hero 入场时间线 */
  function playHeroIntro() {
    const tl = gsap.timeline({ defaults: { ease: 'power4.out' } });
    tl.to('.ai-hero__visual', { opacity: 1, scale: 1, duration: 1.1, ease: 'power3.out' })
      .to('.ai-hero__badge', { opacity: 1, y: 0, duration: .7 }, '-=.7')
      .to('.ai-hero__title .line', { opacity: 1, y: 0, duration: .9 }, '-=.5')
      .to('.ai-hero__sub', { opacity: 1, y: 0, duration: .7 }, '-=.55')
      .to('.ai-hero__actions', { opacity: 1, y: 0, duration: .7 }, '-=.5');
  }

  /**
   * 等待 preloader 消失。
   * main.js 在加载完成后会把 preloader 的 display 设为 none，
   * 轮询检测到后立即播放入场动画。
   */
  let waited = 0;
  const timer = setInterval(() => {
    waited += 60;
    const hidden = !preloader || preloader.style.display === 'none';
    // 兜底：超过 8 秒不再等待（防止极端情况下动画永不播放）
    if (hidden || waited > 8000) {
      clearInterval(timer);
      playHeroIntro();
    }
  }, 60);

  /* ----------------------------------------------------------
     2. 滚动淡入揭示
     所有带 data-ai-reveal 的元素进入视口时加 .is-visible
  ---------------------------------------------------------- */
  const revealEls = document.querySelectorAll('[data-ai-reveal]');

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target); // 只播放一次
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -40px 0px',
    });

    revealEls.forEach((el) => io.observe(el));
  } else {
    // 老浏览器不支持 IntersectionObserver：直接全部显示
    revealEls.forEach((el) => el.classList.add('is-visible'));
  }

  /* ----------------------------------------------------------
     3. 悬浮微动效（emoji 图标 / 灯泡）
     随机浮动幅度与速度，避免整齐划一
  ---------------------------------------------------------- */
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!reduceMotion) {
    document.querySelectorAll('[data-float]').forEach((el, i) => {
      gsap.to(el, {
        y: i % 2 === 0 ? -8 : 7,
        rotate: i % 2 === 0 ? 5 : -5,
        duration: 2.4 + Math.random() * 1.6,
        ease: 'sine.inOut',
        repeat: -1,
        yoyo: true,
        delay: Math.random() * .8,
      });
    });
  }

  /* ----------------------------------------------------------
     4. 板块头部核心滚动视差（轻微反向漂移）
  ---------------------------------------------------------- */
  if (!reduceMotion && window.ScrollTrigger) {
    document.querySelectorAll('[data-head-visual]').forEach((el) => {
      gsap.to(el.querySelector('.ai-head-visual__core'), {
        yPercent: 18,
        ease: 'none',
        scrollTrigger: {
          trigger: el,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 1,
        },
      });
    });
  }

  /* ----------------------------------------------------------
     5. 3D 倾斜卡片（仅带鼠标的设备启用）
     - 悬停上浮 8px
     - 指针移动驱动 rotateX / rotateY
     - 离开时弹性回正
  ---------------------------------------------------------- */
  const canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  if (canHover && !reduceMotion) {
    // 卡片网格需要透视景深
    document.querySelectorAll('.ai-cards').forEach((grid) => {
      gsap.set(grid, { perspective: 1000 });
    });

    document.querySelectorAll('[data-tilt]').forEach((card) => {
      const MAX_RX = 7;   // 上下倾斜最大角度
      const MAX_RY = 9;   // 左右倾斜最大角度
      let raf = null;
      let target = { rx: 0, ry: 0 };

      const apply = () => {
        raf = null;
        gsap.to(card, {
          rotateX: target.rx,
          rotateY: target.ry,
          y: target.y || -8,
          duration: .45,
          ease: 'power2.out',
          overwrite: 'auto',
        });
      };

      card.addEventListener('pointermove', (e) => {
        const rect = card.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width - .5;   // -.5 ~ .5
        const py = (e.clientY - rect.top) / rect.height - .5;
        target = { rx: -py * MAX_RX * 2, ry: px * MAX_RY * 2, y: -8 };
        if (!raf) raf = requestAnimationFrame(apply);
      });

      card.addEventListener('pointerenter', () => {
        target = { rx: 0, ry: 0, y: -8 };
        gsap.to(card, { y: -8, duration: .3, ease: 'power2.out', overwrite: 'auto' });
      });

      card.addEventListener('pointerleave', () => {
        target = { rx: 0, ry: 0, y: 0 };
        gsap.to(card, {
          rotateX: 0,
          rotateY: 0,
          y: 0,
          duration: .9,
          ease: 'elastic.out(1, .55)',
          overwrite: 'auto',
        });
      });
    });
  }

  /* ----------------------------------------------------------
     6. 玻璃卡片装饰层注入（纯装饰，零 HTML 侵入）
        - 斜向扫光
        - 霓虹扫描线
  ---------------------------------------------------------- */
  document.querySelectorAll('.ai-card').forEach((card) => {
    const sheen = document.createElement('span');
    sheen.className = 'ai-card__sheen';
    const scan = document.createElement('span');
    scan.className = 'ai-card__scanline';
    card.appendChild(sheen);
    card.appendChild(scan);
  });

  /* ----------------------------------------------------------
     7. 极光星云指针视差（quickTo 高性能）
  ---------------------------------------------------------- */
  if (canHover && !reduceMotion) {
    document.querySelectorAll('[data-aurora]').forEach((el, i) => {
      const depth = (i % 2 === 0 ? 46 : 28) * (i < 2 ? 1 : -1);
      const qx = gsap.quickTo(el, 'x', { duration: 1.2, ease: 'power3' });
      const qy = gsap.quickTo(el, 'y', { duration: 1.2, ease: 'power3' });
      window.addEventListener('pointermove', (e) => {
        const nx = e.clientX / innerWidth - .5;
        const ny = e.clientY / innerHeight - .5;
        qx(nx * depth);
        qy(ny * depth);
      }, { passive: true });
    });
  }

  /* ----------------------------------------------------------
     8. 深空星空 canvas
        - 星星闪烁 + 缓慢下沉
        - 指针轻微视差
        - 随机流星
        - 页面隐藏时暂停；减少动效时只绘制静态一帧
  ---------------------------------------------------------- */
  function initStarfield() {
    const cv = document.getElementById('aiStarfield');
    if (!cv) return;
    const ctx = cv.getContext('2d');
    const DPR = Math.min(window.devicePixelRatio || 1, 2);

    let w = 0, h = 0, stars = [], running = false;
    const pointer = { x: .5, y: .5 };

    /* 生成星星（数量按面积，封顶 220） */
    function buildStars() {
      const count = Math.min(220, Math.floor(w * h / 8500));
      stars = [];
      for (let i = 0; i < count; i++) {
        const roll = Math.random();
        stars.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: Math.random() * 1.4 + .35,
          phase: Math.random() * Math.PI * 2,
          speed: .5 + Math.random() * 1.4,
          drift: .04 + Math.random() * .1,
          tint: roll < .68 ? [219, 231, 254] : roll < .86 ? [147, 197, 253] : [196, 181, 253],
        });
      }
    }

    function resize() {
      w = cv.clientWidth;
      h = cv.clientHeight;
      cv.width = Math.max(1, w * DPR);
      cv.height = Math.max(1, h * DPR);
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      buildStars();
    }

    /* 流星状态 */
    let meteor = null;
    let meteorAt = 2600 + Math.random() * 4000;
    let elapsed = 0;
    let last = performance.now();

    function spawnMeteor() {
      const fromLeft = Math.random() < .5;
      meteor = {
        x: fromLeft ? Math.random() * w * .5 : w * .5 + Math.random() * w * .5,
        y: Math.random() * h * .3,
        vx: (fromLeft ? 1 : -1) * (6 + Math.random() * 3),
        vy: 3.6 + Math.random() * 2,
        life: 1,
      };
    }

    function drawFrame(now) {
      const dt = Math.min(now - last, 50);
      last = now;
      elapsed += dt;

      ctx.clearRect(0, 0, w, h);

      /* 指针视差偏移（星星越大偏移越多） */
      const ox = (pointer.x - .5) * 22;
      const oy = (pointer.y - .5) * 14;

      for (const s of stars) {
        s.phase += dt / 1000 * s.speed * 2;
        s.y += s.drift * dt / 16;
        if (s.y > h + 4) { s.y = -4; s.x = Math.random() * w; }
        if (s.x > w + 4) s.x = -4;
        if (s.x < -4) s.x = w + 4;

        const alpha = .28 + .72 * (Math.sin(s.phase) * .5 + .5);
        const x = s.x - ox * s.r;
        const y = s.y - oy * s.r;

        ctx.beginPath();
        ctx.arc(x, y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(' + s.tint[0] + ',' + s.tint[1] + ',' + s.tint[2] + ',' + alpha + ')';
        ctx.fill();

        /* 较大的星星加十字微光 */
        if (s.r > 1.25) {
          ctx.strokeStyle = 'rgba(' + s.tint[0] + ',' + s.tint[1] + ',' + s.tint[2] + ',' + (alpha * .45) + ')';
          ctx.lineWidth = .6;
          ctx.beginPath();
          ctx.moveTo(x - s.r * 3, y); ctx.lineTo(x + s.r * 3, y);
          ctx.moveTo(x, y - s.r * 3); ctx.lineTo(x, y + s.r * 3);
          ctx.stroke();
        }
      }

      /* 流星调度 */
      meteorAt -= dt;
      if (meteorAt <= 0 && !meteor) {
        spawnMeteor();
        meteorAt = 4200 + Math.random() * 5200;
      }
      if (meteor) {
        meteor.x += meteor.vx;
        meteor.y += meteor.vy;
        meteor.life -= dt / 1000 * .55;

        const tailX = meteor.x - meteor.vx * 9;
        const tailY = meteor.y - meteor.vy * 9;
        const grad = ctx.createLinearGradient(meteor.x, meteor.y, tailX, tailY);
        grad.addColorStop(0, 'rgba(191,219,254,' + Math.max(meteor.life, 0) + ')');
        grad.addColorStop(1, 'rgba(191,219,254,0)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(meteor.x, meteor.y);
        ctx.lineTo(tailX, tailY);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(meteor.x, meteor.y, 1.6, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255,255,255,' + Math.max(meteor.life, 0) + ')';
        ctx.fill();

        if (meteor.life <= 0 || meteor.x < -80 || meteor.x > w + 80 || meteor.y > h + 80) {
          meteor = null;
        }
      }

      /* 避免未使用告警 */
      void elapsed;

      if (running) requestAnimationFrame(drawFrame);
    }

    function start() {
      if (running) return;
      running = true;
      last = performance.now();
      requestAnimationFrame(drawFrame);
    }
    function stop() { running = false; }

    /* 静态帧（减少动效偏好时使用） */
    function drawStatic() {
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(' + s.tint[0] + ',' + s.tint[1] + ',' + s.tint[2] + ',.7)';
        ctx.fill();
      }
    }

    window.addEventListener('resize', resize);
    window.addEventListener('pointermove', (e) => {
      pointer.x = e.clientX / innerWidth;
      pointer.y = e.clientY / innerHeight;
    }, { passive: true });

    /* 标签隐藏时暂停渲染，省电 */
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stop();
      else if (!reduceMotion) start();
    });

    resize();
    if (reduceMotion) {
      drawStatic();
    } else {
      start();
    }
  }

  initStarfield();
})();
