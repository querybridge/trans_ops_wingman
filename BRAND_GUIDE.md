# Transportation Operations Wingman: Brand Guide

How to make the app look and feel like it belongs next to Yzer Next's public brand without presenting it as an official Yzer product.

**Source:** observed on https://www.yzernext.com/ on 2026-10-22, from the site's own theme CSS (Elementor global tokens, `typography.css`, `general.css`) and a 1440px-wide full-page render. Values are what the public site uses today, not an official Yzer brand book. If Yzer shares real brand guidelines, those win.

---

## 1. Brand alignment boundaries (read first)

The build brief says this is "an independent demonstration, not an official Yzer product." Being on brand means **looking familiar, not impersonating**:

- **Do** use Yzer's typeface, color palette, button shapes, and tone so the CIO sees the app fitting into their world.
- **Don't** use the Yzer Next logo, wordmark, or "Yzer Next" name in the app's header, favicon, or page titles. The product name is **Transportation Operations Wingman**.
- **Don't** reuse Yzer photography or marketing copy.
- **Always** show the "Prototype - Synthetic data - For Demo Only" label (brief requirement).

---

## 2. Typography

### Typeface
**Plus Jakarta Sans** is the only typeface on yzernext.com, used for headings, body, buttons, and labels. It is free (SIL Open Font License) on Google Fonts.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&display=swap" rel="stylesheet">
```

Fallback stack: `"Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", sans-serif`

For shipment, event, and note IDs (e.g. `SHP-00042`), use the system monospace stack `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` so IDs scan cleanly and read as references. This is an app addition, not something the site uses.

### Weights in use
| Weight | Site usage | App usage |
| --- | --- | --- |
| 400 Regular | Body copy | Body, table cells |
| 500 Medium | **All headings**, lead text | Headings, metric numbers |
| 700 Bold | Buttons, uppercase eyebrow labels, `<strong>` | Buttons, eyebrows, badges, table headers |

Headings are **Medium (500), not Bold**. That's a defining trait of the brand's look; don't bold the headings.

### Letter spacing
- Headings: tight, **-0.03em** (h1–h3, h5) / -0.02em (h4, h6)
- Body: **-0.01em** everywhere
- Eyebrow labels: **+0.05em**, UPPERCASE, 700

### Site type scale (marketing, for reference)
| Element | Desktop | Tablet ≤1024 | Mobile ≤767 | Line height |
| --- | --- | --- | --- | --- |
| h1 | 52px | 46px | 38px | 1.0 |
| h2 | 46px | 40px | 34px | 1.1 |
| h3 | 36px | | 30px | 1.1 |
| h4 | 26px | | | 1.4 |
| h5 | 22px | | | 1.3 |
| h6 | 20px | | | 1.3 |
| Lead (`l-text`) | 18px / 500 | | | 1.5 |
| Body (`m-text`) | 16px / 400 | | | 1.5 |
| Small (`s-text`) | 14px / 400 | | | 1.5 |
| Eyebrow | 16px / 700 / caps / +0.05em | | | 1.5 |

### App type scale (dashboard, scaled down)
Marketing sizes are too large for a dense operations screen. Keep the same weights and tracking, but use these sizes:

| Role | Size / weight | Tracking |
| --- | --- | --- |
| Page title ("Transportation Operations Wingman") | 26px / 500 | -0.03em |
| Section heading (e.g. "Exceptions", "Shipment SHP-00042") | 20px / 500 | -0.02em |
| Panel heading | 16px / 500 | -0.01em |
| Eyebrow / section label (e.g. "NEEDS ATTENTION") | 12px / 700 / caps | +0.05em |
| Body | 15px / 400 | -0.01em |
| Table cell | 14px / 400 | -0.01em |
| Metric number | 32px / 500 | -0.03em, tabular figures |
| Caption, timestamps, citations | 13px / 400 | -0.01em |

Use `font-variant-numeric: tabular-nums` on metrics, counts, ages, and timestamps so digits line up in columns.

---

## 3. Color

### Core palette (exact tokens from the site's CSS)
| Name | Hex | Site role |
| --- | --- | --- |
| **Navy** | `#002A4E` | Hero and footer backgrounds, dark sections, dark buttons, hover state |
| **Sky Blue** (Elementor "primary") | `#32C5F4` | Primary pill buttons, eyebrow labels, arrow icons, highlight numbers |
| **Blue** (Elementor "secondary") | `#045493` | Call-to-action panels, secondary dark surfaces |
| **Aqua** (Elementor "accent") | `#86D2DA` | Logo "NEXT", stat-circle rings, subtle accents on navy |
| **Ink** (text) | `#19191B` | All body text and headings on light backgrounds |
| **Slate** | `#6D7276` | Secondary/muted text |
| **Light Gray** | `#F4F4F4` | Alternating section backgrounds, cards |
| **White** | `#FFFFFF` | Main background, text on dark |

