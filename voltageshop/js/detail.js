/* ============================================================
   Product detail page — data + interactions
   ============================================================ */

// ---------- Product data ----------
const productData = {
  'eufy-4k-nvr-s4-max-8': {
    id: 'eufy-4k-nvr-s4-max-8',
    name: 'eufy 4K NVR S4 Max 8',
    price: 499,
    priceStr: '$499',
    tag: '新品上市',
    img: 'images/products/eufy-4k-nvr-s4-max-8.png',
    desc: '专业级 8 路 4K 网络视频录像机，支持 2TB 本地存储与智能人形/车辆过滤，让家庭与小型商铺的安防监控更高效。',
    miniSpecs: [
      { label: '8 路 4K 同步录制', icon: 'monitor' },
      { label: '2TB 本地存储', icon: 'chip' },
      { label: '智能人形 / 车辆过滤', icon: 'eye' },
      { label: '远程实时预览', icon: 'globe' }
    ],
    colors: ['#2a2a30', '#f2f2f5'],
    specs: [
      ['产品类型', '网络视频录像机 (NVR)'],
      ['支持路数', '8 路'],
      ['最高分辨率', '4K (3840 × 2160)'],
      ['存储容量', '内置 2TB HDD，可扩展'],
      ['视频编码', 'H.265 / H.264'],
      ['网络接口', '千兆以太网 × 1'],
      ['无线连接', '不支持（有线）'],
      ['本地回放', '支持'],
      ['移动侦测', '支持（人形 / 车辆过滤）'],
      ['远程访问', 'eufy App / Web 端'],
      ['尺寸', '320 × 240 × 45 mm'],
      ['重量', '约 1.8 kg'],
      ['工作温度', '0°C ~ 45°C'],
      ['保修', '2 年官方质保']
    ],
    features: [
      { icon: 'monitor', title: '8 路 4K 同步', body: '同时接入 8 台 4K 摄像头，全通道实时预览与录制，无延迟、无丢帧。' },
      { icon: 'chip', title: '2TB 大容量', body: '内置 2TB 机械硬盘，支持扩展存储，最长可存储数月的高清录像。' },
      { icon: 'eye', title: '智能过滤', body: 'AI 人形 / 车辆侦测，过滤无效告警，只推送真正重要的事件通知。' },
      { icon: 'globe', title: '远程访问', body: '通过 eufy App 或 Web 端随时随地查看实时画面与历史录像。' },
      { icon: 'shield', title: '本地存储更安全', body: '视频数据本地存储，不依赖云端，隐私更有保障，不怕网络中断。' },
      { icon: 'plug', title: '即插即用', body: '简单安装，连接 PoE 摄像头即可开始工作，无需复杂配置。' }
    ],
    gallery: [
      'images/products/eufy-4k-nvr-s4-max-8.png',
      'images/products/eufy-4k-nvr-s4-max-8-1.png'
    ]
  },

  'eufycam-s4': {
    id: 'eufycam-s4',
    name: 'eufyCam S4',
    price: 249,
    priceStr: '$249',
    tag: '新品上市',
    img: 'images/products/eufycam-s4.png',
    desc: '太阳能供电的 2K 全彩无线安防摄像头，IP67 级防水防尘，半年续航，支持双向语音与 AI 智能识别。',
    miniSpecs: [
      { label: '2K 全彩夜视', icon: 'star' },
      { label: '180 天超长续航', icon: 'battery' },
      { label: 'IP67 防护等级', icon: 'droplet' },
      { label: '双向语音对讲', icon: 'mic' }
    ],
    colors: ['#ffffff', '#2a2a30'],
    specs: [
      ['产品类型', '太阳能无线安防摄像头'],
      ['图像传感器', '2K CMOS'],
      ['最高分辨率', '2K (2560 × 1440)'],
      ['夜视类型', '全彩夜视'],
      ['夜视距离', '约 10 米'],
      ['电池容量', '9000 mAh 内置锂电'],
      ['续航时间', '最长 180 天'],
      ['太阳能板', '标配 2W 单晶硅'],
      ['无线连接', 'Wi-Fi 2.4GHz'],
      ['防护等级', 'IP67'],
      ['双向语音', '支持'],
      ['AI 侦测', '人形 / 车辆 / 宠物'],
      ['本地存储', '不支持'],
      ['云端存储', 'eufy 云存储（付费）'],
      ['工作温度', '-20°C ~ 50°C'],
      ['尺寸', '135 × 95 × 58 mm'],
      ['重量', '约 380 g'],
      ['保修', '2 年官方质保']
    ],
    features: [
      { icon: 'star', title: '2K 全彩夜视', body: '即使深夜也能呈现清晰彩色画面，告别黑白夜视的模糊与失真。' },
      { icon: 'battery', title: '180 天续航', body: '大容量内置电池 + 太阳能板，一次安装半年无需充电。' },
      { icon: 'droplet', title: 'IP67 防护', body: '防尘防水，室内外皆可安装，雨雪天气照常工作。' },
      { icon: 'mic', title: '双向语音', body: '随时随地与家人或访客通话，无需额外对讲设备。' },
      { icon: 'brain', title: 'AI 智能识别', body: '区分人、车、宠物，减少无效告警推送。' },
      { icon: 'sun', title: '太阳能供电', body: '附赠高效太阳能板，光照充足时自动充电，永不断电。' }
    ],
    gallery: [
      'images/products/eufycam-s4.png',
      'images/products/eufycam-s4-1.png'
    ]
  },

  'solocam-s340': {
    id: 'solocam-s340',
    name: 'SoloCam S340',
    price: 199,
    priceStr: '$199',
    tag: '新品上市',
    img: 'images/products/solocam-s340.png',
    desc: '太阳能 + 4G 双连接 360° 全景摄像头，双摄像头协同工作，支持智能追踪，是无 Wi-Fi 场景的最佳选择。',
    miniSpecs: [
      { label: '太阳能 + 4G 供电', icon: 'sun' },
      { label: '360° 全景视野', icon: 'rotate' },
      { label: '双摄像头协同', icon: 'monitor' },
      { label: '智能追踪', icon: 'target' }
    ],
    colors: ['#ffffff'],
    specs: [
      ['产品类型', '太阳能 4G 全景摄像头'],
      ['连接方式', '4G LTE（全网通）'],
      ['图像传感器', '2K CMOS × 2'],
      ['最高分辨率', '2K (2560 × 1440)'],
      ['视野角度', '360° 全景'],
      ['电池容量', '6000 mAh 内置锂电'],
      ['续航时间', '约 90 天（4G 模式）'],
      ['太阳能板', '标配 3W 单晶硅'],
      ['双向语音', '支持'],
      ['智能追踪', '支持（人形 / 车辆）'],
      ['本地存储', '不支持'],
      ['云端存储', 'eufy 云存储（付费）'],
      ['防护等级', 'IP65'],
      ['工作温度', '-20°C ~ 50°C'],
      ['SIM 卡', 'Nano SIM（需自备）'],
      ['尺寸', '150 × 100 × 85 mm'],
      ['重量', '约 520 g'],
      ['保修', '2 年官方质保']
    ],
    features: [
      { icon: 'sun', title: '太阳能 + 4G', body: '无需 Wi-Fi 也能工作，4G 全网通 + 太阳能供电，偏远地区也可覆盖。' },
      { icon: 'rotate', title: '360° 全景', body: '双摄像头拼接实现 360° 无死角全景视野，一台顶两台。' },
      { icon: 'target', title: '智能追踪', body: '自动识别人形 / 车辆并追踪拍摄，关键时刻不错过。' },
      { icon: 'mic', title: '双向语音', body: '远程对讲，户外也能与访客实时沟通。' },
      { icon: 'map', title: '无 Wi-Fi 场景', body: '农场、仓库、工地、车库等无网络环境的最佳选择。' },
      { icon: 'shield', title: 'IP65 防护', body: '防尘防水，户外恶劣环境稳定运行。' }
    ],
    gallery: [
      'images/products/solocam-s340.png',
      'images/products/solocam-s340-1.png'
    ]
  },

  'eufy-4g-lte-cam-s330': {
    id: 'eufy-4g-lte-cam-s330',
    name: 'eufy 4G LTE Cam S330',
    price: 299,
    priceStr: '$299',
    tag: '新品上市',
    img: 'images/products/eufy-4g-lte-cam-s330.png',
    desc: '4G LTE 全网通户外摄像头，无需 Wi-Fi 即可联网，内置太阳能电池板，支持移动侦测告警与云端存储。',
    miniSpecs: [
      { label: '4G 全网通', icon: 'signal' },
      { label: '无需 Wi-Fi', icon: 'offline' },
      { label: '移动侦测告警', icon: 'bell' },
      { label: '云端存储', icon: 'cloud' }
    ],
    colors: ['#2a2a30'],
    specs: [
      ['产品类型', '4G LTE 户外安防摄像头'],
      ['连接方式', '4G LTE（全网通）'],
      ['图像传感器', '1080P CMOS'],
      ['最高分辨率', '1080P (1920 × 1080)'],
      ['夜视类型', '红外夜视'],
      ['夜视距离', '约 8 米'],
      ['电池容量', '内置锂电（可充电）'],
      ['供电方式', '太阳能板 + 可更换锂电池'],
      ['双向语音', '支持'],
      ['移动侦测', '支持'],
      ['本地存储', 'Micro SD 卡（最大 128GB）'],
      ['云端存储', 'eufy 云存储（付费）'],
      ['防护等级', 'IP66'],
      ['工作温度', '-20°C ~ 50°C'],
      ['SIM 卡', 'Nano SIM（需自备）'],
      ['尺寸', '115 × 75 × 70 mm'],
      ['重量', '约 280 g'],
      ['保修', '2 年官方质保']
    ],
    features: [
      { icon: 'signal', title: '4G 全网通', body: '支持三大运营商 4G 网络，偏远地区也能稳定联网。' },
      { icon: 'offline', title: '无需 Wi-Fi', body: '摆脱 Wi-Fi 束缚，只要有 4G 信号就能安装使用。' },
      { icon: 'bell', title: '移动侦测告警', body: '实时检测到移动物体立即推送告警通知。' },
      { icon: 'cloud', title: '云端存储', body: '录像自动上传云端，设备丢失也不怕视频丢失。' },
      { icon: 'sd', title: '本地 Micro SD', body: '支持本地 Micro SD 卡存储，双重保险。' },
      { icon: 'battery', title: '太阳能续航', body: '内置太阳能板，自动充电，长期免维护。' }
    ],
    gallery: [
      'images/products/eufy-4g-lte-cam-s330.png',
      'images/products/eufy-4g-lte-cam-s330-1.png'
    ]
  }
};

