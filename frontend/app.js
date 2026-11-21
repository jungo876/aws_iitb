/* KagazCheck frontend - vanilla JS, no build step. */
(() => {
  "use strict";

  const API = "";                       // same origin (CloudFront routes /api/* to API Gateway)
  const DOC_ORDER = ["aadhaar", "bank", "marksheet", "income", "caste"];
  const DOC_ICON = { aadhaar: "🪪", bank: "🏦", marksheet: "📜", income: "💰", caste: "📄" };

  const FIELD_ORDER = {
    aadhaar: ["name", "dob", "gender", "aadhaar_last4"],
    bank: ["holder_name", "ifsc", "bank_name", "branch", "account_last4"],
    marksheet: ["name", "father_name", "mother_name", "dob", "board", "year"],
    income: ["name", "father_name", "annual_income", "issue_date", "issuing_authority"],
    caste: ["name", "father_name", "category", "caste", "issue_date"],
  };

  const T = {
    en: {
      nav_insights: "Insights",
      hero_eyebrow: "For scholarship & DBT applicants",
      hero_title: 'Your scholarship shouldn\'t fail because of a <span class="hl">spelling</span>.',
      hero_lead: "Photograph your Aadhaar, bank passbook, marksheet and certificates. In under a minute KagazCheck finds the mismatches that get applications rejected and payments stuck, and tells you exactly how to fix them in your language.",
      cta_start: "Check my documents", cta_sample: "Try with sample documents",
      privacy_short: "Photos are read in memory and never stored. Aadhaar numbers are masked.",
      problem_title: "Why applications fail",
      problem_body: "Scholarship and DBT portals match your details across documents letter by letter. One missing letter, an initial instead of a full name, an old income certificate, or an account not seeded for DBT, and the money doesn't arrive. Students usually find out months later.",
      how1_t: "Pick your scheme", how1_d: "Central or state scholarship or DBT scheme.",
      how2_t: "Snap your documents", how2_d: "AI on AWS reads names, dates, IFSC and income.",
      how3_t: "Get a fix-list", how3_d: "Every problem, why it matters, and the exact steps to fix it. Listen to it in Hindi or share it on WhatsApp.",
      checks_line: "Checks: name spelling, initials & order · date of birth · gender · father's name · income limit · certificate age · IFSC · account in your own name · Aadhaar-DBT seeding",
      scheme_title: "Which scheme are you applying for?",
      scheme_sub: "We use it to know which documents and income limit to check.",
      custom_limit: "Income limit for your scheme (₹ per year), if any",
      limit_note: "Income limits shown are from scheme guidelines. Always confirm the latest limit on scholarships.gov.in or your state portal.",
      back: "Back", next: "Next", review_details: "Review details",
      docs_title: "Add photos of your documents",
      docs_sub: "Place the document flat in good light. Make sure the name and numbers are readable.",
      review_title: "Is this what your documents say?",
      review_sub: "Correct anything we read wrongly. Type it exactly as printed, mistakes included.",
      run_check: "Find problems",
      insights_title: "What is blocking students?",
      insights_sub: "Live, anonymous counts from every check run on KagazCheck. No names, numbers or photos are stored, only which problems were found. Colleges and scholarship cells can use this to run targeted help desks.",
      footer_privacy: "Privacy: photos are processed in memory on AWS (Mumbai region) and deleted immediately. We store only anonymous counts of problem types.",
      footer_disclaimer: "KagazCheck is an independent student project. It is not affiliated with UIDAI, NSP or any government department. Always follow your scheme's official guidelines.",
      doc_aadhaar: "Aadhaar card", doc_bank: "Bank passbook (first page)", doc_marksheet: "10th marksheet",
      doc_income: "Income certificate", doc_caste: "Caste certificate",
      required: "Needed", optional: "Optional",
      add_photo: "Add photo", retake: "Change", type_instead: "Type instead",
      st_empty: "Not added yet", st_reading: "Reading with AI…", st_done: "Read ✓", st_manual: "Will type manually",
      st_error: "Couldn't read. Try a clearer photo or type it.",
      need_one: "Add at least your Aadhaar and bank passbook (or type them).",
      still_reading: "Please wait, still reading your documents…",
      income_limit_label: "Income limit",
      no_limit: "No fixed income limit",
      f_name: "Name", f_holder_name: "Account holder name", f_dob: "Date of birth (DD/MM/YYYY)", f_gender: "Gender",
      f_aadhaar_last4: "Aadhaar last 4 digits", f_ifsc: "IFSC code", f_bank_name: "Bank", f_branch: "Branch",
      f_account_last4: "Account last 4 digits", f_father_name: "Father's name", f_mother_name: "Mother's name",
      f_board: "Board", f_year: "Year of passing", f_annual_income: "Annual family income (₹)",
      f_issue_date: "Date of issue (DD/MM/YYYY)", f_issuing_authority: "Issued by", f_category: "Category", f_caste: "Caste",
      w_type: "This photo looks like a {t}. Please check you added the right document.",
      w_quality: "The photo looks {q}. Please check every value carefully.",
      w_textract: "Read with backup OCR. Please check every value carefully.",
      engine_bedrock: "Read by Amazon Bedrock", engine_textract: "Read by Amazon Textract", engine_mock: "Demo mode", engine_manual: "Typed by you",
      checking: "Checking…",
      verdict_ready: "Looks ready to apply 🎉",
      verdict_almost: "Almost ready. Check a few things",
      verdict_fix_first: "Fix {n} problem(s) before you apply",
      verdict_not_ready: "Not ready: {n} serious problem(s) found",
      score: "readiness", scheme_label: "Scheme", checked: "Documents checked",
      listen: "🔊 Listen", stop: "■ Stop", share_wa: "Share on WhatsApp", print: "Save / Print", again: "Check again",
      edit: "Edit details",
      report_lang: "Report language",
      fix_steps: "How to fix",
      looks_fine: "What looks fine",
      p_name_ok: "Name on {doc} matches Aadhaar", p_dob_ok: "Date of birth matches on Aadhaar and marksheet",
      p_income_ok: "Income ₹{income} is within the ₹{limit} limit", p_income_cert_fresh: "Income certificate is recent ({issue_date})",
      p_ifsc_ok: "IFSC {ifsc} is in a valid format", p_father_ok: "Father's name on {doc} matches marksheet",
      translating: "Translating…", speaking: "Preparing audio…",
      audio_lang_note: "Audio is available in Hindi and English.",
      wa_header: "My KagazCheck document report",
      wa_footer: "Check your own documents free:",
      ins_total: "checks run", ins_blocked: "had a problem that could block payment", ins_top: "most common problem",
      ins_empty: "No checks yet. Be the first!",
      err_generic: "Something went wrong. Please try again.",
      sample_loading: "Loading sample documents of a fictional student, Priyanka…",
    },
    hi: {
      nav_insights: "आँकड़े",
      hero_eyebrow: "स्कॉलरशिप और DBT आवेदकों के लिए",
      hero_title: 'एक <span class="hl">स्पेलिंग</span> की गलती से आपकी स्कॉलरशिप नहीं रुकनी चाहिए।',
      hero_lead: "अपने आधार, बैंक पासबुक, मार्कशीट और प्रमाण पत्रों की फोटो लें। एक मिनट से कम में KagazCheck वे गड़बड़ियाँ ढूँढता है जिनसे आवेदन रिजेक्ट होते हैं और पैसा अटकता है, और आपकी भाषा में बताता है कि उन्हें कैसे ठीक करें।",
      cta_start: "मेरे दस्तावेज़ जाँचें", cta_sample: "सैंपल दस्तावेज़ों से आज़माएँ",
      privacy_short: "फोटो सिर्फ पढ़ी जाती हैं, कभी सेव नहीं होतीं। आधार नंबर छिपा दिया जाता है।",
      problem_title: "आवेदन क्यों फेल होते हैं",
      problem_body: "स्कॉलरशिप और DBT पोर्टल आपके दस्तावेज़ों की जानकारी को अक्षर-दर-अक्षर मिलाते हैं। एक अक्षर छूट जाए, पूरे नाम की जगह initials हों, आय प्रमाण पत्र पुराना हो, या खाता DBT के लिए सीड न हो, तो पैसा नहीं आता। छात्रों को अक्सर महीनों बाद पता चलता है।",
      how1_t: "अपनी योजना चुनें", how1_d: "केंद्र या राज्य की स्कॉलरशिप या DBT योजना।",
      how2_t: "दस्तावेज़ों की फोटो लें", how2_d: "AWS पर AI नाम, तारीख, IFSC और आय पढ़ता है।",
      how3_t: "सुधार की सूची पाएँ", how3_d: "हर समस्या, वह क्यों ज़रूरी है, और ठीक करने के सटीक कदम। हिंदी में सुनें या WhatsApp पर शेयर करें।",
      checks_line: "जाँच: नाम की स्पेलिंग, initials और क्रम · जन्मतिथि · लिंग · पिता का नाम · आय सीमा · प्रमाण पत्र की तारीख · IFSC · खुद के नाम पर खाता · आधार-DBT सीडिंग",
      scheme_title: "आप किस योजना के लिए आवेदन कर रहे हैं?",
      scheme_sub: "इससे हम जानते हैं कि कौन से दस्तावेज़ और आय सीमा जाँचनी है।",
      custom_limit: "आपकी योजना की आय सीमा (₹ प्रति वर्ष), अगर कोई हो",
      limit_note: "दिखाई गई आय सीमाएँ योजना के दिशानिर्देशों से हैं। नवीनतम सीमा हमेशा scholarships.gov.in या अपने राज्य पोर्टल पर जाँचें।",
      back: "पीछे", next: "आगे", review_details: "विवरण देखें",
      docs_title: "अपने दस्तावेज़ों की फोटो जोड़ें",
      docs_sub: "दस्तावेज़ को अच्छी रोशनी में सीधा रखें। नाम और नंबर साफ़ पढ़ने लायक हों।",
      review_title: "क्या आपके दस्तावेज़ों पर यही लिखा है?",
      review_sub: "जो गलत पढ़ा गया हो उसे ठीक करें। बिल्कुल वैसा ही लिखें जैसा छपा है, गलतियों सहित।",
      run_check: "समस्याएँ ढूँढें",
      insights_title: "छात्रों को क्या रोक रहा है?",
      insights_sub: "KagazCheck पर हुई हर जाँच के लाइव, गुमनाम आँकड़े। कोई नाम, नंबर या फोटो सेव नहीं होती, सिर्फ यह कि कौन सी समस्या मिली। कॉलेज और स्कॉलरशिप सेल इससे सही जगह मदद दे सकते हैं।",
      footer_privacy: "गोपनीयता: फोटो AWS (मुंबई रीजन) पर मेमोरी में प्रोसेस होकर तुरंत हट जाती हैं। हम सिर्फ समस्याओं की गुमनाम गिनती रखते हैं।",
      footer_disclaimer: "KagazCheck एक स्वतंत्र छात्र प्रोजेक्ट है। इसका UIDAI, NSP या किसी सरकारी विभाग से कोई संबंध नहीं है। हमेशा अपनी योजना के आधिकारिक दिशानिर्देश मानें।",
      doc_aadhaar: "आधार कार्ड", doc_bank: "बैंक पासबुक (पहला पन्ना)", doc_marksheet: "10वीं की मार्कशीट",
      doc_income: "आय प्रमाण पत्र", doc_caste: "जाति प्रमाण पत्र",
      required: "ज़रूरी", optional: "वैकल्पिक",
      add_photo: "फोटो जोड़ें", retake: "बदलें", type_instead: "खुद लिखें",
      st_empty: "अभी नहीं जोड़ा", st_reading: "AI से पढ़ा जा रहा है…", st_done: "पढ़ लिया ✓", st_manual: "खुद लिखेंगे",
      st_error: "पढ़ नहीं पाए। साफ़ फोटो लें या खुद लिखें।",
      need_one: "कम से कम आधार और बैंक पासबुक जोड़ें (या खुद लिखें)।",
      still_reading: "कृपया रुकें, दस्तावेज़ अभी पढ़े जा रहे हैं…",
      income_limit_label: "आय सीमा",
      no_limit: "कोई तय आय सीमा नहीं",
      f_name: "नाम", f_holder_name: "खाताधारक का नाम", f_dob: "जन्मतिथि (DD/MM/YYYY)", f_gender: "लिंग",
      f_aadhaar_last4: "आधार के आखिरी 4 अंक", f_ifsc: "IFSC कोड", f_bank_name: "बैंक", f_branch: "शाखा",
      f_account_last4: "खाते के आखिरी 4 अंक", f_father_name: "पिता का नाम", f_mother_name: "माता का नाम",
      f_board: "बोर्ड", f_year: "पास होने का वर्ष", f_annual_income: "सालाना पारिवारिक आय (₹)",
      f_issue_date: "जारी होने की तारीख (DD/MM/YYYY)", f_issuing_authority: "जारीकर्ता", f_category: "श्रेणी", f_caste: "जाति",
      w_type: "यह फोटो {t} जैसी लगती है। जाँच लें कि सही दस्तावेज़ जोड़ा है।",
      w_quality: "फोटो {q} लगती है। हर जानकारी ध्यान से जाँचें।",
      w_textract: "बैकअप OCR से पढ़ा गया। हर जानकारी ध्यान से जाँचें।",
      engine_bedrock: "Amazon Bedrock से पढ़ा", engine_textract: "Amazon Textract से पढ़ा", engine_mock: "डेमो मोड", engine_manual: "आपने लिखा",
      checking: "जाँच हो रही है…",
      verdict_ready: "आवेदन के लिए तैयार लगते हैं 🎉",
      verdict_almost: "लगभग तैयार – कुछ चीज़ें जाँच लें",
      verdict_fix_first: "आवेदन से पहले {n} समस्या ठीक करें",
      verdict_not_ready: "अभी तैयार नहीं – {n} गंभीर समस्या मिली",
      score: "तैयारी", scheme_label: "योजना", checked: "जाँचे गए दस्तावेज़",
      listen: "🔊 सुनें", stop: "■ रोकें", share_wa: "WhatsApp पर भेजें", print: "सेव / प्रिंट", again: "फिर से जाँचें",
      edit: "विवरण बदलें",
      report_lang: "रिपोर्ट की भाषा",
      fix_steps: "कैसे ठीक करें",
      looks_fine: "क्या सही है",
      p_name_ok: "{doc} पर नाम आधार से मेल खाता है", p_dob_ok: "आधार और मार्कशीट पर जन्मतिथि एक जैसी है",
      p_income_ok: "आय ₹{income}, ₹{limit} की सीमा के अंदर है", p_income_cert_fresh: "आय प्रमाण पत्र नया है ({issue_date})",
      p_ifsc_ok: "IFSC {ifsc} सही फॉर्मेट में है", p_father_ok: "{doc} पर पिता का नाम मार्कशीट से मेल खाता है",
      translating: "अनुवाद हो रहा है…", speaking: "ऑडियो तैयार हो रहा है…",
      audio_lang_note: "ऑडियो हिंदी और अंग्रेज़ी में उपलब्ध है।",
      wa_header: "मेरी KagazCheck दस्तावेज़ रिपोर्ट",
      wa_footer: "अपने दस्तावेज़ मुफ़्त जाँचें:",
      ins_total: "जाँचें हुईं", ins_blocked: "में ऐसी समस्या थी जो भुगतान रोक सकती थी", ins_top: "सबसे आम समस्या",
      ins_empty: "अभी कोई जाँच नहीं हुई। पहले आप करें!",
      err_generic: "कुछ गड़बड़ हुई। कृपया दोबारा कोशिश करें।",
      sample_loading: "एक काल्पनिक छात्रा, प्रियंका, के सैंपल दस्तावेज़ लोड हो रहे हैं…",
    },
  };

  const ISSUE_SHORT = {
    en: {
      "name_mismatch:bank": "Name on bank account ≠ Aadhaar", "name_mismatch:marksheet": "Name on marksheet ≠ Aadhaar",
      "name_mismatch:income": "Name on income certificate ≠ Aadhaar", "name_mismatch:caste": "Name on caste certificate ≠ Aadhaar",
      bank_not_own_account: "Bank account not in student's name", dob_mismatch: "Date of birth mismatch",
      dob_year_only: "Aadhaar has only year of birth", gender_mismatch: "Gender mismatch",
      father_name_mismatch: "Father's name mismatch", income_over_limit: "Income above scheme limit",
      income_cert_expired: "Income certificate too old", income_cert_old_fy: "Income certificate from last FY",
      income_cert_no_date: "No date on income certificate", ifsc_invalid: "Invalid IFSC", ifsc_missing: "IFSC missing",
      doc_missing: "Required document missing",
    },
    hi: {
      "name_mismatch:bank": "बैंक खाते का नाम ≠ आधार", "name_mismatch:marksheet": "मार्कशीट का नाम ≠ आधार",
      "name_mismatch:income": "आय प्रमाण पत्र का नाम ≠ आधार", "name_mismatch:caste": "जाति प्रमाण पत्र का नाम ≠ आधार",
      bank_not_own_account: "खाता छात्र के नाम पर नहीं", dob_mismatch: "जन्मतिथि अलग",
      dob_year_only: "आधार पर सिर्फ जन्म वर्ष", gender_mismatch: "लिंग अलग",
      father_name_mismatch: "पिता का नाम अलग", income_over_limit: "आय सीमा से ज़्यादा",
      income_cert_expired: "आय प्रमाण पत्र पुराना", income_cert_old_fy: "आय प्रमाण पत्र पिछले साल का",
      income_cert_no_date: "आय प्रमाण पत्र पर तारीख नहीं", ifsc_invalid: "गलत IFSC", ifsc_missing: "IFSC नहीं",
      doc_missing: "ज़रूरी दस्तावेज़ नहीं",
    },
  };

  const REPORT_LANGS = [
    ["en", "English"], ["hi", "हिन्दी"], ["mr", "मराठी"], ["bn", "বাংলা"], ["ta", "தமிழ்"], ["te", "తెలుగు"],
    ["gu", "ગુજરાતી"], ["kn", "ಕನ್ನಡ"], ["ml", "മലയാളം"], ["pa", "ਪੰਜਾਬੀ"], ["or", "ଓଡ଼ିଆ"], ["ur", "اردو"],
  ];

  const FALLBACK_SCHEMES = [
    { id: "pms_sc", name: "Post-Matric Scholarship for SC Students", name_hi: "अनुसूचित जाति के छात्रों के लिए पोस्ट-मैट्रिक स्कॉलरशिप", income_limit: 250000, required: ["aadhaar", "bank", "marksheet", "income", "caste"] },
    { id: "other", name: "Other / State scholarship or DBT scheme", name_hi: "अन्य / राज्य स्कॉलरशिप या DBT योजना", income_limit: null, required: ["aadhaar", "bank"] },
  ];

  const state = {
    lang: "en",
    schemes: [],
    scheme: null,
    incomeLimit: "",
    docs: {},          // type -> {status, thumb, fields, engine, detected_type, quality, type_mismatch}
    report: null,
    reportLang: "en",
    translations: {},  // lang -> {issues:[{title,why,fix}], verdict}
    audio: null,
  };

  // ------------------------------------------------------------ utils
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const t = (k, p = {}) => (T[state.lang][k] ?? T.en[k] ?? k).replace(/\{(\w+)\}/g, (_, x) => p[x] ?? "");
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmtINR = (n) => Number(n).toLocaleString("en-IN");

  function toast(msg, ms = 3200) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.remove("show"), ms);
  }

  async function api(path, body) {
    const opts = body === undefined ? {} : { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) };
    const res = await fetch(API + path, opts);
    let data = {};
    try { data = await res.json(); } catch { /* ignore */ }
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }

  /** Resize + re-encode to JPEG so uploads are small (~200-400 KB) and EXIF is stripped. */
  async function compressImage(blob, maxSide = 1600, quality = 0.85) {
    let bmp;
    try {
      bmp = await createImageBitmap(blob, { imageOrientation: "from-image" });
    } catch {
      bmp = await new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = URL.createObjectURL(blob);
      });
    }
    const w = bmp.width, h = bmp.height;
    const scale = Math.min(1, maxSide / Math.max(w, h));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(w * scale);
    canvas.height = Math.round(h * scale);
    canvas.getContext("2d").drawImage(bmp, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", quality);
  }

  // ------------------------------------------------------------ i18n
  function applyLang() {
    document.documentElement.lang = state.lang;
    document.body.classList.toggle("lang-hi", state.lang === "hi");
    $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$("[data-i18n-html]").forEach((el) => { el.innerHTML = T[state.lang][el.dataset.i18nHtml]; });
    $$(".lang-toggle button").forEach((b) => b.classList.toggle("active", b.dataset.lang === state.lang));
    try { localStorage.setItem("kc_lang", state.lang); } catch { /* ignore */ }
    renderCurrent();
  }

  // ------------------------------------------------------------ routing
  const SCREENS = ["home", "scheme", "docs", "review", "report", "insights"];
  let current = "home";

  function go(name, push = true) {
    if (name === "docs" && !state.scheme) name = "scheme";
    if (name === "review" && !Object.keys(readyDocs()).length) name = state.scheme ? "docs" : "scheme";
    if (name === "report" && !state.report) name = "home";
    if (current !== name && name !== "docs") $("#toast").classList.remove("show");
    current = name;
    SCREENS.forEach((s) => { $("#screen-" + s).hidden = s !== name; });
    if (push && location.hash.slice(1) !== name) history.pushState(null, "", name === "home" ? location.pathname : "#" + name);
    renderCurrent();
    window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  }

  function renderCurrent() {
    ({ scheme: renderSchemes, docs: renderDocs, review: renderReview, report: renderReport, insights: renderInsights }[current] || (() => {}))();
  }

  // ------------------------------------------------------------ scheme
  function schemeName(s) { return state.lang === "hi" ? s.name_hi : s.name; }

  function renderSchemes() {
    const list = $("#scheme-list");
    list.innerHTML = state.schemes.map((s) => `
      <label class="choice ${state.scheme === s.id ? "selected" : ""}">
        <input type="radio" name="scheme" value="${s.id}" ${state.scheme === s.id ? "checked" : ""}>
        <span><span class="title">${esc(schemeName(s))}</span><br>
        <span class="meta">${s.income_limit ? `${t("income_limit_label")}: ₹${fmtINR(s.income_limit)}` : t("no_limit")}
        · ${s.required.map((d) => t("doc_" + d)).join(", ")}</span></span>
      </label>`).join("");
    $$("input[name=scheme]", list).forEach((r) => r.addEventListener("change", () => {
      state.scheme = r.value;
      renderSchemes();
    }));
    $("#custom-limit").hidden = state.scheme !== "other";
    $("#income-limit").value = state.incomeLimit;
  }

  // ------------------------------------------------------------ documents
  function requiredDocs() {
    const s = state.schemes.find((x) => x.id === state.scheme);
    return s ? s.required : ["aadhaar", "bank"];
  }

  function readyDocs() {
    const out = {};
    for (const [k, d] of Object.entries(state.docs)) if (d.status === "done" || d.status === "manual") out[k] = d;
    return out;
  }

  function renderDocs() {
    const req = requiredDocs();
    $("#doc-list").innerHTML = DOC_ORDER.map((type) => {
      const d = state.docs[type] || { status: "empty" };
      const statusText = {
        empty: t("st_empty"), reading: `<span class="spinner"></span>${t("st_reading")}`, done: t("st_done"),
        manual: t("st_manual"), error: esc(d.error || t("st_error")),
      }[d.status];
      const statusCls = { done: "ok", error: "err", manual: "ok" }[d.status] || "";
      const warn = d.status === "done" && (d.type_mismatch || (d.quality && d.quality !== "good")) ? " warn" : "";
      return `
      <div class="doc" data-type="${type}">
        <div class="thumb" style="${d.thumb ? `background-image:url('${d.thumb}')` : ""}">${d.thumb ? "" : DOC_ICON[type]}</div>
        <div>
          <div class="name">${t("doc_" + type)}<span class="${req.includes(type) ? "req" : "opt"}">${req.includes(type) ? t("required") : t("optional")}</span></div>
          <div class="status ${statusCls}${warn}">${statusText}</div>
        </div>
        <div class="btns">
          <label class="btn small ${d.status === "empty" || d.status === "error" ? "primary" : "ghost"}">
            📷 ${d.thumb ? t("retake") : t("add_photo")}
            <input type="file" accept="image/*" data-file="${type}">
          </label>
          ${d.status === "empty" || d.status === "error" ? `<button class="btn small ghost" data-manual="${type}">✍️ ${t("type_instead")}</button>` : ""}
        </div>
      </div>`;
    }).join("");
    $$("input[data-file]").forEach((inp) => inp.addEventListener("change", () => {
      if (inp.files && inp.files[0]) handleFile(inp.dataset.file, inp.files[0]);
    }));
    $$("button[data-manual]").forEach((b) => b.addEventListener("click", () => {
      state.docs[b.dataset.manual] = { status: "manual", engine: "manual", fields: {} };
      renderDocs();
    }));
  }

  async function handleFile(type, blob) {
    state.docs[type] = { status: "reading" };
    renderCurrent();
    try {
      const dataUrl = await compressImage(blob);
      state.docs[type].thumb = dataUrl;
      renderCurrent();
      const r = await api("/api/extract", { doc_type: type, image: dataUrl });
      state.docs[type] = { ...state.docs[type], status: "done", fields: r.fields || {}, engine: r.engine,
        detected_type: r.detected_type, quality: r.quality, type_mismatch: r.type_mismatch };
    } catch (e) {
      state.docs[type] = { ...state.docs[type], status: "error", error: e.message && e.message.length < 140 ? e.message : null };
    }
    renderCurrent();
  }

  // ------------------------------------------------------------ review
  function renderReview() {
    const docs = readyDocs();
    $("#review-list").innerHTML = DOC_ORDER.filter((x) => docs[x]).map((type) => {
      const d = docs[type];
      const warns = [];
      if (d.type_mismatch && d.detected_type) warns.push(t("w_type", { t: d.detected_type === "other" ? "different document" : t("doc_" + d.detected_type) }));
      if (d.quality && d.quality !== "good") warns.push(t("w_quality", { q: d.quality }));
      if (d.engine === "textract") warns.push(t("w_textract"));
      return `
      <div class="card review-doc">
        <h3><span>${DOC_ICON[type]} ${t("doc_" + type)}</span><span class="engine">${t("engine_" + (d.engine || "manual"))}</span></h3>
        ${warns.map((w) => `<div class="warnbox">⚠️ ${esc(w)}</div>`).join("")}
        <div class="review-grid">
          ${FIELD_ORDER[type].map((f) => `
            <div class="field">
              <label for="f-${type}-${f}">${t("f_" + f)}</label>
              <input id="f-${type}-${f}" data-doc="${type}" data-field="${f}" value="${esc(d.fields?.[f] ?? "")}" autocomplete="off"
                ${/last4/.test(f) ? 'inputmode="numeric" maxlength="4"' : ""}>
            </div>`).join("")}
        </div>
      </div>`;
    }).join("");
    $$("#review-list input").forEach((inp) => inp.addEventListener("input", () => {
      const d = state.docs[inp.dataset.doc];
      d.fields = d.fields || {};
      d.fields[inp.dataset.field] = inp.value;
    }));
  }

  async function runCheck() {
    const btn = $("#btn-check");
    const docs = {};
    for (const [k, d] of Object.entries(readyDocs())) docs[k] = d.fields || {};
    btn.disabled = true;
    btn.textContent = t("checking");
    try {
      state.report = await api("/api/check", { scheme: state.scheme, docs, income_limit: state.scheme === "other" ? state.incomeLimit : null });
      state.translations = {};
      state.reportLang = state.lang;
      go("report");
    } catch (e) {
      toast(e.message || t("err_generic"));
    } finally {
      btn.disabled = false;
      btn.textContent = t("run_check");
    }
  }

  // ------------------------------------------------------------ report
  function verdictText(lang) {
    const r = state.report;
    const L = T[lang] ? lang : "en";
    const n = r.verdict === "not_ready" ? r.issues.filter((i) => i.severity === "critical").length || r.blocking : r.blocking;
    return T[L]["verdict_" + r.verdict].replace("{n}", n);
  }

  function issueText(i, idx) {
    const L = state.reportLang;
    if (L === "en" || L === "hi") return i.text[L];
    const tr = state.translations[L];
    return tr ? tr.issues[idx] : i.text.en;
  }

  function nameDiff(issue) {
    if (issue.code !== "name_mismatch") return "";
    const details = issue.params.details || [];
    const bad = new Set(details.flatMap((d) => [d.expected, d.found]).filter(Boolean));
    const mark = (name, tag) => esc(name).toUpperCase().split(/\s+/).map((w) => (bad.has(w.replace(/[^A-Z]/g, "")) ? `<${tag}>${w}</${tag}>` : w)).join(" ");
    const L = state.reportLang === "hi" ? "hi" : "en";
    return `<div class="diff">${T[L].doc_aadhaar}: ${mark(issue.params.ref, "ins")}<br>${T[L]["doc_" + issue.params.doc]}: ${mark(issue.params.found, "del")}</div>`;
  }

  function passedText(p) {
    const L = state.reportLang === "hi" ? "hi" : "en";
    let doc = p.doc ? T[L]["doc_" + p.doc] : "";
    if (L === "en" && doc && !/^(Aadhaar|10th)/.test(doc)) doc = doc.charAt(0).toLowerCase() + doc.slice(1);
    if (L === "en" && doc) doc = "the " + doc;
    return T[L]["p_" + p.code].replace(/\{(\w+)\}/g, (_, k) => (k === "doc" ? doc : p[k] ?? ""));
  }

  function renderReport() {
    const r = state.report;
    if (!r) return;
    const L = state.reportLang;
    const scheme = state.schemes.find((s) => s.id === r.scheme.id) || r.scheme;
    const color = { ready: "var(--ok)", almost: "var(--med)", fix_first: "var(--high)", not_ready: "var(--crit)" }[r.verdict];
    const fixLabel = (T[L] || T.en).fix_steps;
    const tr = state.translations[L];
    const verdict = L === "en" || L === "hi" ? verdictText(L) : (tr ? tr.verdict : verdictText("en"));

    $("#report").innerHTML = `
      <div class="card">
        <div class="summary">
          <div class="ring" style="--p:${r.score};--c:${color}"><div><span><b>${r.score}</b><small>/100 ${t("score")}</small></span></div></div>
          <div>
            <p class="verdict ${r.verdict}">${esc(verdict)}</p>
            <div class="muted">${t("scheme_label")}: <b>${esc(schemeName(scheme))}</b></div>
            <div class="muted">${t("checked")}: ${r.checked_docs.map((d) => t("doc_" + d)).join(", ")}</div>
          </div>
        </div>
        <div class="toolbar">
          <label class="sr" for="report-lang" style="font-weight:600;font-size:.9rem">${t("report_lang")}</label>
          <select id="report-lang">${REPORT_LANGS.map(([c, n]) => `<option value="${c}" ${c === L ? "selected" : ""}>${n}</option>`).join("")}</select>
          <button class="btn small ghost" id="btn-listen">${state.audio ? t("stop") : t("listen")}</button>
          <button class="btn small wa" id="btn-wa">${t("share_wa")}</button>
          <button class="btn small ghost" id="btn-print">${t("print")}</button>
        </div>
      </div>
      <div id="issues">
        ${r.issues.map((i, idx) => {
          const x = issueText(i, idx);
          return `
          <article class="issue ${i.severity}">
            <div class="head"><span class="dot">${esc(x.severity_label || i.text.en.severity_label)}</span><h3>${esc(x.title)}</h3></div>
            <div class="body">
              ${nameDiff(i)}
              <p class="why">${esc(x.why)}</p>
              <div class="fixlabel">${esc(fixLabel)}</div>
              <ol>${x.fix.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>
            </div>
          </article>`;
        }).join("")}
      </div>
      ${r.passed && r.passed.length ? `<div class="good"><b>✅ ${(T[L] || T.en).looks_fine}</b><ul>${r.passed.map((p) => `<li>${esc(passedText(p))}</li>`).join("")}</ul></div>` : ""}
      <div class="actions">
        <button class="btn ghost" id="btn-edit">${t("edit")}</button>
        <button class="btn primary" id="btn-again">${t("again")}</button>
      </div>`;

    $("#report-lang").addEventListener("change", (e) => setReportLang(e.target.value));
    $("#btn-listen").addEventListener("click", listen);
    $("#btn-wa").addEventListener("click", shareWhatsApp);
    $("#btn-print").addEventListener("click", () => window.print());
    $("#btn-edit").addEventListener("click", () => go("review"));
    $("#btn-again").addEventListener("click", () => { state.docs = {}; state.report = null; go("scheme"); });
  }

  async function setReportLang(L) {
    stopAudio();
    if (L !== "en" && L !== "hi" && !state.translations[L]) {
      toast(t("translating"), 8000);
      const r = state.report;
      const flat = [verdictText("en")];
      r.issues.forEach((i) => flat.push(i.text.en.severity_label, i.text.en.title, i.text.en.why, ...i.text.en.fix));
      try {
        const out = (await api("/api/translate", { texts: flat, target: L })).texts;
        let k = 1;
        state.translations[L] = {
          verdict: out[0],
          issues: r.issues.map((i) => {
            const o = { severity_label: out[k++], title: out[k++], why: out[k++] };
            o.fix = i.text.en.fix.map(() => out[k++]);
            return o;
          }),
        };
        toast("✓", 800);
      } catch (e) {
        toast(e.message || t("err_generic"));
        L = "en";
      }
    }
    state.reportLang = L;
    renderReport();
  }

  function stopAudio() {
    if (state.audio) { state.audio.pause(); state.audio = null; }
  }

  async function listen() {
    if (state.audio) { stopAudio(); renderReport(); return; }
    const voiceLang = state.reportLang === "en" ? "en" : "hi";
    if (!["en", "hi"].includes(state.reportLang)) toast(t("audio_lang_note"));
    const r = state.report;
    const parts = [verdictText(voiceLang)];
    r.issues.forEach((i, n) => {
      const x = i.text[voiceLang];
      parts.push(`${n + 1}. ${x.title}. ${x.fix.join(" ")}`);
    });
    const btn = $("#btn-listen");
    btn.disabled = true;
    btn.textContent = t("speaking");
    try {
      const res = await api("/api/speak", { text: parts.join("\n").slice(0, 2800), lang: voiceLang });
      if (!res.audio) throw new Error("Audio unavailable");
      const a = new Audio("data:audio/mpeg;base64," + res.audio);
      state.audio = a;
      a.addEventListener("ended", () => { state.audio = null; if (current === "report") renderReport(); });
      await a.play();
    } catch (e) {
      state.audio = null;
      toast(e.message || t("err_generic"));
    }
    renderReport();
  }

  function shareWhatsApp() {
    const r = state.report;
    const L = state.reportLang;
    const H = T[L] || T.en;
    const lines = [`*${H.wa_header}*`, verdictText(L === "hi" ? "hi" : "en"), ""];
    if (L !== "en" && L !== "hi" && state.translations[L]) lines[1] = state.translations[L].verdict;
    r.issues.forEach((i, idx) => {
      const x = issueText(i, idx);
      lines.push(`${idx + 1}. *${x.title}*`);
      x.fix.forEach((s) => lines.push(`   • ${s}`));
      lines.push("");
    });
    lines.push(`${H.wa_footer} ${location.origin}`);
    window.open("https://wa.me/?text=" + encodeURIComponent(lines.join("\n")), "_blank", "noopener");
  }

  // ------------------------------------------------------------ insights
  async function renderInsights() {
    const box = $("#insights");
    box.innerHTML = `<p class="muted"><span class="spinner"></span></p>`;
    try {
      const s = await api("/api/stats");
      if (!s.total) { box.innerHTML = `<p class="card">${t("ins_empty")}</p>`; return; }
      const blocked = (s.verdicts.fix_first || 0) + (s.verdicts.not_ready || 0);
      const issues = Object.entries(s.issues).sort((a, b) => b[1] - a[1]);
      const label = (k) => ISSUE_SHORT[state.lang][k] || ISSUE_SHORT.en[k] || k;
      const max = issues.length ? issues[0][1] : 1;
      box.innerHTML = `
        <div class="kpis">
          <div class="kpi"><b>${fmtINR(s.total)}</b><small>${t("ins_total")}</small></div>
          <div class="kpi"><b>${Math.round((100 * blocked) / s.total)}%</b><small>${t("ins_blocked")}</small></div>
          <div class="kpi"><b style="font-size:1.05rem">${issues.length ? esc(label(issues[0][0])) : "–"}</b><small>${t("ins_top")}</small></div>
        </div>
        <div class="card bars">
          ${issues.map(([k, n]) => `
            <div class="bar-row">
              <div class="lbl"><span>${esc(label(k))}</span><b>${Math.round((100 * n) / s.total)}%</b></div>
              <div class="track"><div class="fill" style="width:${(100 * n) / max}%"></div></div>
            </div>`).join("")}
        </div>`;
    } catch (e) {
      box.innerHTML = `<p class="card">${esc(t("err_generic"))}</p>`;
    }
  }

  // ------------------------------------------------------------ sample flow
  async function trySample() {
    toast(t("sample_loading"), 4000);
    state.scheme = "pms_sc";
    state.docs = {};
    state.report = null;
    go("docs");
    await Promise.all(DOC_ORDER.map(async (type) => {
      try {
        const blob = await (await fetch(`samples/${type}.jpg`)).blob();
        await handleFile(type, blob);
      } catch {
        state.docs[type] = { status: "error" };
        renderCurrent();
      }
    }));
  }

  // ------------------------------------------------------------ wire up
  async function init() {
    let saved = null;
    try { saved = localStorage.getItem("kc_lang"); } catch { /* ignore */ }
    state.lang = saved || ((navigator.language || "").toLowerCase().startsWith("hi") ? "hi" : "en");
    try { state.schemes = (await api("/api/schemes")).schemes; } catch { state.schemes = FALLBACK_SCHEMES; }

    document.addEventListener("click", (e) => {
      const el = e.target.closest("[data-go]");
      if (el) { e.preventDefault(); go(el.dataset.go); }
    });
    $$(".lang-toggle button").forEach((b) => b.addEventListener("click", () => { state.lang = b.dataset.lang; if (state.reportLang === "en" || state.reportLang === "hi") state.reportLang = state.lang; applyLang(); }));
    $("#btn-sample").addEventListener("click", trySample);
    $("#income-limit").addEventListener("input", (e) => { state.incomeLimit = e.target.value; });
    $("#btn-scheme-next").addEventListener("click", () => {
      if (!state.scheme) { toast(t("scheme_title")); return; }
      go("docs");
    });
    $("#btn-docs-next").addEventListener("click", () => {
      if (Object.values(state.docs).some((d) => d.status === "reading")) { toast(t("still_reading")); return; }
      const ready = readyDocs();
      if (!ready.aadhaar && !ready.marksheet) { toast(t("need_one")); return; }
      if (Object.keys(ready).length < 2) { toast(t("need_one")); return; }
      go("review");
    });
    $("#btn-check").addEventListener("click", runCheck);
    window.addEventListener("popstate", () => go(location.hash.slice(1) || "home", false));

    applyLang();
    const start = location.hash.slice(1);
    go(SCREENS.includes(start) ? start : "home", false);
  }

  init();
})();