Supporting values seen in the CSS: error `#FF9292` and success `#9FFFB1` (pale form-message colors). They're too light for status text, so the app uses the status palette below instead.

### Measured color share on yzernext.com
Measured by classifying every pixel of a 1440px full-page homepage render against the palette.

| Color | Whole page | Excluding photography |
| --- | --- | --- |
| White `#FFFFFF` | 29.6% | ~40% |
| Navy `#002A4E` | 14.7% | ~20% |
| Light Gray `#F4F4F4` | 14.2% | ~19% |
| Blue `#045493` | 6.7% | ~9% |
| Ink `#19191B` | 4.1% | ~6% |
| Slate `#6D7276` | 2.4% | ~3% |
| Aqua `#86D2DA` | 2.0% | ~3% |
| Sky Blue `#32C5F4` | 0.2% | <1% |
| Photography / other | 26.1% | n/a |

**What this shows:** the brand is mostly white and light gray, anchored by large navy blocks. **Sky Blue covers less than 1% of the page but carries almost all the emphasis** (every primary button, eyebrow, and arrow). It's a spotlight color, not a fill color.

### Recommended color share for the app
The site uses photography for about a quarter of the page; the app uses none (the brief rules out decorative imagery). So shift that share to neutrals and keep the navy and sky-blue roles intact:

| Color | Target share | Where it goes in the app |
| --- | --- | --- |
| White + Light Gray | **~70%** | Page background (white), cards and panels, table zebra striping and filter bar (light gray) |
| Navy | **~15%** | Top app bar, "Generate Briefing" panel or footer band, selected table row edge |
| Ink + Slate (text) | **~8%** | Headings, body, table text; slate for timestamps and captions |
| Blue | **~4%** | Primary buttons (white text), links, active filter chips, info badges |
| Sky Blue | **~2%** | Eyebrow labels on navy, focus rings, small highlights, arrow icons. Never large fills |
| Aqua | **~1%** | Accents on navy (prototype label, rings around metric icons) |
| Status colors | **only where status exists** | Severity badges and conflict/unknown callouts |

Rule of thumb: a screenshot of any app screen should read as **white and navy with one or two sparks of sky blue**, with severity colors appearing only on flagged rows.

### Accessibility: contrast checks (WCAG 2.x)
| Pair | Ratio | Verdict |
| --- | --- | --- |
| White on Navy | 14.57 | ✅ AAA |
| Ink on White | 17.56 | ✅ AAA |
| Ink on Light Gray | 15.96 | ✅ AAA |
| White on Blue `#045493` | 7.79 | ✅ AAA |
| Navy on Sky Blue | 7.24 | ✅ AAA |
| Sky Blue on Navy | 7.24 | ✅ AAA |
| Aqua on Navy | 8.50 | ✅ AAA |
| Slate on White | 4.86 | ✅ AA (body text) |
| Slate on Light Gray | 4.42 | ⚠️ AA large text only |
| **White on Sky Blue** | **2.01** | ❌ Fails, though the site does this on its buttons |
| **Sky Blue on White** | **2.01** | ❌ Fails for text, though the site uses it for eyebrow labels |

**App rules that follow from this:**
1. **Primary buttons:** Blue `#045493` with white text (7.79). Alternative: Sky Blue with **navy** text (7.24). Never white text on sky blue.
2. **Eyebrow labels:** Blue `#045493` on light backgrounds; Sky Blue only on navy.
3. **Muted text:** Slate only on white. On light gray, use Ink or a darker slate such as `#5A5F63`.

