/**
 * MediVision AI — Shared Theme Toggle
 * Injects a floating toggle button and applies light/dark mode across all pages.
 */
(function () {
  // ── Apply saved theme immediately (before paint) ──────────────
  const saved = localStorage.getItem('mv_theme') || 'dark';
  if (saved === 'light') document.documentElement.classList.add('light-mode');

  // ── Inject CSS variables for light mode ───────────────────────
  const style = document.createElement('style');
  style.textContent = `
    /* ===== LIGHT MODE OVERRIDES ===== */
    .light-mode {
      --slate-900: #f0f4f8 !important;
      --slate-800: #ffffff !important;
      --slate-700: #e2e8f0 !important;
      --slate-600: #64748b !important;
      --slate-500: #64748b !important;
      --slate-400: #475569 !important;
      --slate-300: #334155 !important;
      --slate-200: #1e293b !important;
      --teal:      #0d9488 !important;
      --teal-light:#0f766e !important;
      --cyan:      #0891b2 !important;
      --white:     #0f172a !important;
    }

    /* ── Body & Global ── */
    .light-mode body {
      background: #f0f4f8 !important;
      color: #1e293b !important;
    }

    /* ── Navigation (landing page) ── */
    .light-mode nav {
      background: rgba(240,244,248,.92) !important;
      border-bottom-color: rgba(13,148,136,.15) !important;
    }
    .light-mode .nav-links a { color: #475569 !important; }
    .light-mode .nav-links a:hover { color: #0d9488 !important; }
    .light-mode .btn-ghost {
      color: #334155 !important;
      border-color: rgba(13,148,136,.3) !important;
    }
    .light-mode .btn-ghost:hover { color: #0d9488 !important; border-color: #0d9488 !important; }

    /* ── Hero / Landing ── */
    .light-mode h1,
    .light-mode h2,
    .light-mode .hero h1 { color: #0f172a !important; }
    .light-mode .hero-sub,
    .light-mode .section-sub,
    .light-mode .stat-label,
    .light-mode .feature-desc,
    .light-mode .vision-desc { color: #64748b !important; }
    .light-mode .stat-val { color: #0f172a !important; }
    .light-mode .section-title { color: #0f172a !important; }
    .light-mode .hero-bg {
      background: radial-gradient(ellipse 80% 60% at 50% -10%, rgba(13,148,136,.15) 0%, transparent 70%) !important;
    }
    .light-mode .grid-lines { opacity: .04 !important; }

    /* ── Feature cards (landing) ── */
    .light-mode .feature-card {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.12) !important;
      box-shadow: 0 2px 12px rgba(0,0,0,.06);
    }
    .light-mode .feature-card:hover {
      border-color: rgba(13,148,136,.3) !important;
    }
    .light-mode .feature-title { color: #0f172a !important; }
    .light-mode .tag { color: #0d9488 !important; }

    /* ── Vision cards (landing) ── */
    .light-mode .vision-card {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .vision-name { color: #0f172a !important; }

    /* ── Float badges (landing) ── */
    .light-mode .float-badge {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.2) !important;
      color: #334155 !important;
      box-shadow: 0 4px 12px rgba(0,0,0,.08);
    }

    /* ── CTA (landing) ── */
    .light-mode .cta-section {
      background: linear-gradient(135deg, rgba(13,148,136,.08), rgba(6,182,212,.04)) !important;
      border-color: rgba(13,148,136,.15) !important;
    }
    .light-mode .cta-title { color: #0f172a !important; }
    .light-mode .cta-sub { color: #64748b !important; }

    /* ── Footer (landing) ── */
    .light-mode footer {
      color: #64748b !important;
      border-color: rgba(13,148,136,.12) !important;
    }

    /* ── Topbar (medibot, vision, health report) ── */
    .light-mode .topbar {
      background: rgba(240,244,248,.95) !important;
      border-bottom-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .back-btn { color: #0d9488 !important; }
    .light-mode .brand { color: #0f172a !important; }
    .light-mode .bot-status { color: #0d9488 !important; }

    /* ── Sidebar ── */
    .light-mode .sidebar {
      background: #ffffff !important;
      border-right-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .sidebar-brand {
      border-bottom-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .brand-text { color: #0f172a !important; }
    .light-mode .brand-text span { color: #0d9488 !important; }
    .light-mode .nav-group-label { color: #94a3b8 !important; }
    .light-mode .nav-item { color: #475569 !important; }
    .light-mode .nav-item:hover,
    .light-mode .nav-item.active {
      background: rgba(13,148,136,.1) !important;
      color: #0d9488 !important;
    }

    /* ── Cards ── */
    .light-mode .card,
    .light-mode .metric-card,
    .light-mode .doctor-card,
    .light-mode .rx-card {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .card-title,
    .light-mode .doctor-name,
    .light-mode .rx-id,
    .light-mode .rx-doctor { color: #0f172a !important; }
    .light-mode .page-title { color: #0f172a !important; }
    .light-mode .page-sub,
    .light-mode .doctor-meta,
    .light-mode .rx-date { color: #64748b !important; }
    .light-mode .doctor-fee { color: #0f172a !important; }

    /* ── Tabs ── */
    .light-mode .tabs {
      background: rgba(240,244,248,.8) !important;
      border-color: rgba(13,148,136,.15) !important;
    }
    .light-mode .tab { color: #64748b !important; }
    .light-mode .tab.active { background: #0d9488 !important; color: #fff !important; }

    /* ── Input fields ── */
    .light-mode .filter-input,
    .light-mode .field input,
    .light-mode .form-group input,
    .light-mode .form-group select,
    .light-mode #chatInput {
      background: #f8fafc !important;
      border-color: rgba(13,148,136,.2) !important;
      color: #1e293b !important;
    }
    .light-mode .filter-input::placeholder,
    .light-mode .field input::placeholder,
    .light-mode #chatInput::placeholder { color: #94a3b8 !important; }
    .light-mode .filter-input:focus,
    .light-mode .field input:focus,
    .light-mode .form-group input:focus,
    .light-mode .form-group select:focus,
    .light-mode #chatInput:focus { border-color: #0d9488 !important; }
    .light-mode .form-group select option { background: #fff !important; color: #1e293b !important; }

    /* ── Appointment items ── */
    .light-mode .appt-item {
      background: #f8fafc !important;
      border-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .appt-name { color: #0f172a !important; }
    .light-mode .appt-detail { color: #64748b !important; }

    /* ── Slot grid ── */
    .light-mode .slot {
      background: #f1f5f9 !important;
      border-color: rgba(13,148,136,.12) !important;
      color: #334155 !important;
    }
    .light-mode .slot:hover,
    .light-mode .slot.selected {
      background: rgba(13,148,136,.12) !important;
      border-color: #0d9488 !important;
      color: #0d9488 !important;
    }

    /* ── Modal ── */
    .light-mode .modal {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.2) !important;
    }
    .light-mode .modal-title { color: #0f172a !important; }
    .light-mode .modal-sub,
    .light-mode .summary-row { color: #64748b !important; }
    .light-mode .summary-row.total { color: #0f172a !important; }
    .light-mode .booking-summary {
      background: #f1f5f9 !important;
      border-radius: 12px;
    }
    .light-mode .payment-method {
      border-color: rgba(13,148,136,.15) !important;
    }
    .light-mode .payment-method:hover,
    .light-mode .payment-method.selected {
      border-color: #0d9488 !important;
      background: rgba(13,148,136,.08) !important;
    }
    .light-mode .pm-name { color: #334155 !important; }

    /* ── Prescriptions ── */
    .light-mode .rx-header {
      background: rgba(13,148,136,.06) !important;
      border-bottom-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .rx-body { color: #1e293b !important; }
    .light-mode .rx-footer {
      background: #f1f5f9 !important;
    }
    .light-mode .medicine-table th { color: #64748b !important; border-color: rgba(13,148,136,.1) !important; }
    .light-mode .medicine-table td { color: #334155 !important; border-color: rgba(13,148,136,.06) !important; }
    .light-mode .medicine-table td:first-child { color: #0f172a !important; }
    .light-mode .notes-box { background: rgba(245,158,11,.06) !important; }

    /* ── Health Report ── */
    .light-mode .report-header {
      background: linear-gradient(135deg, rgba(13,148,136,.06), rgba(6,182,212,.03)) !important;
      border-color: rgba(13,148,136,.12) !important;
    }
    .light-mode h1 { color: #0f172a !important; }
    .light-mode .report-meta { color: #64748b !important; }
    .light-mode .vital-name { color: #64748b !important; }
    .light-mode .vital-row { border-bottom-color: rgba(13,148,136,.08) !important; }
    .light-mode .recommendation {
      background: #f8fafc !important;
      border-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .rec-title { color: #0f172a !important; }
    .light-mode .rec-text { color: #64748b !important; }
    .light-mode table th { color: #64748b !important; }
    .light-mode table td { color: #334155 !important; }

    /* ── Medibot ── */
    .light-mode .chat-layout { background: #f0f4f8 !important; }
    .light-mode .messages { background: #f0f4f8 !important; }
    .light-mode .msg.bot .msg-bubble {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.12) !important;
      color: #1e293b !important;
    }
    .light-mode .msg.bot .msg-bubble strong { color: #0d9488 !important; }
    .light-mode .msg-time { color: #94a3b8 !important; }
    .light-mode .typing {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .input-area {
      background: rgba(240,244,248,.9) !important;
      border-top-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .quick-replies {
      background: #f0f4f8 !important;
      border-top-color: rgba(13,148,136,.08) !important;
    }
    .light-mode .quick-reply {
      color: #0d9488 !important;
      border-color: rgba(13,148,136,.25) !important;
    }
    .light-mode .quick-reply:hover {
      background: rgba(13,148,136,.1) !important;
    }
    .light-mode .char-hint { color: #94a3b8 !important; }
    .light-mode .chat-sidebar {
      background: #ffffff !important;
      border-left-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .sidebar-section h4 { color: #94a3b8 !important; }
    .light-mode .topic-btn {
      background: #f1f5f9 !important;
      border-color: rgba(13,148,136,.1) !important;
      color: #475569 !important;
    }
    .light-mode .topic-btn:hover {
      background: rgba(13,148,136,.08) !important;
      color: #0d9488 !important;
    }
    .light-mode .disclaimer {
      background: rgba(245,158,11,.05) !important;
      border-color: rgba(245,158,11,.15) !important;
      color: #92400e !important;
    }
    .light-mode .voice-btn {
      background: #e2e8f0 !important;
      color: #334155 !important;
    }

    /* ── Vision / Skin Analysis ── */
    .light-mode .right-panel {
      background: #ffffff !important;
      border-left-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .panel-top { border-bottom-color: rgba(13,148,136,.1) !important; }
    .light-mode .panel-top h3 { color: #0f172a !important; }
    .light-mode .panel-top p { color: #64748b !important; }
    .light-mode .controls { border-top-color: rgba(13,148,136,.12) !important; }
    .light-mode .cb.secondary {
      background: #e2e8f0 !important;
      color: #334155 !important;
    }
    .light-mode .cb.secondary:hover { background: #cbd5e1 !important; }
    .light-mode .score-wrap { border-bottom-color: rgba(13,148,136,.1) !important; }
    .light-mode .score-lbl { color: #64748b !important; }
    .light-mode .section-hd { color: #94a3b8 !important; }
    .light-mode .metric-name { color: #475569 !important; }
    .light-mode .metric-bar-wrap { background: rgba(0,0,0,.07) !important; }
    .light-mode .meta-card {
      background: #f1f5f9 !important;
      border-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .meta-card-lbl { color: #94a3b8 !important; }
    .light-mode .meta-card-val { color: #0f172a !important; }
    .light-mode .sug-item {
      color: #334155 !important;
      border-bottom-color: rgba(13,148,136,.08) !important;
    }
    .light-mode .sug-arrow { color: #0d9488 !important; }
    .light-mode .empty-state { color: #64748b !important; }
    .light-mode .camera-off {
      background: radial-gradient(ellipse at center,rgba(13,148,136,.04) 0%,#f0f4f8 70%) !important;
    }
    .light-mode .camera-off h2 { color: #0f172a !important; }
    .light-mode .camera-off p { color: #64748b !important; }

    /* ── Login page specific ── */
    .light-mode .left { background: #f0f4f8 !important; }
    .light-mode .right {
      background: linear-gradient(160deg, rgba(13,148,136,.06), rgba(6,182,212,.02)) !important;
      border-left-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .login-title { color: #0f172a !important; }
    .light-mode .login-sub { color: #64748b !important; }
    .light-mode .login-footer { color: #64748b !important; }
    .light-mode .login-footer a { color: #0d9488 !important; }
    .light-mode .role-toggle {
      background: rgba(240,244,248,.9) !important;
      border-color: rgba(13,148,136,.15) !important;
    }
    .light-mode .role-btn:not(.active) { color: #64748b !important; }
    .light-mode .role-btn:not(.active):hover {
      color: #0f172a !important;
      background: rgba(13,148,136,.06) !important;
    }
    .light-mode .feat-item {
      background: #f1f5f9 !important;
      border-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .feat-item h4 { color: #0f172a !important; }
    .light-mode .right h2 { color: #0f172a !important; }
    .light-mode .right > p { color: #64748b !important; }
    .light-mode .demo-box {
      background: rgba(13,148,136,.06) !important;
      border-color: rgba(13,148,136,.15) !important;
    }
    .light-mode .demo-cred span:first-child { color: #64748b !important; }
    .light-mode .demo-cred code {
      background: rgba(0,0,0,.06) !important;
      color: #0f172a !important;
    }
    .light-mode .otp-digit,
    .light-mode .otp-input {
      background: #f8fafc !important;
      border-color: rgba(13,148,136,.2) !important;
      color: #0f172a !important;
    }
    .light-mode .otp-hint,
    .light-mode .otp-timer { color: #64748b !important; }
    .light-mode .doctor-mode-bar {
      background: linear-gradient(90deg, rgba(139,92,246,.07), rgba(6,182,212,.04)) !important;
      border-color: rgba(139,92,246,.15) !important;
    }

    /* ── Register page specific ── */
    .light-mode .container { color: #1e293b; }
    .light-mode .logo p { color: #64748b !important; }
    .light-mode .logo h1 { color: #0f172a !important; }
    .light-mode .step-label { color: #64748b !important; }
    .light-mode .section-sub { color: #64748b !important; }
    .light-mode .btn-link { color: #64748b !important; }
    .light-mode .btn-link:hover { color: #0d9488 !important; }
    .light-mode .login-link { color: #64748b !important; }
    .light-mode .login-link a { color: #0d9488 !important; }

    /* ── AI Predict page ── */
    .light-mode .symptom-input,
    .light-mode .form-input,
    .light-mode .autocomplete {
      background: #f8fafc !important;
      color: #1e293b !important;
      border-color: rgba(13,148,136,.2) !important;
    }
    .light-mode .autocomplete-item { color: #334155 !important; background: #fff !important; }
    .light-mode .autocomplete-item:hover { background: rgba(13,148,136,.08) !important; }
    .light-mode .skin-result,
    .light-mode .disease-result {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .disease-name { color: #0f172a !important; }
    .light-mode .log-item { background: #f8fafc !important; }
    .light-mode .log-msg { color: #334155 !important; }
    .light-mode .suggestion-item,
    .light-mode .sug-item { color: #334155 !important; }
    .light-mode .reco-item { color: #334155 !important; }
    .light-mode .prob-bar,
    .light-mode .metric-bar-wrap,
    .light-mode .hr-progress { background: rgba(13,148,136,.08) !important; }
    .light-mode .score-ring-num,
    .light-mode .score-inner { color: #0d9488 !important; }

    /* ── Doctor dashboard ── */
    .light-mode .stat-card {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .notif-item,
    .light-mode .category-card {
      background: #f1f5f9 !important;
      border-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .panel-title { color: #0f172a !important; }
    .light-mode .panel-sub { color: #64748b !important; }

    /* ── Background glow / grid ── */
    .light-mode .bg-glow {
      background: radial-gradient(ellipse 60% 80% at 30% 50%, rgba(13,148,136,.07) 0%, transparent 70%) !important;
    }
    .light-mode .grid {
      opacity: .025 !important;
    }

    /* ── Scrollbar ── */
    .light-mode ::-webkit-scrollbar-thumb {
      background: rgba(13,148,136,.2) !important;
    }

    /* ── Doctor Dashboard specific ── */
    .light-mode .topbar {
      background: rgba(240,244,248,.95) !important;
      border-bottom-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .logo-wrap {
      border-bottom-color: rgba(13,148,136,.12) !important;
      color: #0f172a !important;
    }
    .light-mode .sidebar-bottom {
      border-top-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .doc-name { color: #0f172a !important; }
    .light-mode .stat-box {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.12) !important;
    }
    .light-mode .stat-num { color: #0f172a !important; }
    .light-mode .stat-lbl { color: #64748b !important; }
    .light-mode .apt-card {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.1) !important;
    }
    .light-mode .apt-pname { color: #0f172a !important; }
    .light-mode .apt-pid { color: #94a3b8 !important; }
    .light-mode .apt-meta-cell {
      background: #f1f5f9 !important;
    }
    .light-mode .amc-lbl { color: #94a3b8 !important; }
    .light-mode .amc-val { color: #334155 !important; }
    .light-mode .apt-reason-box {
      background: #f1f5f9 !important;
      color: #475569 !important;
    }
    .light-mode .apt-reason-box b { color: #94a3b8 !important; }
    .light-mode .abt-gray {
      background: #e2e8f0 !important;
      color: #334155 !important;
    }
    .light-mode .abt-gray:hover { background: #cbd5e1 !important; }
    .light-mode .btn-add-med {
      background: #e2e8f0 !important;
      color: #334155 !important;
    }
    .light-mode .btn-add-med:hover { background: #cbd5e1 !important; }
    .light-mode .btn-sm-refresh {
      background: #e2e8f0 !important;
      color: #334155 !important;
    }
    .light-mode .btn-sm-refresh:hover { background: #cbd5e1 !important; }
    .light-mode .meds-title { border-bottom-color: rgba(13,148,136,.1) !important; }
    .light-mode .med-col-hd span { color: #94a3b8 !important; }
    .light-mode .field input,
    .light-mode .field select,
    .light-mode .field textarea,
    .light-mode .med-row input {
      background: #f8fafc !important;
      border-color: rgba(13,148,136,.2) !important;
      color: #1e293b !important;
    }
    .light-mode .field input:focus,
    .light-mode .field select:focus,
    .light-mode .field textarea:focus,
    .light-mode .med-row input:focus { border-color: #0d9488 !important; }
    .light-mode .field select option,
    .light-mode .field input::placeholder,
    .light-mode .field textarea::placeholder {
      background: #fff !important;
      color: #94a3b8 !important;
    }
    .light-mode .empty-wrap { color: #64748b !important; }
    .light-mode .rx-card {
      background: #ffffff !important;
      border-color: rgba(13,148,136,.1) !important;
    }

    /* Toggle button */
    #mv-theme-toggle {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
      width: 46px;
      height: 46px;
      border-radius: 50%;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      box-shadow: 0 4px 16px rgba(0,0,0,.25);
      transition: all .25s cubic-bezier(.4,0,.2,1);
      background: #1e293b;
      color: #fcd34d;
    }
    .light-mode #mv-theme-toggle {
      background: #ffffff;
      color: #0d9488;
      box-shadow: 0 4px 16px rgba(0,0,0,.12);
    }
    #mv-theme-toggle:hover { transform: scale(1.1) rotate(15deg); }
  `;
  document.head.appendChild(style);

  // ── Inject toggle button after DOM ready ─────────────────────
  function injectButton() {
    if (document.getElementById('mv-theme-toggle')) return;
    const btn = document.createElement('button');
    btn.id = 'mv-theme-toggle';
    btn.title = 'Toggle Light / Dark Mode';
    const isDark = !document.documentElement.classList.contains('light-mode');
    btn.textContent = isDark ? '☀️' : '🌙';
    btn.addEventListener('click', () => {
      const isLight = document.documentElement.classList.toggle('light-mode');
      localStorage.setItem('mv_theme', isLight ? 'light' : 'dark');
      btn.textContent = isLight ? '🌙' : '☀️';
    });
    document.body.appendChild(btn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectButton);
  } else {
    injectButton();
  }
})();
