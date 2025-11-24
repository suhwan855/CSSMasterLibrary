// src/components/IframePreview.jsx
import React, { useMemo, useRef, useEffect, useState } from "react";

/* ========= 공통 유틸 ========= */
function isFullHTMLDocument(str = "") {
  const s = (str || "").trim().toLowerCase();
  return s.startsWith("<!doctype") || s.includes("<html") || s.includes("<head") || s.includes("<body");
}
function decodeEntities(s = "") {
  return (s || "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

/* ========= Tailwind 로딩 제어 & 헤드 구성 ========= */
function looksLikeTailwind(html = "") {
  const clsParts = [];
  const re = /class\s*=\s*"(.*?)"/gis;
  let m;
  while ((m = re.exec(html))) clsParts.push(m[1]);
  const classes = clsParts.join(" ");
  return /\b(bg|text|border|shadow|rounded|p|px|py|m|mx|my|flex|grid|gap|justify|items|w|h|min-w|min-h|max-w|max-h|overflow|object|z|inset|top|left|right|bottom|translate|rotate|scale|skew)-[a-z0-9]/i.test(
    classes
  );
}
function buildHeadTags({ code }) {
  const needsTw = looksLikeTailwind(code || "");
  const tags = [];
  if (needsTw) {
    tags.push('<script>window.tailwind = { config: { corePlugins: { preflight: false } } };</script>');
    tags.push('<script src="https://cdn.tailwindcss.com"></script>');
    tags.push(buildLegacyShimCSS());
  }
  tags.push(buildExternalDeps(code || ""));
  return tags.join("\n");
}
function buildLegacyShimCSS() {
  const COLORS = [
    "gray","grey","red","orange","amber","yellow","lime","green","emerald","teal",
    "cyan","sky","blue","indigo","violet","purple","fuchsia","pink","rose"
  ];
  const SHADES = [50,100,200,300,400,500,600,700,800,900];
  const VARS = ["hover","focus","active"];
  const lines = [];
  lines.push("@layer utilities {");
  for (const n of SHADES) {
    lines.push(`.bg-grey-${n} { @apply bg-gray-${n}; }`);
    lines.push(`.text-grey-${n} { @apply text-gray-${n}; }`);
    lines.push(`.border-grey-${n} { @apply border-gray-${n}; }`);
    for (const v of VARS) {
      lines.push(`.${v}\\:bg-grey-${n}:${v} { @apply ${v}:bg-gray-${n}; }`);
      lines.push(`.${v}\\:text-grey-${n}:${v} { @apply ${v}:text-gray-${n}; }`);
      lines.push(`.${v}\\:border-grey-${n}:${v} { @apply ${v}:border-gray-${n}; }`);
    }
  }
  lines.push(".bg-grey { @apply bg-gray-500; }");
  lines.push(".text-grey { @apply text-gray-500; }");
  lines.push(".border-grey { @apply border-gray-500; }");
  for (const v of VARS) {
    lines.push(`.${v}\\:bg-grey:${v} { @apply ${v}:bg-gray-500; }`);
    lines.push(`.${v}\\:text-grey:${v} { @apply ${v}:text-gray-500; }`);
    lines.push(`.${v}\\:border-grey:${v} { @apply ${v}:border-gray-500; }`);
  }
  for (let c of COLORS) {
    const base = c === "grey" ? "gray" : c;
    lines.push(`.bg-${c} { @apply bg-${base}-500; }`);
    lines.push(`.text-${c} { @apply text-${base}-500; }`);
    lines.push(`.border-${c} { @apply border-${base}-500; }`);
    lines.push(`.bg-${c}-light { @apply bg-${base}-400; }`);
    lines.push(`.bg-${c}-dark { @apply bg-${base}-600; }`);
    lines.push(`.text-${c}-light { @apply text-${base}-400; }`);
    lines.push(`.text-${c}-dark { @apply text-${base}-600; }`);
    lines.push(`.border-${c}-light { @apply border-${base}-400; }`);
    lines.push(`.border-${c}-dark { @apply border-${base}-600; }`);
    for (const v of VARS) {
      lines.push(`.${v}\\:bg-${c}:${v} { @apply ${v}:bg-${base}-500; }`);
      lines.push(`.${v}\\:text-${c}:${v} { @apply ${v}:text-${base}-500; }`);
      lines.push(`.${v}\\:border-${c}:${v} { @apply ${v}:border-${base}-500; }`);
      lines.push(`.${v}\\:bg-${c}-light:${v} { @apply ${v}:bg-${base}-400; }`);
      lines.push(`.${v}\\:bg-${c}-dark:${v} { @apply ${v}:bg-${base}-600; }`);
      lines.push(`.${v}\\:text-${c}-light:${v} { @apply ${v}:text-${base}-400; }`);
      lines.push(`.${v}\\:text-${c}-dark:${v} { @apply ${v}:text-${base}-600; }`);
      lines.push(`.${v}\\:border-${c}-light:${v} { @apply ${v}:border-${base}-400; }`);
      lines.push(`.${v}\\:border-${c}-dark:${v} { @apply ${v}:border-${base}-600; }`);
    }
  }
  lines.push(".rounded-0 { @apply rounded-none; }");
  lines.push(".rounded-1 { @apply rounded-sm; }");
  lines.push(".rounded-2 { @apply rounded; }");
  lines.push(".rounded-3 { @apply rounded-lg; }");
  lines.push("}");
  return `<style type="text/tailwindcss">\n${lines.join("\n")}\n</style>`;
}
function buildExternalDeps(html = "") {
  const needsFA = /\bfa[srlb]?-/.test(html) || /font-awesome/i.test(html);
  const needsRemix = /\bri-[\w-]+/.test(html);
  const needsBoxicons = /\bbx[sl]?-[\w-]+/.test(html);
  const needsMaterialSymbols = /\bmaterial-symbols-(?:outlined|rounded|sharp)\b/.test(html);
  const needsPressFont = /press\s*start\s*2p/i.test(html); // ★ Press Start 2P 감지

  const lines = [];
  if (needsFA) lines.push('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" referrerpolicy="no-referrer" />');
  if (needsRemix) lines.push('<link href="https://cdn.jsdelivr.net/npm/remixicon@4.3.0/fonts/remixicon.css" rel="stylesheet">');
  if (needsBoxicons) lines.push('<link href="https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css" rel="stylesheet">');
  if (needsMaterialSymbols) {
    lines.push('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,200..700,0..1,-50..200" />');
    lines.push('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,200..700,0..1,-50..200" />');
    lines.push('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Sharp:opsz,wght,FILL,GRAD@20..48,200..700,0..1,-50..200" />');
  }
  if (needsPressFont) {
    lines.push('<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">');
  }
  return lines.join("\n");
}
function extractLinksFrom(html = "") {
  const links = [];
  const re = /<link[^>]+>/gi;
  let m;
  while ((m = re.exec(html))) {
    const tag = m[0];
    if (/fonts\.googleapis\.com|gstatic|font-awesome|remixicon|boxicons|material/i.test(tag)) links.push(tag);
  }
  return links.join("\n");
}

/* ========= Tailwind 래퍼 ========= */
function buildSrcDocTailwind(code = "") {
  const head = buildHeadTags({ code });
  const pulledLinks = extractLinksFrom(code || "");
  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    ${head}
    ${pulledLinks}
    <style>
      html,body{margin:0;padding:0}
      ._preview-root{max-width:100%;padding:12px}
    </style>
  </head>
  <body>
    <div class="_preview-root">
      ${fixCommonCssTypos(code)}
    </div>
  </body>
</html>`;
}

/* ========= CSS/HTML 정규화 & 합성 ========= */
function bodyLooksLikeCssOnly(fullHtml = "") {
  try {
    const doc = new DOMParser().parseFromString(fullHtml, "text/html");
    const t = (doc.body?.innerHTML || "").trim();
    return t && t.includes("{") && t.includes("}") && !t.includes("<") && !t.includes(">");
  } catch { return false; }
}
function extractCssFromFullDoc(html = "") {
  const out = []; const re = /<style[^>]*>([\s\S]*?)<\/style>/gi; let m;
  while ((m = re.exec(html))) out.push(m[1] || "");
  return out.join("\n");
}
function getBodyInner(html = "") {
  const m = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  return m ? m[1] : "";
}
function setBodyInner(html = "", newInner = "") {
  if (!/<body/i.test(html)) return html;
  return html.replace(/<body[^>]*>[\s\S]*?<\/body>/i, `<body>${newInner}</body>`);
}
function addHeadStyles(fullHtml, cssText) {
  const extra = `<style>${cssText}</style>`;
  return /<\/head>/i.test(fullHtml)
    ? fullHtml.replace(/<\/head>/i, `${extra}</head>`)
    : fullHtml.replace(/<html[^>]*>/i, `$&<head>${extra}</head>`);
}
function fixCommonCssTypos(code = "") {
  return (code || "").replace(/0%\.\s*to/g, "0%, to");
}

/* ====== 특수 패턴: Press Start 2P 버튼(A안 단일 요소 합성) ====== */
function detectPressButtonPattern(css = "") {
  const s = css || "";
  const hasBorder = /(^|\})\s*\.button-border\s*\{/.test(s);
  const hasBase   = /(^|\})\s*\.button-base\s*\{/.test(s);
  const hasFace   = /(^|\})\s*\.button\s*\{/.test(s);
  const usesPressFont = /press\s*start\s*2p/i.test(s);
  return { hasBorder, hasBase, hasFace, usesPressFont };
}
function bodyHasOnlyBorderButton(inner = "") {
  // 예: <button class="button-border">Button</button> 만 있는 경우
  const clean = (inner || "").replace(/\s+/g, " ").toLowerCase();
  const hasButtonBorder = /<[^>]+class=["'][^"']*\bbutton-border\b[^"']*["'][^>]*>/.test(clean);
  const hasButtonBase = /\bbutton-base\b/.test(clean);
  const hasFace = /<[^>]+class=["'][^"']*\bbutton\b[^"']*["'][^>]*>/.test(clean);
  return hasButtonBorder && !hasButtonBase && !hasFace;
}
function buildPressSingleStyle() {
  return `
:root{
  --bdr: #ffae70;
  --base: #75221c;
  --face: #e64539;
  --c1:   #e7b8b4;
  --c2:   #f8c9c5;
  --c3:   #4e1814;
  --c4:   #79241e;
  --text: #ffee83;
}
.btn-press{
  position: relative;
  display: inline-block;
  font-family: "Press Start 2P", cursive;
  font-size: 20px;
  color: var(--text);
  background: var(--face);
  border: 4px solid;
  border-left-color: var(--c1);
  border-top-color: var(--c2);
  border-bottom-color: var(--c3);
  border-right-color: var(--c4);
  border-radius: 100px;
  padding: 18px 28px;
  cursor: pointer;
  outline: 2px solid black;
  transform: translateY(-8px);
  transition: transform .15s ease, box-shadow .15s ease;
  box-shadow: 0 6px 0 0 var(--base), 0 10px 16px rgba(0,0,0,.25);
}
.btn-press::before{
  content:"";
  position:absolute; inset:-14px;
  border:8px solid var(--bdr);
  outline:4px solid currentColor;
  border-radius:inherit;
  pointer-events:none;
}
.btn-press:hover{ transform: translateY(-4px); }
.btn-press:active{ transform: translateY(0); }
html,body{ margin:0; padding:16px; }
`;
}

/* ---- CSS/HTML 메인 합성 ---- */
function detectCssFeatures(css = "") {
  const s = css || "";
  return {
    btnBase: /(^|\})\s*button\s*\{/.test(s) || /(^|\})\s*\.button\s*\{/.test(s),
    btnSpan: /(^|\})\s*button\s+span\s*\{/.test(s),
    patContainer: /(^|\})\s*\.button-container\s*\{/.test(s),
    patBorder: /(^|\})\s*\.button-border\s*\{/.test(s),
    patButton: /(^|\})\s*\.button\s*\{/.test(s),
    patRealButton: /(^|\})\s*\.real-button\s*\{/.test(s),
    patSpin: /(^|\})\s*\.spin(\b|:)/.test(s),
    patUsesSvgFilters: /url\(#unopaq[23]?\)/.test(s),
    playPauseContainer:
      /(^|\})\s*\.container\s*\{/.test(s) &&
      /input:checked\s*~\s*\.play/.test(s) &&
      /input:checked\s*~\s*\.pause/.test(s),
    outerCont: /(^|\})\s*\.outer-cont\s*\{/.test(s),
    gradient: /(^|\})\s*\.gradient\s*\{/.test(s) || /button\s+\.gradient/.test(s),
    label: /(^|\})\s*\.label\s*\{/.test(s) || /button\s+\.label/.test(s),
    transition: /(^|\})\s*\.transition\s*\{/.test(s) || /button\s+\.transition/.test(s),
    hoverText: /(^|\})\s*\.hover-text\s*\{/.test(s),
    iconSeries: /\.icon-\d/.test(s) || /\.fil-leaf-\d/.test(s),
    scene: /(^|\})\s*\.scene\s*\{/.test(s),
    cube: /(^|\})\s*\.cube\s*\{/.test(s),
    side: /(^|\})\s*\.side\s*\{/.test(s),
    top: /(^|\})\s*\.top\s*\{/.test(s),
    front: /(^|\})\s*\.front\s*\{/.test(s),
    classFirst: (s.match(/\.([A-Za-z_][\w-]*)\s*\{/) || [,""])[1],
  };
}

// 1) container + play/pause + checkbox 토글
function synthesizePlayPauseContainer() {
  return `
<label class="container" role="button" aria-label="play/pause toggle" style="display:inline-flex">
  <input type="checkbox" aria-hidden="true"/>
  <svg class="play" viewBox="0 0 64 64" width="1em" height="1em" aria-hidden="true">
    <polygon points="22,16 50,32 22,48" />
  </svg>
  <svg class="pause" viewBox="0 0 64 64" width="1em" height="1em" aria-hidden="true">
    <rect x="18" y="16" width="10" height="32" />
    <rect x="36" y="16" width="10" height="32" />
  </svg>
</label>`.trim();
}
// 2) button-container + border + spin
function synthesizeContainerPattern({ withFilters }) {
  const filters = withFilters ? `
<svg width="0" height="0" style="position:absolute">
  <defs>
    <filter id="unopaq">
      <feGaussianBlur stdDeviation="8"></feGaussianBlur>
      <feColorMatrix type="matrix"
        values="1 0 0 0 0
                0 1 0 0 0
                0 0 1 0 0
                0 0 0 18 -8"></feColorMatrix>
    </filter>
    <filter id="unopaq2">
      <feGaussianBlur stdDeviation="2"></feGaussianBlur>
      <feColorMatrix type="matrix"
        values="1 0 0 0 0
                0 1 0 0 0
                0 0 1 0 0
                0 0 0 18 -8"></feColorMatrix>
    </filter>
    <filter id="unopaq3">
      <feGaussianBlur stdDeviation="1.5"></feGaussianBlur>
      <feColorMatrix type="matrix"
        values="1 0 0 0 0
                0 1 0 0 0
                0 0 1 0 0
                0 0 0 18 -8"></feColorMatrix>
    </filter>
  </defs>
</svg>` : "";
  return `
<div class="button-container" style="display:inline-block">
  <button class="real-button" aria-label="button"></button>
  <div class="button-border">
    <div class="button">
      <span>Button</span>
      <div class="backdrop"></div>
      <div class="spin spin-blur"></div>
      <div class="spin spin-intense"></div>
      <div class="spin spin-inside"></div>
    </div>
  </div>
</div>
${filters}`.trim();
}
// 3) outer-cont 그라데이션 버튼
function synthesizeOuterContButton() {
  return `
<button class="outer-cont" type="button" style="display:inline-block">
  <span class="flex">
    <span>Button</span>
  </span>
</button>`.trim();
}

/* ---- 메인 합성 ---- */
function synthesizeFromCss(css = "") {
  const f = detectCssFeatures(css);
  const hasAnyButtonRule = !!f.btnBase;

  if (f.playPauseContainer) return synthesizePlayPauseContainer();
  if (f.patContainer && (f.patBorder || f.patButton || f.patRealButton || f.patSpin)) {
    return synthesizeContainerPattern({ withFilters: f.patUsesSvgFilters });
  }
  if (f.outerCont) return synthesizeOuterContButton();

  if (hasAnyButtonRule && (f.gradient || f.label || f.transition)) {
    return `<button type="button">
      <span class="${f.label ? "label" : ""}">Button</span>
      ${f.transition ? '<span class="transition"></span>' : ""}
      ${f.gradient ?  '<span class="gradient"></span>'  : ""}
    </button>`;
  }
  if (hasAnyButtonRule && f.btnSpan) return `<button type="button"><span>Button</span></button>`;

  if (hasAnyButtonRule && f.iconSeries) {
    const leaf = (cls, fill) =>
      `<svg class="${cls}" viewBox="0 0 100 100" width="0" height="0" aria-hidden="true"><circle class="${fill}" cx="50" cy="50" r="45"></circle></svg>`;
    return `<button type="button"><span>Hover me</span>
      ${leaf("icon-1","fil-leaf-1")}${leaf("icon-2","fil-leaf-2")}${leaf("icon-3","fil-leaf-3")}
      ${leaf("icon-4","fil-leaf-4")}${leaf("icon-5","fil-leaf-5")}</button>`;
  }
  if (f.scene && f.cube && (f.top || f.front || f.side)) {
    return `<div class="scene"><div class="cube"><div class="side front">Front</div><div class="side top">Top</div></div></div>`;
  }
  if (f.hoverText) return `<button class="button"><span class="hover-text" data-text="Button">Button</span></button>`;
  if (hasAnyButtonRule) return `<button type="button">Button</button>`;

  if (f.classFirst) {
    return /btn|button/i.test(f.classFirst)
      ? `<button class="${f.classFirst}">Button</button>`
      : `<div class="${f.classFirst}">Preview</div>`;
  }
  return `<button type="button">Button</button>`;
}

function repairCssOnlyBody(fullHtml = "") {
  try {
    const doc = new DOMParser().parseFromString(fullHtml, "text/html");
    const css = (doc.body?.innerHTML || "").trim();
    const head = doc.head || doc.documentElement;
    const st = doc.createElement("style"); st.textContent = fixCommonCssTypos(css); head.appendChild(st);
    doc.body.innerHTML = synthesizeFromCss(css);
    const extra = doc.createElement("style");
    extra.textContent = `html,body{margin:0;padding:16px}button{display:inline-block}svg{display:block}`;
    head.appendChild(extra);
    return "<!doctype html>\n" + doc.documentElement.outerHTML;
  } catch { return fullHtml; }
}

function normalizePartialFullDoc(fullHtml = "") {
  try {
    const css = fixCommonCssTypos(extractCssFromFullDoc(fullHtml));
    if (!css) return fullHtml;

    const inner = (getBodyInner(fullHtml) || "").trim();
    const f = detectCssFeatures(css);

    // ★ Press Start 2P 3-겹 패턴 자동보정 (A안 단일 요소로 치환)
    const press = detectPressButtonPattern(css);
    if (press.hasBorder && press.hasFace && bodyHasOnlyBorderButton(inner)) {
      // 1) 바디를 단일 버튼으로 교체
      let html = setBodyInner(fullHtml, `<button class="btn-press">Button</button>`);
      // 2) 전용 스타일 삽입
      html = addHeadStyles(html, buildPressSingleStyle());
      // 3) 폰트 링크가 없으면 자동 삽입 (buildExternalDeps는 원문 코드 기반이므로 여기서 보강)
      if (!/Press\+Start\+2P/i.test(html)) {
        html = html.replace(
          /<\/head>/i,
          `<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">\n</head>`
        );
      }
      return html;
    }

    // --- 기존 보강 로직 ---
    const hasCheckbox = /<input[^>]*type=["']checkbox["'][^>]*>/i.test(inner);
    const hasPlay = /class=["'][^"']*\bplay\b[^"']*["']/i.test(inner);
    const hasPause = /class=["'][^"']*\bpause\b[^"']*["']/i.test(inner);
    const hasPlayPauseDom = hasCheckbox && hasPlay && hasPause;

    const hasOuterContDom = /class=["'][^"']*\bouter-cont\b[^"']*["']/i.test(inner);
    const hasContainerDom = /class=["'][^"']*\bbutton-container\b[^"']*["']/i.test(inner);

    const looksLikePreviewOnly =
      inner.replace(/\s+/g, " ").toLowerCase().includes("preview") &&
      !/<(button|input|svg)\b/i.test(inner);

    const containerOnly =
      /class=["'][^"']*\bcontainer\b[^"']*["']/i.test(inner) &&
      !hasCheckbox && !/<svg\b/i.test(inner);

    const needs =
      (f.playPauseContainer && (!hasPlayPauseDom || looksLikePreviewOnly || containerOnly)) ||
      (f.outerCont && !hasOuterContDom) ||
      (f.patContainer && !hasContainerDom) ||
      (((/button\s*\{/.test(css) || /\.button\b/.test(css)) && !/<button\b/i.test(inner)) ||
       (/\.icon-\d/.test(css) && !/<svg\b/i.test(inner)));

    if (!needs) {
      return fullHtml.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, (m) =>
        m.replace(/0%\.\s*to/g, "0%, to")
      );
    }

    const synthesized = synthesizeFromCss(css);
    let html = setBodyInner(fullHtml, synthesized);
    html = addHeadStyles(html, `html,body{margin:0;padding:16px}button{display:inline-block}svg{display:block}`);
    html = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, (m) => m.replace(/0%\.\s*to/g, "0%, to"));
    return html;
  } catch { return fullHtml; }
}

/* ========= srcDoc ========= */
function chooseSrcDoc(code = "") {
  const decoded = decodeEntities(code || "");
  if (isFullHTMLDocument(decoded)) {
    if (bodyLooksLikeCssOnly(decoded)) return repairCssOnlyBody(decoded);
    return normalizePartialFullDoc(decoded);
  }
  return buildSrcDocTailwind(decoded);
}

/* ========= 버튼 존재/품질 필터 ========= */
// 빠른 사전 필터: 버튼 DOM 흔적이 없으면 렌더 생략
function hasButtonSignature(html = "") {
  const re = /<(button)\b|role=["']button["']|class=["'][^"']*\b(btn|button)\b/gi;
  return re.test(html || "");
}

/* ========= 컴포넌트 ========= */
export default function IframePreview({
  code,
  height: fixedHeight = 420,
  autoHeight = false,
  maxHeight = 10000,
  minWidth = 60,          // 버튼 최소 너비(px)
  minHeight = 24,         // 버튼 최소 높이(px)
  minStyledSignals = 1,   // 스타일 신호 최소 개수
  onDecide,               // 통과/실패 부모 통지
}) {
  const iframeRef = useRef(null);
  const [height, setHeight] = useState(fixedHeight);
  const [qualityOK, setQualityOK] = useState(true);

  const srcDoc = useMemo(() => chooseSrcDoc(code || ""), [code]);

  // 1) 사전 필터: 버튼 흔적 자체가 없으면 렌더 X
  const prefilterOK = useMemo(() => hasButtonSignature(srcDoc), [srcDoc]);

  useEffect(() => {
    if (!prefilterOK) {
      onDecide?.(false);
      return;
    }
    const el = iframeRef.current;
    if (!el) return;

    const onLoad = () => {
      try {
        const doc = el.contentDocument;
        if (!doc) return;

        // 내부 스크롤 제어
        try {
          const style = doc.createElement("style");
          style.textContent = `html,body{overflow:hidden} ._preview-root{overflow:auto; max-height:100%}`;
          doc.head.appendChild(style);
        } catch {}

        // 2) 품질 체크
        const candidates = Array.from(
          doc.querySelectorAll('button, [role="button"], .button, .btn')
        );

        const isVisible = (node) => {
          const cs = doc.defaultView?.getComputedStyle?.(node);
          if (!cs) return false;
          if (cs.display === "none" || cs.visibility === "hidden") return false;
          if (parseFloat(cs.opacity || "1") <= 0.05) return false;
          const r = node.getBoundingClientRect?.();
          if (!r) return false;
          if (r.width < minWidth || r.height < minHeight) return false;
          return true;
        };

        const styledScore = (node) => {
          const cs = doc.defaultView?.getComputedStyle?.(node);
          if (!cs) return 0;

          const bgAlpha = (() => {
            const m = cs.backgroundColor?.match(/rgba?\(([^)]+)\)/i);
            if (!m) return 0;
            const parts = m[1].split(",").map((x) => x.trim());
            const a = parts.length === 4 ? parseFloat(parts[3]) : 1;
            return isNaN(a) ? 0 : a;
          })();

          let score = 0;
          if (parseFloat(cs.borderTopLeftRadius || "0") > 4 ||
              parseFloat(cs.borderTopRightRadius || "0") > 4 ||
              parseFloat(cs.borderBottomLeftRadius || "0") > 4 ||
              parseFloat(cs.borderBottomRightRadius || "0") > 4) score++;
          if ((cs.boxShadow || "none") !== "none") score++;
          if ((cs.backgroundImage || "none") !== "none") score++;
          if (bgAlpha > 0.05) score++;
          const borderSum =
            parseFloat(cs.borderTopWidth || "0") +
            parseFloat(cs.borderRightWidth || "0") +
            parseFloat(cs.borderBottomWidth || "0") +
            parseFloat(cs.borderLeftWidth || "0");
          if (borderSum > 0.5) score++;
          if ((cs.transform || "none") !== "none") score++;
          if ((cs.filter || "none") !== "none") score++;
          if ((cs.backdropFilter || "none") !== "none") score++;
          const hasTransition =
            (cs.transitionDuration && cs.transitionDuration.split(",").some(d => parseFloat(d) > 0)) ||
            (cs.animationName && cs.animationName !== "none");
          if (hasTransition) score++;

          return score;
        };

        let pass = false;
        for (const node of candidates) {
          if (!isVisible(node)) continue;
          if (styledScore(node) >= minStyledSignals) { pass = true; break; }
        }

        setQualityOK(pass);
        onDecide?.(pass);

        // 높이 측정(통과한 경우만)
        if (pass) {
          if (!autoHeight) { setHeight(fixedHeight); return; }
          let done = false;
          const measureOnceStable = () => {
            if (done) return;
            const h = Math.max(
              doc.documentElement?.scrollHeight || 0,
              doc.body?.scrollHeight || 0,
              360
            );
            const clamped = Math.min(h, maxHeight);
            setHeight(clamped);
            done = true;
          };
          measureOnceStable();
          setTimeout(measureOnceStable, 250);
          doc.fonts?.ready?.then?.(() => setTimeout(measureOnceStable, 50));
        }
      } catch {
        onDecide?.(false);
      }
    };

    el.addEventListener("load", onLoad);
    return () => el.removeEventListener("load", onLoad);
  }, [srcDoc, prefilterOK, autoHeight, fixedHeight, maxHeight, minWidth, minHeight, minStyledSignals, onDecide]);

  if (!prefilterOK) return null;
  if (!qualityOK && onDecide) return null;

  return (
    <iframe
      ref={iframeRef}
      title="component-preview"
      srcDoc={srcDoc}
      sandbox="allow-scripts allow-forms allow-pointer-lock allow-popups allow-modals allow-same-origin"
      style={{
        width: "100%",
        border: "1px solid rgba(0,0,0,.08)",
        borderRadius: 12,
        height,
        background: "transparent",
      }}
    />
  );
}