### Status / severity palette (app addition)
The site has no status colors suitable for an operations dashboard. These are chosen to sit comfortably next to the blues, pass AA, and never be confused with brand blue:

| Status | Text / border | Badge background | Contrast | Use |
| --- | --- | --- | --- | --- |
| Critical | `#B42318` | `#FEF3F2` | 6.05 | Missed window past threshold, failed attempt |
| Warning | `#B54708` | `#FFFAEB` | 5.20 | Missing scan, POD within grace issues |
| Resolved / OK | `#027A48` | `#ECFDF3` | 5.13 | Clean, delivered with POD |
| Info / Unknown | `#045493` (Blue) | `#F4F4F4` | 7.79 vs white | Unknown ETA, needs verification, conflicting evidence |

- Always pair color with a text label ("Critical", "Warning"); never rely on color alone.
- Severity labels are rule-based. Never style them like probabilities or scores (brief requirement).

---

## 4. Components

### Buttons
Taken from the site's `.btn` styles:

- **Shape:** full pill, `border-radius: 60px`
- **Site size:** `padding: 11px 29px`, 16px, weight 700, -0.01em
- **App size:** `padding: 8px 20px`, 14px, weight 700 (denser); keep the pill
- **Border:** 1px solid, same color as fill
- **Transition:** `color, background, border-color` over `.35s ease`
- **Hover:** the site swaps to Navy (`#002A4E`) on hover. Keep that: Blue → Navy.
- **Disabled:** `opacity: .7; pointer-events: none` (site value)

| Variant | Default | Hover | App use |
| --- | --- | --- | --- |
| Primary | Blue bg, white text | Navy bg | "Generate Briefing", "Explain shipment" |
| Light on dark | White bg, navy text | Navy bg, white text with white border | Buttons inside navy bands |
| Outline on dark | Transparent, white border and text | White bg, navy text | Secondary actions on navy |
| Quiet | Transparent, blue text | Light gray bg | "Retry", "View source", table "Details" |

