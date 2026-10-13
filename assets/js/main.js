(() => {
  "use strict";

  // Shop hours, keyed by JS weekday (0 = Sunday). [open, close] in 24h.
  const HOURS = { 1: [9, 17], 4: [9, 17], 5: [9, 18], 6: [9, 17] };
  const TZ = "America/New_York";
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];

  /* ---------- Header ---------- */
  const header = $("[data-header]");
  const menuBtn = $("[data-menu-btn]");
  const menu = $("[data-menu]");

  const onScroll = () => header.classList.toggle("is-solid", window.scrollY > 24);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  const setMenu = (open) => {
    menu.hidden = !open;
    menuBtn.setAttribute("aria-expanded", String(open));
    header.classList.toggle("is-open", open);
    $("use", menuBtn).setAttribute("href", open ? "#i-close" : "#i-menu");
  };
  menuBtn.addEventListener("click", () => setMenu(menu.hidden));
  menu.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { setMenu(false); menuBtn.focus(); } });
  window.matchMedia("(min-width: 961px)").addEventListener("change", (e) => { if (e.matches) setMenu(false); });

  // Highlight the nav link for the section in view.
  const navLinks = $$(".nav a");
  const sections = navLinks.map((a) => $(a.getAttribute("href"))).filter(Boolean);
  if ("IntersectionObserver" in window && sections.length) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        navLinks.forEach((a) => {
          if (a.getAttribute("href") === "#" + en.target.id) a.setAttribute("aria-current", "true");
          else a.removeAttribute("aria-current");
        });
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    sections.forEach((s) => spy.observe(s));
  }

  /* ---------- Open / closed status ---------- */
  const fmtHour = (h) => (h === 12 ? "12pm" : h > 12 ? `${h - 12}pm` : `${h}am`);

  function shopNow() {
    const parts = Object.fromEntries(
      new Intl.DateTimeFormat("en-US", { timeZone: TZ, weekday: "short", hour: "numeric", minute: "numeric", hourCycle: "h23" })
        .formatToParts(new Date()).map((p) => [p.type, p.value])
    );
    const day = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(parts.weekday);
    return { day, mins: Number(parts.hour) * 60 + Number(parts.minute) };
  }

  function statusText() {
    const { day, mins } = shopNow();
    const today = HOURS[day];
    if (today) {
      const [o, c] = today;
      if (mins >= o * 60 && mins < c * 60) return { label: "Open now", rest: `until ${fmtHour(c)} today` };
      if (mins < o * 60) return { label: "Closed", rest: `opens today at ${fmtHour(o)}` };
    }
    for (let i = 1; i <= 7; i++) {
      const d = (day + i) % 7;
      if (HOURS[d]) return { label: "Closed", rest: `opens ${i === 1 ? "tomorrow" : DAYS[d]} at ${fmtHour(HOURS[d][0])}` };
    }
    return null;
  }

  const status = $("[data-status]");
  const renderStatus = () => {
    const s = statusText();
    if (!s) return;
    status.innerHTML = `<strong>${s.label}</strong>, ${s.rest} · 1207 Kingstown Rd`;
  };
  renderStatus();
  setInterval(renderStatus, 60_000);

  const todayRow = $(`[data-hours] tr[data-day="${shopNow().day}"]`);
  if (todayRow) todayRow.classList.add("is-today");

  /* ---------- Contact form ---------- */
  const form = $("[data-form]");
  const done = $("[data-done]");
  const note = $("[data-form-status]");
  const submitBtn = $("[data-submit]");
  const msgLabel = $("[data-msg-label]");
  const msg = $("#f-msg");

  const TYPES = {
    part:       { subject: "Part inquiry",        label: "Anything else?",                    placeholder: "Quantity, color, budget, how soon you need it…", msgRequired: false },
    service:    { subject: "Service request",     label: "What's going on with the bike?",    placeholder: "Noises, shifting issues, last tune-up, anything we should know…", msgRequired: true },
    suspension: { subject: "Suspension service",  label: "How is it feeling?",                placeholder: "When was it last serviced? Any leaks, harshness or noises?", msgRequired: true },
    build:      { subject: "Custom build",        label: "Tell us about the build",           placeholder: "Type of riding, budget, parts you have in mind…", msgRequired: true },
    other:      { subject: "General question",    label: "Message",                           placeholder: "How can we help?", msgRequired: true },
  };

  const currentType = () => form.elements.inquiry.value || "part";

  function applyType() {
    const type = currentType();
    const cfg = TYPES[type];
    $$("[data-show]", form).forEach((field) => {
      const show = field.dataset.show.split(" ").includes(type);
      field.hidden = !show;
      $$("input, select, textarea", field).forEach((input) => { input.disabled = !show; });
    });
    msgLabel.innerHTML = cfg.label + (cfg.msgRequired ? "" : ' <span class="opt">optional</span>');
    msg.placeholder = cfg.placeholder;
    msg.required = cfg.msgRequired;
    $("#f-part").required = type === "part";
    clearError(msg);
  }

  $$('input[name="inquiry"]', form).forEach((r) => r.addEventListener("change", applyType));
  applyType();

  // Links elsewhere on the page pre-select the inquiry type, and the exact service.
  $$("[data-inquiry]").forEach((link) => link.addEventListener("click", () => {
    const radio = $(`input[name="inquiry"][value="${link.dataset.inquiry}"]`, form);
    if (radio) { radio.checked = true; applyType(); }
    const select = $('[data-show]:not([hidden]) select[name="service_requested"]', form);
    if (select) select.value = link.dataset.service || "";
    if (link.dataset.dropoff) $("#f-when").value = link.dataset.dropoff;
    saveDraft();
  }));

  // Phone becomes required when the customer asks for a call or text.
  const phone = $("#f-phone");
  const replyVia = () => form.elements.reply_via.value || "Email";
  function applyReplyVia() {
    const needPhone = replyVia() !== "Email";
    phone.required = needPhone;
    $("[data-phone-opt]").hidden = needPhone;
    if (!needPhone) clearError(phone);
  }
  $$('input[name="reply_via"]', form).forEach((r) => r.addEventListener("change", applyReplyVia));
  applyReplyVia();

  /* Draft: keep what the customer typed if the page reloads or they switch apps. */
  const DRAFT_KEY = "mbw-form-draft";
  const DRAFT_FIELDS = ["inquiry", "reply_via", "service_requested", "name", "email", "phone", "bike", "part", "suspension_model", "preferred_dropoff", "message"];
  let draftTimer;
  function saveDraft() {
    clearTimeout(draftTimer);
    draftTimer = setTimeout(() => {
      const draft = {};
      DRAFT_FIELDS.forEach((n) => {
        const el = form.elements[n];
        if (!el) return;
        if (n === "service_requested") {
          const visible = $('[data-show]:not([hidden]) select[name="service_requested"]', form);
          if (visible && visible.value) draft[n] = visible.value;
        } else if (el.value) draft[n] = el.value;
      });
      try { localStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); } catch {}
    }, 300);
  }
  function clearDraft() {
    clearTimeout(draftTimer);
    try { localStorage.removeItem(DRAFT_KEY); } catch {}
  }
  function restoreDraft() {
    let draft;
    try { draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null"); } catch { return; }
    if (!draft) return;
    ["inquiry", "reply_via"].forEach((n) => {
      const radio = draft[n] && $(`input[name="${n}"][value="${CSS.escape(draft[n])}"]`, form);
      if (radio) radio.checked = true;
    });
    applyType();
    applyReplyVia();
    DRAFT_FIELDS.forEach((n) => {
      if (n === "inquiry" || n === "reply_via" || !draft[n]) return;
      if (n === "service_requested") {
        const visible = $('[data-show]:not([hidden]) select[name="service_requested"]', form);
        if (visible) visible.value = draft[n];
        return;
      }
      const el = form.elements[n];
      if (el && !el.disabled) el.value = draft[n];
    });
  }
  restoreDraft();
  form.addEventListener("input", saveDraft);
  form.addEventListener("change", saveDraft);

  function setError(input, text) {
    const field = input.closest(".field");
    let err = $(".err", field);
    if (!err) { err = document.createElement("p"); err.className = "err"; err.id = input.id + "-err"; field.append(err); }
    field.classList.add("has-error");
    input.setAttribute("aria-invalid", "true");
    input.setAttribute("aria-describedby", err.id);
    err.textContent = text;
  }
  function clearError(input) {
    const field = input.closest(".field");
    field.classList.remove("has-error");
    input.removeAttribute("aria-invalid");
    const err = $(".err", field);
    if (err) err.textContent = "";
  }

  function validate() {
    let first = null;
    $$("input, textarea", form).forEach((input) => {
      if (input.disabled || input.type === "hidden" || input.type === "radio" || input.type === "checkbox") return;
      clearError(input);
      const v = input.value.trim();
      let problem = "";
      if (input.required && !v) {
        problem = input.id === "f-name" ? "Please enter your name."
          : input.id === "f-email" ? "Please enter your email so we can reply."
          : input.id === "f-part" ? "Tell us which part you're after."
          : input.id === "f-phone" ? `Add a phone number so we can ${replyVia().toLowerCase()} you.`
          : "Please add a few details.";
      } else if (input.type === "email" && v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
        problem = "That email doesn't look right.";
      }
      if (problem) { setError(input, problem); first ??= input; }
    });
    if (first) first.focus();
    return !first;
  }

  // Clear an error as soon as the user fixes it.
  form.addEventListener("input", (e) => {
    if (e.target.closest(".field.has-error") && e.target.value.trim()) clearError(e.target);
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    note.textContent = "";
    note.classList.remove("is-error");
    if (!validate()) return;

    const data = Object.fromEntries(new FormData(form));
    delete data.redirect;
    const cfg = TYPES[currentType()];
    data.subject = `${cfg.subject} from ${data.name}`;
    data.inquiry = cfg.subject;

    if (!data.access_key || data.access_key.startsWith("YOUR_")) {
      note.textContent = "The form isn't connected yet. Please call 401-218-0029.";
      note.classList.add("is-error");
      return;
    }

    submitBtn.classList.add("is-loading");
    $(".btn-label", submitBtn).textContent = "Sending…";
    try {
      const res = await fetch(form.action, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || json.success === false) throw new Error(json.message || "Request failed");

      $("[data-done-msg]").textContent = doneMessage(data);
      clearDraft();
      form.hidden = true;
      done.hidden = false;
      done.focus();
      form.reset();
      applyType();
      applyReplyVia();
    } catch {
      note.textContent = "Something went wrong sending your message. Please try again or call 401-218-0029.";
      note.classList.add("is-error");
    } finally {
      submitBtn.classList.remove("is-loading");
      $(".btn-label", submitBtn).textContent = "Send message";
    }
  });

  // Tell the customer when to actually expect a reply, based on shop hours.
  function nextReply() {
    const { day, mins } = shopNow();
    const today = HOURS[day];
    if (today && mins < today[1] * 60 - 30) return { when: "today", closed: mins < today[0] * 60 };
    for (let i = 1; i <= 7; i++) {
      const d = (day + i) % 7;
      if (HOURS[d]) return { when: i === 1 ? "tomorrow" : `on ${DAYS[d]}`, closed: true };
    }
    return { when: "soon", closed: true };
  }

  function doneMessage(data) {
    const how = data.reply_via === "Call" ? `call you at ${data.phone}`
      : data.reply_via === "Text" ? `text you at ${data.phone}`
      : `email you at ${data.email}`;
    const { when, closed } = nextReply();
    if (when === "today" && !closed) return `Thanks, ${data.name}. We'll ${how} later today.`;
    if (when === "today") return `Thanks, ${data.name}. We'll ${how} once the shop opens today.`;
    return `Thanks, ${data.name}. The shop is closed right now, so we'll ${how} ${when}.`;
  }

  $("[data-reset]").addEventListener("click", () => {
    done.hidden = true;
    form.hidden = false;
    $("#f-name").focus();
  });

  /* ---------- Phone quick bar ---------- */
  // Hide the bar while typing (keyboard is up) and while the contact form is on screen.
  const quickbar = $("[data-quickbar]");
  let typing = false, formVisible = false;
  const syncBar = () => quickbar.classList.toggle("is-hidden", typing || formVisible);
  document.addEventListener("focusin", (e) => { typing = e.target.matches("input, textarea, select"); syncBar(); });
  document.addEventListener("focusout", () => { typing = false; syncBar(); });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(([en]) => { formVisible = en.isIntersecting; syncBar(); }, { threshold: 0.15 })
      .observe($("#contact"));
  }

  /* ---------- Misc ---------- */
  $("[data-year]").textContent = new Date().getFullYear();
})();