// Other products for "related" section (from index.html arrivals + industry)
const otherProducts = [
  { id: 'eufycam-3-pro', name: 'eufyCam 3 Pro', price: 199, img: 'images/products/eufycam-s4.png', desc: '4K 彩色夜视 · 太阳能续航' },
  { id: 'eufycam-3c', name: 'eufyCam 3C', price: 159, img: 'images/products/eufycam-s4.png', desc: '2K 全彩影像 · 半年续航' },
  { id: 'solocam-e40', name: 'SoloCam E40', price: 149, img: 'images/products/solocam-s340.png', desc: '太阳能供电 · 360° 视野' },
  { id: 'solocam-s40', name: 'SoloCam S40', price: 179, img: 'images/products/solocam-s340.png', desc: '太阳能 + 4G · 全景看护' }
];

// ---------- Icon map (inline SVGs, keyed by name) ----------
const iconMap = {
  monitor: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
  chip:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/></svg>',
  eye:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>',
  globe:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></svg>',
  star:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m12 3 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.8 6.2 20.9l1.1-6.5L2.6 9.8l6.5-.9L12 3Z"/></svg>',
  battery: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="7" width="16" height="10" rx="2"/><rect x="18" y="10" width="3" height="4"/><path d="M6 12h4"/></svg>',
  droplet: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2s6 7 6 12a6 6 0 0 1-12 0c0-5 6-12 6-12Z"/></svg>',
  mic:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>',
  sun:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  rotate:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>',
  target:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></svg>',
  signal:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 20h.01M7 20v-6M12 20v-10M17 20V6M22 20V2"/></svg>',
  offline: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1 1l22 22M16.7 11.4A8 8 0 0 1 18 13M5 13a8 8 0 0 1 2.5-5.8M9 19a4 4 0 0 1 6 0M2 9a15 15 0 0 1 4.2-2.2M18.5 8.8A15 15 0 0 1 22 10.3"/></svg>',
  bell:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M18 16V11a6 6 0 1 0-12 0v5l-2 2h16l-2-2ZM10 21a2 2 0 0 0 4 0"/></svg>',
  cloud:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 18a5 5 0 0 1-1-9.9A7 7 0 0 1 19 11a4 4 0 0 1-1 7.9H7Z"/></svg>',
  sd:      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6a2 2 0 0 1 2-2h10l4 4v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6Z"/><path d="M8 12v4M12 12v4M16 12v4"/></svg>',
  brain:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-3 3 3 3 0 0 0 1 2.3A3 3 0 0 0 6 17a3 3 0 0 0 3 3"/><path d="M15 3a3 3 0 0 1 3 3 3 3 0 0 1 3 3 3 3 0 0 1-1 2.3A3 3 0 0 1 18 17a3 3 0 0 1-3 3"/><path d="M12 3v18"/></svg>',
  shield:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2 4 5v6c0 5 3.5 9.5 8 11 4.5-1.5 8-6 8-11V5l-8-3Z"/></svg>',
  map:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 3 3 6v15l6-3 6 3 6-3V3l-6 3-6-3ZM9 3v15M15 6v15"/></svg>',
  plug:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 2v6M15 2v6M7 8h10v4a5 5 0 0 1-10 0V8ZM12 17v4"/></svg>',
  target_alt: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></svg>'
};

