<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Piece & Petal — Tokyo Drops</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .hide-scrollbar::-webkit-scrollbar { display: none; }
    .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  </style>
</head>
<body class="bg-[#FAF8F5] text-stone-800 pb-28 antialiased selection:bg-stone-200">

  <!-- Header -->
  <header class="sticky top-0 z-30 bg-[#FAF8F5]/90 backdrop-blur-md px-5 py-4 border-b border-stone-200/60 flex items-center justify-between">
    <div>
      <h1 class="text-lg font-bold tracking-tight text-stone-900">Piece & Petal</h1>
      <p class="text-[11px] font-medium text-stone-500 uppercase tracking-wider">Tokyo Sourcing • Drop 01</p>
    </div>
    <span class="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
      100% Tokyo Authentic
    </span>
  </header>

  <!-- Filter Bar -->
  <div class="sticky top-[69px] z-20 bg-[#FAF8F5]/90 backdrop-blur-md px-5 py-3 border-b border-stone-100 flex flex-col space-y-2">
    <div id="category-bar" class="flex space-x-2 overflow-x-auto hide-scrollbar"></div>
  </div>

  <!-- Product Grid -->
  <main class="p-5">
    <div id="product-grid" class="grid grid-cols-2 gap-4">
      <div class="col-span-2 text-center py-16 text-xs text-stone-400">Loading catalog...</div>
    </div>
  </main>

  <!-- Product Detail Drawer -->
  <div id="detail-modal" class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm hidden flex items-end">
    <div class="bg-white w-full rounded-t-3xl max-h-[92vh] overflow-y-auto p-6 space-y-5 hide-scrollbar">
      <div class="flex justify-between items-center pb-2 border-b border-stone-100">
        <span id="p-brand-badge" class="px-2.5 py-1 rounded-full text-xs font-bold bg-stone-100 text-stone-700"></span>
        <button onclick="closeDetail()" class="text-stone-400 hover:text-stone-700 text-sm font-semibold p-1">✕</button>
      </div>

      <div class="aspect-square w-full bg-[#FAF8F5] rounded-2xl overflow-hidden border border-stone-100">
        <img id="p-detail-img" src="" alt="Product" class="w-full h-full object-contain">
      </div>

      <div>
        <h2 id="p-detail-title" class="text-lg font-bold text-stone-900 leading-snug"></h2>
        <p id="p-detail-price" class="text-2xl font-extrabold text-stone-900 mt-1"></p>
      </div>

      <div class="grid grid-cols-2 gap-2 text-[11px] font-semibold text-stone-600">
        <div class="bg-stone-50 border border-stone-200/70 p-2.5 rounded-xl flex items-center space-x-2">
          <span>🚚</span>
          <span>Phnom Penh 1–2 days</span>
        </div>
        <div class="bg-stone-50 border border-stone-200/70 p-2.5 rounded-xl flex items-center space-x-2">
          <span>📦</span>
          <span>Provinces via VET</span>
        </div>
        <div class="bg-stone-50 border border-stone-200/70 p-2.5 rounded-xl flex items-center space-x-2">
          <span>✓</span>
          <span>100% Tokyo Authentic</span>
        </div>
        <div class="bg-stone-50 border border-stone-200/70 p-2.5 rounded-xl flex items-center space-x-2">
          <span>💵</span>
          <span>KHQR or COD Available</span>
        </div>
      </div>

      <div class="space-y-2 pt-2">
        <div class="grid grid-cols-2 gap-3">
          <button id="p-add-cart-btn" class="w-full py-3.5 bg-stone-900 text-white rounded-xl text-xs font-bold active:scale-[0.98] transition">
            Add to Cart
          </button>
          <button id="p-buy-now-btn" class="w-full py-3.5 bg-amber-400 hover:bg-amber-500 text-stone-900 rounded-xl text-xs font-bold active:scale-[0.98] transition">
            Place Order Now
          </button>
        </div>
        <button onclick="askAboutProduct()" class="w-full py-3 text-xs font-semibold text-stone-600 hover:text-stone-900 flex items-center justify-center space-x-1">
          <span>💬</span>
          <span>Ask about this product</span>
        </button>
      </div>

      <div class="space-y-2 border-t border-stone-100 pt-4">
        <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400">Description</h3>
        <p id="p-detail-desc" class="text-xs text-stone-600 leading-relaxed"></p>
      </div>

      <div class="space-y-2 border-t border-stone-100 pt-4">
        <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400">Specifications</h3>
        <div class="grid grid-cols-2 gap-y-2 text-xs py-2">
          <span class="text-stone-400">Brand</span>
          <span id="spec-brand" class="font-medium text-stone-800"></span>
          <span class="text-stone-400">Category</span>
          <span id="spec-category" class="font-medium text-stone-800"></span>
          <span class="text-stone-400">Size / Volume</span>
          <span id="spec-size" class="font-medium text-stone-800"></span>
          <span class="text-stone-400">Availability</span>
          <span id="spec-avail" class="font-medium text-stone-800"></span>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom Cart Sticky Bar -->
  <div id="cart-bar" class="fixed bottom-4 inset-x-4 max-w-md mx-auto hidden z-40">
    <button onclick="openCheckout()" class="w-full bg-stone-900 text-white p-4 rounded-2xl shadow-xl flex items-center justify-between font-medium active:scale-[0.98] transition">
      <div class="flex items-center space-x-2">
        <span id="cart-count-badge" class="bg-stone-700 text-[11px] px-2 py-0.5 rounded-full font-semibold">0</span>
        <span class="text-sm font-semibold">View Selected Items</span>
      </div>
      <span id="cart-total-display" class="text-sm font-semibold">$0.00</span>
    </button>
  </div>

  <!-- Checkout Drawer -->
  <div id="checkout-modal" class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm hidden flex items-end">
    <div class="bg-white w-full rounded-t-3xl max-h-[92vh] overflow-y-auto p-6 space-y-5 hide-scrollbar">
      <div class="flex justify-between items-center pb-2 border-b border-stone-100">
        <div>
          <h2 class="text-base font-semibold text-stone-900">Checkout</h2>
          <p class="text-[11px] text-stone-400">Choose payment method & address</p>
        </div>
        <button onclick="closeCheckout()" class="text-stone-400 hover:text-stone-700 text-sm font-medium">Close</button>
      </div>

      <div id="order-items-list" class="divide-y divide-stone-100 text-sm"></div>

      <div class="space-y-3 pt-2">
        <div>
          <label class="text-[11px] font-semibold text-stone-500 uppercase">Your Name</label>
          <input type="text" id="cust-name" placeholder="Name" class="w-full mt-1 p-3 border border-stone-200 rounded-xl text-sm outline-none focus:border-stone-800">
        </div>
        <div>
          <label class="text-[11px] font-semibold text-stone-500 uppercase">Phone Number <span class="text-rose-500">*</span></label>
          <input type="tel" id="cust-phone" placeholder="012 345 678" class="w-full mt-1 p-3 border border-stone-200 rounded-xl text-sm outline-none focus:border-stone-800">
        </div>
        <div>
          <label class="text-[11px] font-semibold text-stone-500 uppercase">Delivery Location <span class="text-rose-500">*</span></label>
          <input type="text" id="cust-address" placeholder="Phnom Penh address / Province" class="w-full mt-1 p-3 border border-stone-200 rounded-xl text-sm outline-none focus:border-stone-800">
        </div>
      </div>

      <!-- Payment Method Switcher -->
      <div class="space-y-2 pt-1">
        <label class="text-[11px] font-semibold text-stone-500 uppercase">Payment Method</label>
        <div class="grid grid-cols-2 gap-2">
          <button type="button" id="pay-opt-khqr" onclick="setPaymentMethod('KHQR')" class="p-3 rounded-xl border-2 text-xs font-bold flex flex-col items-center justify-center space-y-1 transition border-stone-900 bg-stone-900 text-white shadow-sm">
            <span class="text-base">💳</span>
            <span>ABA / KHQR (Pay Now)</span>
          </button>
          <button type="button" id="pay-opt-cod" onclick="setPaymentMethod('COD')" class="p-3 rounded-xl border-2 text-xs font-bold flex flex-col items-center justify-center space-y-1 transition border-stone-200 bg-stone-50 text-stone-600 hover:bg-stone-100">
            <span class="text-base">💵</span>
            <span>Cash on Delivery</span>
          </button>
        </div>
      </div>

      <!-- Panel 1: KHQR Payment Details -->
      <div id="khqr-box" class="p-4 bg-[#F8F9FA] rounded-2xl border border-stone-200 text-center space-y-3">
        <div class="flex items-center justify-between px-1">
          <p class="text-xs font-bold uppercase tracking-wider text-stone-800">Transfer Payment</p>
          <span class="text-[10px] font-bold text-sky-800 bg-sky-100 px-2 py-0.5 rounded-full">ABA • KHQR</span>
        </div>

        <div class="bg-white p-3 rounded-xl border border-stone-200 shadow-sm flex items-center justify-between">
          <span class="text-xs text-stone-500 font-medium">Total to transfer:</span>
          <span id="transfer-amount-display" class="text-base font-extrabold text-stone-900">$0.00</span>
        </div>

        <div class="w-48 h-48 mx-auto bg-white p-2.5 rounded-xl shadow-sm border border-stone-200 flex items-center justify-center overflow-hidden">
          <img id="qr-img-tag" src="/static/khqr.png" alt="Piece & Petal KHQR" class="w-full h-full object-contain">
        </div>

        <div class="grid grid-cols-2 gap-2 pt-1">
          <button type="button" onclick="saveOrOpenQr()" class="py-2.5 px-3 bg-white border border-stone-300 hover:bg-stone-50 active:scale-[0.98] rounded-xl text-xs font-semibold text-stone-800 shadow-sm flex items-center justify-center space-x-1.5 transition">
            <span>💾</span>
            <span>Save / View QR</span>
          </button>
          
          <button type="button" id="copy-acc-btn" onclick="copyAccountNumber()" class="py-2.5 px-3 bg-white border border-stone-300 hover:bg-stone-50 active:scale-[0.98] rounded-xl text-xs font-semibold text-stone-800 shadow-sm flex items-center justify-center space-x-1.5 transition">
            <span>📋</span>
            <span id="copy-btn-label">Copy ABA No.</span>
          </button>
        </div>

        <div class="p-2.5 bg-sky-50/70 rounded-xl border border-sky-150 text-[11px] text-sky-900 text-left space-y-1">
          <p class="font-bold flex items-center justify-between">
            <span>ABA: KEVIN KEO</span>
            <span class="font-mono font-bold text-sky-950">010 799 300</span>
          </p>
          <p class="text-[10px] text-sky-700 leading-tight">
            សូមផ្ទេររួចផ្ញើ Slip ចូល Chat បន្ទាប់ពី Submit ការបញ្ជាទិញ។
          </p>
        </div>
      </div>

      <!-- Panel 2: Cash On Delivery Notice -->
      <div id="cod-box" class="hidden p-4 bg-amber-50/80 rounded-2xl border border-amber-200 text-left space-y-2">
        <div class="flex items-center space-x-2">
          <span class="text-lg">📦</span>
          <span class="text-xs font-bold text-amber-950 uppercase tracking-wide">Cash on Delivery (COD)</span>
        </div>
        <p class="text-xs text-amber-900 leading-relaxed">
          បងអាចទូទាត់ប្រាក់សុទ្ធផ្ទាល់នៅពេលដែលអ្នកដឹកជញ្ជូនយកឥវ៉ាន់ទៅដល់ទីតាំងរបស់បង។
        </p>
        <div class="bg-white/80 p-2.5 rounded-xl border border-amber-200/60 text-[11px] text-amber-800 flex items-center justify-between">
          <span>Amount due upon delivery:</span>
          <span id="cod-amount-display" class="font-bold text-stone-900 text-sm">$0.00</span>
        </div>
        <p class="text-[10px] text-amber-700">
          * សេវាដឹកជញ្ជូនរៀបចំតាមរយៈក្រុមហ៊ុនដឹកជញ្ជូនក្នុងរាជធានីភ្នំពេញ និងខេត្ត។
        </p>
      </div>

      <button id="submit-btn" onclick="submitOrder()" class="w-full bg-stone-900 hover:bg-stone-800 text-white py-4 rounded-xl text-sm font-semibold active:scale-[0.98] transition">
        I Have Transferred • Send Slip
      </button>
    </div>
  </div>

  <!-- Success Confirmation Screen -->
  <div id="success-screen" class="fixed inset-0 z-50 bg-[#FAF8F5] hidden flex flex-col items-center justify-center p-6 text-center">
    <div class="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-4 text-2xl font-bold">✓</div>
    <h2 id="success-title" class="text-xl font-bold text-stone-900">Order Submitted!</h2>
    <p id="success-desc" class="text-sm text-stone-600 mt-2 max-w-xs leading-relaxed">
      អរគុណបង! សូមផ្ញើរូបភាព Slip ផ្ទេរប្រាក់ចូលក្នុង Chat នេះ ដើម្បីក្រុមការងារផ្ទៀងផ្ទាត់ និងរៀបចំឥវ៉ាន់ជូនបងភ្លាមៗណា៎ ✨
    </p>
    <button onclick="dismissSuccess()" class="mt-8 w-full max-w-xs py-3.5 bg-stone-900 text-white rounded-xl text-sm font-semibold active:scale-[0.98] transition">
      Back to Chat
    </button>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.expand();
      tg.ready();
    }

    const ABA_ACCOUNT_NUMBER = "010799300";

    let allProducts = [];
    let activeFilter = 'All';
    let cart = {};
    let selectedProduct = null;
    let paymentMethod = 'KHQR'; // 'KHQR' or 'COD'

    document.addEventListener("DOMContentLoaded", () => {
      if (localStorage.getItem('p_phone')) {
        document.getElementById('cust-phone').value = localStorage.getItem('p_phone');
      }
      if (localStorage.getItem('p_address')) {
        document.getElementById('cust-address').value = localStorage.getItem('p_address');
      }
      if (localStorage.getItem('p_name')) {
        document.getElementById('cust-name').value = localStorage.getItem('p_name');
      }
    });

    function setPaymentMethod(method) {
      paymentMethod = method;
      const khqrBtn = document.getElementById('pay-opt-khqr');
      const codBtn = document.getElementById('pay-opt-cod');
      const khqrBox = document.getElementById('khqr-box');
      const codBox = document.getElementById('cod-box');
      const submitBtn = document.getElementById('submit-btn');

      if (method === 'KHQR') {
        khqrBtn.className = "p-3 rounded-xl border-2 text-xs font-bold flex flex-col items-center justify-center space-y-1 transition border-stone-900 bg-stone-900 text-white shadow-sm";
        codBtn.className = "p-3 rounded-xl border-2 text-xs font-bold flex flex-col items-center justify-center space-y-1 transition border-stone-200 bg-stone-50 text-stone-600 hover:bg-stone-100";
        khqrBox.classList.remove('hidden');
        codBox.classList.add('hidden');
        submitBtn.innerText = "I Have Transferred • Send Slip";
      } else {
        codBtn.className = "p-3 rounded-xl border-2 text-xs font-bold flex flex-col items-center justify-center space-y-1 transition border-stone-900 bg-stone-900 text-white shadow-sm";
        khqrBtn.className = "p-3 rounded-xl border-2 text-xs font-bold flex flex-col items-center justify-center space-y-1 transition border-stone-200 bg-stone-50 text-stone-600 hover:bg-stone-100";
        khqrBox.classList.add('hidden');
        codBox.classList.remove('hidden');
        submitBtn.innerText = "Confirm Order (Cash on Delivery)";
      }
    }

    function saveOrOpenQr() {
      const qrUrl = window.location.origin + "/static/khqr.png";
      if (tg && tg.openLink) {
        tg.openLink(qrUrl);
      } else {
        window.open(qrUrl, '_blank');
      }
    }

    function copyAccountNumber() {
      navigator.clipboard.writeText(ABA_ACCOUNT_NUMBER).then(() => {
        const btnLabel = document.getElementById('copy-btn-label');
        const originalText = btnLabel.innerText;
        btnLabel.innerText = "Copied!";
        btnLabel.parentElement.classList.add('bg-emerald-50', 'text-emerald-700', 'border-emerald-300');
        
        setTimeout(() => {
          btnLabel.innerText = originalText;
          btnLabel.parentElement.classList.remove('bg-emerald-50', 'text-emerald-700', 'border-emerald-300');
        }, 2000);
      }).catch(() => {
        alert("Account: " + ABA_ACCOUNT_NUMBER);
      });
    }

    async function fetchCatalog() {
      try {
        const res = await fetch('/api/products');
        allProducts = await res.json();
        renderCategories();
        renderProducts();
      } catch (err) {
        document.getElementById('product-grid').innerHTML = `
          <div class="col-span-2 text-center py-16 text-xs text-rose-500">Catalog sync failed. Pull down to refresh.</div>
        `;
      }
    }

    function renderCategories() {
      const categories = ['All', ...new Set(allProducts.map(p => p.category).filter(Boolean))];
      const catBar = document.getElementById('category-bar');

      catBar.innerHTML = categories.map(cat => {
        const isActive = cat === activeFilter;
        return `
          <button onclick="setCategory('${cat}')" class="whitespace-nowrap px-4 py-1.5 rounded-full text-xs font-semibold border transition ${
            isActive ? 'bg-stone-900 text-white border-stone-900' : 'bg-white text-stone-600 border-stone-200 hover:bg-stone-50'
          }">
            ${cat}
          </button>
        `;
      }).join('');
    }

    function setCategory(cat) {
      activeFilter = cat;
      renderCategories();
      renderProducts();
    }

    function renderProducts() {
      const filtered = activeFilter === 'All' 
        ? allProducts 
        : allProducts.filter(p => p.category.toLowerCase() === activeFilter.toLowerCase());

      const grid = document.getElementById('product-grid');

      if (filtered.length === 0) {
        grid.innerHTML = `<div class="col-span-2 text-center py-16 text-xs text-stone-400">No items available in this category.</div>`;
        return;
      }

      grid.innerHTML = filtered.map(p => {
        const isSoldOut = p.availability?.toLowerCase().includes('sold') || Number(p.price) === 0;

        return `
          <div onclick="openDetail('${p.id}')" class="bg-white rounded-2xl border border-stone-200/70 overflow-hidden flex flex-col justify-between shadow-sm cursor-pointer active:scale-[0.99] transition">
            <div class="aspect-square w-full bg-stone-50 relative overflow-hidden">
              <img src="${p.image}" alt="${p.title}" class="w-full h-full object-cover ${isSoldOut ? 'opacity-40 grayscale' : ''}" onerror="this.src='https://placehold.co/400x400/faf8f5/stone?text=Piece+%26+Petal'">
              ${p.tag ? `
                <span class="absolute top-2 left-2 text-[9px] font-bold uppercase tracking-wider ${isSoldOut ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-white/90 text-stone-800'} backdrop-blur-sm px-2 py-0.5 rounded-md shadow-sm">
                  ${p.tag}
                </span>
              ` : ''}
              <span class="absolute bottom-2 right-2 text-[10px] font-medium bg-black/40 text-white backdrop-blur-md px-1.5 py-0.5 rounded">
                ${p.brand}
              </span>
            </div>
            <div class="p-3.5 space-y-2 flex-1 flex flex-col justify-between">
              <div>
                <p class="text-xs font-semibold text-stone-900 leading-snug line-clamp-2">${p.title}</p>
                <p class="text-xs font-bold text-stone-900 mt-1">$${Number(p.price).toFixed(2)}</p>
              </div>
              <button onclick="event.stopPropagation(); ${isSoldOut ? '' : `changeQty('${p.id}', 1)`}" ${isSoldOut ? 'disabled' : ''} class="w-full py-2 bg-stone-50 hover:bg-stone-100 border border-stone-200 rounded-lg text-xs font-medium text-stone-800 active:scale-[0.97] transition ${isSoldOut ? 'cursor-not-allowed opacity-40' : ''}">
                ${isSoldOut ? 'Sold Out' : '+ Add to Bag'}
              </button>
            </div>
          </div>
        `;
      }).join('');
    }

    function openDetail(id) {
      selectedProduct = allProducts.find(p => p.id === id);
      if (!selectedProduct) return;

      const isSoldOut = selectedProduct.availability?.toLowerCase().includes('sold');

      document.getElementById('p-brand-badge').innerText = selectedProduct.brand || 'Tokyo Import';
      document.getElementById('p-detail-img').src = selectedProduct.image;
      document.getElementById('p-detail-title').innerText = selectedProduct.title;
      document.getElementById('p-detail-price').innerText = `$${Number(selectedProduct.price).toFixed(2)}`;
      document.getElementById('p-detail-desc').innerText = selectedProduct.description || 'Curated Japanese item.';

      document.getElementById('spec-brand').innerText = selectedProduct.brand || '-';
      document.getElementById('spec-category').innerText = selectedProduct.category || '-';
      document.getElementById('spec-size').innerText = selectedProduct.size || '-';
      document.getElementById('spec-avail').innerText = selectedProduct.availability || 'In Stock';

      const addBtn = document.getElementById('p-add-cart-btn');
      const buyBtn = document.getElementById('p-buy-now-btn');

      if (isSoldOut) {
        addBtn.disabled = true;
        buyBtn.disabled = true;
        addBtn.innerText = 'Sold Out';
        buyBtn.innerText = 'Sold Out';
        addBtn.className = 'w-full py-3.5 bg-stone-200 text-stone-400 rounded-xl text-xs font-bold cursor-not-allowed';
        buyBtn.className = 'w-full py-3.5 bg-stone-200 text-stone-400 rounded-xl text-xs font-bold cursor-not-allowed';
      } else {
        addBtn.disabled = false;
        buyBtn.disabled = false;
        addBtn.innerText = 'Add to Cart';
        buyBtn.innerText = 'Place Order Now';
        addBtn.className = 'w-full py-3.5 bg-stone-900 text-white rounded-xl text-xs font-bold active:scale-[0.98] transition';
        buyBtn.className = 'w-full py-3.5 bg-amber-400 text-stone-900 rounded-xl text-xs font-bold active:scale-[0.98] transition';

        addBtn.onclick = () => {
          changeQty(selectedProduct.id, 1);
          closeDetail();
        };

        buyBtn.onclick = () => {
          cart = { [selectedProduct.id]: 1 };
          updateCartBar();
          closeDetail();
          openCheckout();
        };
      }

      document.getElementById('detail-modal').classList.remove('hidden');
    }

    function closeDetail() {
      document.getElementById('detail-modal').classList.add('hidden');
    }

    async function askAboutProduct() {
      if (!selectedProduct) return;
      const userId = tg?.initDataUnsafe?.user?.id;
      const userName = tg?.initDataUnsafe?.user?.first_name || 'Customer';

      try {
        await fetch('/api/inquire', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            customer_name: userName,
            product_title: selectedProduct.title
          })
        });
      } catch (err) {
        console.error(err);
      }

      if (tg) {
        tg.close();
      }
    }

    function changeQty(id, delta) {
      const next = (cart[id] || 0) + delta;
      if (next <= 0) delete cart[id];
      else cart[id] = next;

      updateCartBar();
      if (!document.getElementById('checkout-modal').classList.contains('hidden')) {
        renderOrderItems();
      }
    }

    function updateCartBar() {
      const totalItems = Object.values(cart).reduce((a, b) => a + b, 0);
      let totalPrice = 0;
      for (const [id, qty] of Object.entries(cart)) {
        const prod = allProducts.find(p => p.id === id);
        if (prod) totalPrice += prod.price * qty;
      }

      const bar = document.getElementById('cart-bar');
      if (totalItems > 0) {
        bar.classList.remove('hidden');
        document.getElementById('cart-count-badge').innerText = `${totalItems} items`;
        document.getElementById('cart-total-display').innerText = `$${totalPrice.toFixed(2)}`;
      } else {
        bar.classList.add('hidden');
        closeCheckout();
      }
    }

    function renderOrderItems() {
      const list = document.getElementById('order-items-list');
      let html = '';
      let total = 0;

      for (const [id, qty] of Object.entries(cart)) {
        const p = allProducts.find(prod => prod.id === id);
        if (p) {
          const itemTotal = p.price * qty;
          total += itemTotal;
          html += `
            <div class="py-3 flex justify-between items-center">
              <div class="pr-2 flex-1">
                <p class="font-medium text-stone-800 text-xs">${p.title}</p>
                <p class="text-[11px] text-stone-500 mt-0.5">$${p.price.toFixed(2)} each</p>
              </div>
              <div class="flex items-center space-x-3">
                <div class="flex items-center border border-stone-200 rounded-lg bg-stone-50">
                  <button onclick="changeQty('${p.id}', -1)" class="w-7 h-7 flex items-center justify-center text-stone-600 hover:text-stone-900 font-bold active:bg-stone-200 rounded-l-lg transition">-</button>
                  <span class="w-6 text-center text-xs font-semibold text-stone-800">${qty}</span>
                  <button onclick="changeQty('${p.id}', 1)" class="w-7 h-7 flex items-center justify-center text-stone-600 hover:text-stone-900 font-bold active:bg-stone-200 rounded-r-lg transition">+</button>
                </div>
                <span class="font-semibold text-stone-800 text-xs w-14 text-right">$${itemTotal.toFixed(2)}</span>
              </div>
            </div>
          `;
        }
      }

      html += `
        <div class="pt-3 flex justify-between items-center text-sm font-bold text-stone-900 border-t border-stone-200">
          <span>Subtotal</span>
          <span>$${total.toFixed(2)}</span>
        </div>
      `;
      list.innerHTML = html;

      const amtDisplay = document.getElementById('transfer-amount-display');
      const codDisplay = document.getElementById('cod-amount-display');
      if (amtDisplay) amtDisplay.innerText = `$${total.toFixed(2)}`;
      if (codDisplay) codDisplay.innerText = `$${total.toFixed(2)}`;
    }

    function openCheckout() {
      renderOrderItems();
      document.getElementById('checkout-modal').classList.remove('hidden');
    }

    function closeCheckout() {
      document.getElementById('checkout-modal').classList.add('hidden');
    }

    async function submitOrder() {
      const name = document.getElementById('cust-name').value.trim();
      const phone = document.getElementById('cust-phone').value.trim();
      const address = document.getElementById('cust-address').value.trim();

      let hasError = false;
      const phoneInput = document.getElementById('cust-phone');
      const addressInput = document.getElementById('cust-address');

      if (!phone) {
        phoneInput.classList.add('border-rose-500', 'bg-rose-50/30');
        hasError = true;
      } else {
        phoneInput.classList.remove('border-rose-500', 'bg-rose-50/30');
      }

      if (!address) {
        addressInput.classList.add('border-rose-500', 'bg-rose-50/30');
        hasError = true;
      } else {
        addressInput.classList.remove('border-rose-500', 'bg-rose-50/30');
      }

      if (hasError) return;

      localStorage.setItem('p_phone', phone);
      localStorage.setItem('p_address', address);
      if (name) localStorage.setItem('p_name', name);

      const submitBtn = document.getElementById('submit-btn');
      submitBtn.disabled = true;
      submitBtn.innerText = 'Submitting order...';

      let summaryList = [];
      let total = 0;
      for (const [id, qty] of Object.entries(cart)) {
        const p = allProducts.find(prod => prod.id === id);
        if (p) {
          total += p.price * qty;
          summaryList.push(`• ${qty}x ${p.title} ($${(p.price * qty).toFixed(2)})`);
        }
      }

      const payload = {
        user_id: tg?.initDataUnsafe?.user?.id || null,
        customer_name: name || tg?.initDataUnsafe?.user?.first_name || 'Customer',
        phone: phone,
        address: address,
        total: total,
        payment_method: paymentMethod, // 'KHQR' or 'COD'
        summary: summaryList.join('\n')
      };

      try {
        const res = await fetch('/api/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          cart = {};
          closeCheckout();
          updateCartBar();

          // Customize confirmation message based on payment method
          if (paymentMethod === 'COD') {
            document.getElementById('success-title').innerText = "Order Received (COD)";
            document.getElementById('success-desc').innerHTML = `
              អរគុណបង! ក្រុមការងារបានទទួលការបញ្ជាទិញ (ទូទាត់ប្រាក់ពេលទំនិញទៅដល់) រួចរាល់ហើយ។<br><br>
              យើងខ្ញុំនឹងទាក់ទងបញ្ជាក់ទីតាំង និងជូនដំណឹងមុនពេលចេញដំណើរដឹកជញ្ជូនណា៎ 🚚✨
            `;
          } else {
            document.getElementById('success-title').innerText = "Order Submitted!";
            document.getElementById('success-desc').innerHTML = `
              អរគុណបង! សូមផ្ញើរូបភាព Slip ផ្ទេរប្រាក់ចូលក្នុង Chat នេះ ដើម្បីឱ្យក្រុមការងារផ្ទៀងផ្ទាត់ និងរៀបចំឥវ៉ាន់ជូនបងភ្លាមៗណា៎ ✨
            `;
          }

          document.getElementById('success-screen').classList.remove('hidden');
        } else {
          alert('Failed to submit order. Please message us directly in chat.');
        }
      } catch (e) {
        alert('Network connection error. Please try again.');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = paymentMethod === 'KHQR' ? 'I Have Transferred • Send Slip' : 'Confirm Order (Cash on Delivery)';
      }
    }

    function dismissSuccess() {
      document.getElementById('success-screen').classList.add('hidden');
      if (tg) tg.close();
    }

    fetchCatalog();
  </script>
</body>
</html>