### Cards and panels
- Radius **6px** (the site's card radius)
- Background white on light-gray sections, or light gray on white
- Shadow: none, or the site's subtle `0 1px 2px 0 rgba(0,0,0,.1)`. No heavy drop shadows.
- 24px internal padding (16px on mobile)

### Metric tiles
The site shows key numbers (89 facilities, 2,500 drivers) large, in Medium weight, with an aqua ring. The app's four metrics (shipments, needing attention, missed windows, missing POD) echo this:
- 32px / 500 numbers, tabular figures
- 12px uppercase eyebrow label above (700, +0.05em)
- Optional thin aqua `#86D2DA` top border or ring, used as decoration only; it isn't a status color

### Eyebrow labels
The site's signature pattern is a small **uppercase bold label** above a heading ("THE DIFFERENCE", "THE SOLUTION"). Use it for section labels: "EXCEPTION QUEUE", "EVIDENCE", "PROCEDURE", "MANAGER BRIEFING".

### Icons
The site uses simple line icons, and circular arrow buttons (sky-blue circle, white arrow) for "more" actions. In the app:
- Use one line-icon set at 1.5–2px stroke, 16–20px size
- Use the circular arrow treatment for the table "Details" action if desired (navy arrow on sky-blue circle for contrast)

### Tables (app addition, in brand style)
- Header row: 12px uppercase, 700, +0.05em, Slate text, light-gray background
- Rows: 14px, Ink, 1px `#E6E6E6` dividers, light-gray zebra striping optional
- Selected row: 3px Blue left border plus light-gray background
- ID columns in monospace; numeric columns right-aligned with tabular figures

---

## 5. Layout and spacing

- **Container:** max-width **1290px**, 15px side padding (site `.container`). This works well for the dashboard too; widen to full width only for the exception table if needed.
- **Grid:** the site is Bootstrap-based (12 columns). Plain CSS grid is fine for the app.
- **Breakpoints** (site values): ≤1024px tablet, ≤767px mobile.
- **Rhythm:** generous whitespace and large section padding on the site; the app should use a tighter 8px spacing scale (8 / 16 / 24 / 32 / 48) while keeping white space around panels.
- **Alternating bands:** the site alternates white, light gray, and navy sections. In the app: navy top bar, white workspace, light-gray filter bar and panels.

---

## 6. Voice and copy

What the site sounds like:
- Headings: **Title Case**, confident, outcome-focused ("The Leading Managed Delivery System", "When Precision and Scale are Mission Critical").
- Recurring themes: *last mile, managed delivery, precision, scale, speed, accuracy, reliability, extension of your business*.
- Short declarative sentences; no jargon or hype.

App copy guidelines:
- Title Case for headings, buttons, and section labels; sentence case for body, explanations, and recommendations.
- Plain, operational verbs: "Review", "Verify", "Contact dispatch", "Escalate to regional lead".
- State uncertainty plainly: "ETA unavailable from source", "Notes conflict — verify with driver". This matches the brand's "reliability" promise better than confident guesses.
- Keep technology names out of the manager workflow; put them in About/Evaluation (brief requirement).
- No hiring language in the UI (brief requirement).

---

## 7. Ready-to-use CSS tokens

```css
:root {
  /* Brand (observed on yzernext.com) */
  --brand-navy: #002A4E;
  --brand-blue: #045493;
  --brand-sky: #32C5F4;
  --brand-aqua: #86D2DA;
  --ink: #19191B;
  --slate: #6D7276;
  --slate-strong: #5A5F63;   /* muted text on light gray */
  --gray-50: #F4F4F4;
  --gray-200: #E6E6E6;       /* dividers (app addition) */
  --white: #FFFFFF;

  /* Status (app addition) */
  --critical: #B42318;  --critical-bg: #FEF3F2;
  --warning:  #B54708;  --warning-bg:  #FFFAEB;
  --ok:       #027A48;  --ok-bg:       #ECFDF3;
  --info:     #045493;  --info-bg:     #F4F4F4;

  /* Type */
  --font-sans: "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --track-heading: -0.03em;
  --track-body: -0.01em;
  --track-eyebrow: 0.05em;

  /* Shape & motion */
  --radius-card: 6px;
  --radius-pill: 60px;
  --shadow-card: 0 1px 2px 0 rgba(0, 0, 0, .1);
  --transition: color .35s ease, background-color .35s ease, border-color .35s ease;

  /* Layout */
  --container: 1290px;
}

body {
  font-family: var(--font-sans);
  font-size: 15px;
  line-height: 1.5;
  letter-spacing: var(--track-body);
  color: var(--ink);
  background: var(--white);
}
h1, h2, h3, h4 { font-weight: 500; letter-spacing: var(--track-heading); }
.eyebrow { font-size: 12px; font-weight: 700; text-transform: uppercase;
           letter-spacing: var(--track-eyebrow); color: var(--brand-blue); }
.on-navy .eyebrow { color: var(--brand-sky); }
.btn { border-radius: var(--radius-pill); padding: 8px 20px; font-weight: 700;
       font-size: 14px; border: 1px solid transparent; transition: var(--transition); }
.btn-primary { background: var(--brand-blue); border-color: var(--brand-blue); color: var(--white); }
.btn-primary:hover { background: var(--brand-navy); border-color: var(--brand-navy); }
.btn:focus-visible { outline: 3px solid var(--brand-sky); outline-offset: 2px; }
.id { font-family: var(--font-mono); font-size: 13px; }
.num { font-variant-numeric: tabular-nums; }
```

---

## 8. On-brand checklist

- [ ] Plus Jakarta Sans loaded; headings at weight 500 with negative tracking
- [ ] Screens read as white + navy with sparing sky-blue accents (~70 / 15 / 2 split)
- [ ] No white text on sky blue; all text pairs pass AA
- [ ] Pill buttons; 6px cards; subtle or no shadows
- [ ] Uppercase eyebrow labels on major sections
- [ ] Severity colors only on flagged items, always with a text label
- [ ] No Yzer logo, wordmark, photography, or "official" implication; prototype label visible
- [ ] Title Case headings; plain, honest operational copy