// ---------- Main ----------
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const id = params.get('id');
  const data = productData[id];

  if (!data) {
    // 无效 ID，返回首页
    console.warn('[detail] 未找到产品 id:', id, '— 跳回首页');
    window.location.replace('index.html');
    return;
  }

  renderProduct(data);
  bindDetailInteractions(data);

  // 加购按钮 — 接入全局购物车
  const addCartBtn = document.getElementById('detailAddCart');
  if (addCartBtn) {
    addCartBtn.addEventListener('click', (e) => {
      const qty = parseInt(document.getElementById('qtyVal').textContent, 10) || 1;
      if (typeof window.addToCart === 'function') {
        window.addToCart({
          name: data.name,
          price: data.price,
          img: data.img,
          qty,
          id: data.id
        }, e.currentTarget);
      } else {
        console.warn('[detail] 全局 addToCart 未找到');
      }
    });
  }

  // 返回按钮
  const backBtn = document.getElementById('backBtn');
  if (backBtn) {
    backBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (document.referrer && document.referrer.includes('product.html')) {
        history.back();
      } else {
        window.location.href = 'index.html#arrivals';
      }
    });
  }

  // 面包屑 — 也可点击跳转
  const crumb = document.querySelector('.breadcrumb a:nth-child(2)');
  if (crumb) crumb.href = 'index.html#arrivals';
});

// ---------- Render ----------
function renderProduct(data) {
  document.title = `${data.name} — Eufy HomeCare・智家看护`;

  // 面包屑
  const crumbName = document.getElementById('crumbName');
  if (crumbName) crumbName.textContent = data.name;

  // 基本信息
  document.getElementById('detailTag').textContent = data.tag || '新品上市';
  document.getElementById('detailName').textContent = data.name;
  document.getElementById('detailPrice').textContent = data.priceStr;
  document.getElementById('detailDesc').textContent = data.desc;

  // 主图（用 gallery 第一张）
  const mainImg = document.getElementById('detailMainImg');
  mainImg.src = data.gallery[0];
  mainImg.alt = data.name;

  // 迷你规格
  const miniSpecs = document.getElementById('detailSpecsMini');
  miniSpecs.innerHTML = data.miniSpecs.map(s => `
    <div class="detail-spec-mini">
      ${iconMap[s.icon] || ''}
      <span>${s.label}</span>
    </div>
  `).join('');

  // 颜色选择
  const colorsList = document.getElementById('detailColorsList');
  colorsList.innerHTML = data.colors.map((c, i) =>
    `<span class="color-dot${i === 0 ? ' is-active' : ''}" style="background:${c}" data-color="${c}"></span>`
  ).join('');
  colorsList.querySelectorAll('.color-dot').forEach(d => {
    d.addEventListener('click', () => {
      colorsList.querySelectorAll('.color-dot').forEach(x => x.classList.remove('is-active'));
      d.classList.add('is-active');
    });
  });

  // 图廊缩略图
  const thumbs = document.getElementById('detailThumbs');
  thumbs.innerHTML = data.gallery.map((src, i) => `
    <button class="detail-thumb${i === 0 ? ' is-active' : ''}" data-src="${src}">
      <img src="${src}" alt="预览 ${i + 1}">
    </button>
  `).join('');
  thumbs.querySelectorAll('.detail-thumb').forEach(thumb => {
    thumb.addEventListener('click', () => {
      const src = thumb.dataset.src;
      const stage = document.getElementById('detailStage');
      const mainImg = document.getElementById('detailMainImg');
      stage.classList.add('is-tilt');
      mainImg.style.opacity = '0';
      setTimeout(() => {
        mainImg.src = src;
        mainImg.style.opacity = '1';
        stage.classList.remove('is-tilt');
      }, 260);
      thumbs.querySelectorAll('.detail-thumb').forEach(t => t.classList.remove('is-active'));
      thumb.classList.add('is-active');
    });
  });

  // 规格参数表
  const specsGrid = document.getElementById('specsGrid');
  specsGrid.innerHTML = data.specs.map(([k, v]) =>
    `<div class="spec-row"><span>${k}</span><span>${v}</span></div>`
  ).join('');

  // 特性 Bento
  const bento = document.getElementById('featuresBento');
  bento.innerHTML = data.features.map(f => `
    <div class="feature-card">
      <div class="feature-card__icon">${iconMap[f.icon] || ''}</div>
      <h3>${f.title}</h3>
      <p>${f.body}</p>
    </div>
  `).join('');

  // 相关推荐（排除当前产品）
  const related = document.getElementById('relatedRow');
  const pool = otherProducts.filter(p => p.id !== data.id);
  related.innerHTML = pool.slice(0, 4).map(p => `
    <article class="product tilt" data-reveal
             data-name="${p.name}" data-price="${p.price}"
             data-img="${p.img}" data-product-id="${p.id}">
      <div class="product__media">
        <img src="${p.img}" alt="${p.name}">
      </div>
      <h3 class="product__name">${p.name}</h3>
      <p class="product__desc">${p.desc}</p>
      <div class="product__price">$${p.price}</div>
      <button class="btn-cart add-to-cart" data-cursor="hover">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 7h12l-1.2 12.2a2 2 0 0 1-2 1.8H9.2a2 2 0 0 1-2-1.8L6 7Z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>
        加入购物车
      </button>
    </article>
  `).join('');

  // 相关推荐也加点击跳转（跳到 4 款详情页的直接打开 index.html 新品区）
  related.querySelectorAll('[data-product-id]').forEach(card => {
    card.addEventListener('click', (ev) => {
      if (ev.target.closest('.btn-cart')) return;
      const pid = card.dataset.productId;
      const knownIds = ['eufy-4k-nvr-s4-max-8','eufycam-s4','solocam-s340','eufy-4g-lte-cam-s330'];
      if (knownIds.includes(pid)) {
        window.location.href = `product.html?id=${pid}`;
      } else {
        window.location.href = 'index.html#arrivals';
      }
    });
  });

  // 让 ScrollTrigger 重新扫描动态生成的规格表 / 特性卡片
  if (typeof ScrollTrigger !== 'undefined') ScrollTrigger.refresh();
}

// ---------- Interactions ----------
function bindDetailInteractions(data) {
  // 3D tilt on detail stage
  const stage = document.getElementById('detailStage');
  if (stage) {
    const rect = () => stage.getBoundingClientRect();
    const tiltOn = (e) => {
      const r = rect();
      const x = (e.clientX - r.left) / r.width;
      const y = (e.clientY - r.top) / r.height;
      const rx = (y - 0.5) * -12;
      const ry = (x - 0.5) * 12;
      gsap.to(stage, { rotationX: rx, rotationY: ry, duration: 0.35, ease: 'power2.out' });
    };
    const tiltOff = () => {
      gsap.to(stage, { rotationX: 0, rotationY: 0, duration: 0.55, ease: 'elastic.out(1, 0.7)' });
    };
    stage.addEventListener('mousemove', tiltOn);
    stage.addEventListener('mouseleave', tiltOff);
  }

  // 数量增减
  const qtyVal = document.getElementById('qtyVal');
  const qtyMinus = document.getElementById('qtyMinus');
  const qtyPlus = document.getElementById('qtyPlus');
  qtyMinus.addEventListener('click', () => {
    let n = parseInt(qtyVal.textContent, 10);
    if (n > 1) { qtyVal.textContent = --n; }
  });
  qtyPlus.addEventListener('click', () => {
    let n = parseInt(qtyVal.textContent, 10);
    qtyVal.textContent = ++n;
  });

  // ScrollTrigger 规格表行揭示
  if (typeof ScrollTrigger !== 'undefined') {
    gsap.utils.toArray('.spec-row').forEach((row, i) => {
      gsap.from(row, {
        opacity: 0, y: 16, duration: 0.6, delay: i * 0.04,
        scrollTrigger: {
          trigger: row,
          start: 'top 90%',
          once: true
        }
      });
    });

    // 特性卡片揭示
    gsap.utils.toArray('.feature-card').forEach((card, i) => {
      gsap.from(card, {
        opacity: 0, y: 24, duration: 0.6, delay: i * 0.08,
        scrollTrigger: {
          trigger: card,
          start: 'top 88%',
          once: true
        }
      });
    });
  }
}
