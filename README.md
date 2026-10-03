# CV Builder

A split-screen resume builder: edit on the left, see a live, print-ready preview
on the right. Export straight to PDF via the browser's print dialog, with no
backend, no server-side rendering; everything runs in the browser and
autosaves to `localStorage`.

## Stack

- **Vite + React**: fast dev server, no build config needed
- **Tailwind CSS**: utility styling, with a small set of CSS variables
  (`--ink`, `--paper`, `--accent`, etc.) driving the theme so the accent
  color can be changed live
- **File System Access API** (Chrome/Edge) for the optional "save
  templates as real files in a folder" feature; see Resumes below.
  No dependency; falls back to browser storage automatically where
  unsupported.
- **No backend, no database**: state lives in React and persists to
  `localStorage` in the browser

## Running it

You'll need [Node.js](https://nodejs.org) **20.19+ or 22.12+** installed, since Vite 8 (used here) requires it. Check with:

```bash
node -v
```

```bash
cd cv-builder
npm install
npm run dev
```

Then open the URL Vite prints (usually `http://localhost:5173`).

To produce a production build:

```bash
npm run build
npm run preview
```

## How it works

- `src/App.jsx` holds all state (resume data, selected template, accent
  color, editor theme, which template is currently loaded) and persists
  it to `localStorage` on every change.
- `src/components/EditorForm.jsx` is the left-hand form, rendering
  sections in the order given by `data.sectionOrder` (see Reordering
  whole sections below).
- `src/components/ResumePreview.jsx` renders whichever template is
  selected inside `#resume-print-root`, the only element left visible
  by the print stylesheet in `src/index.css`, and also measures its
  height to drive the page-count indicator (see Multi-page overflow
  below).
- `src/components/templates/` has two templates, `ClassicTemplate.jsx`
  (single-column serif, ATS-safe) and `ModernTemplate.jsx` (sidebar +
  sans-serif). Both read from the exact same `data` shape and both
  respect `data.sectionOrder`, so switching templates never loses
  information or reordering.
- **Export to PDF** just calls `window.print()`. Pick **Save as PDF** as
  the destination. "Microsoft Print to PDF" goes through the Windows printer
  driver and turns the web fonts into outlines, so the text in that PDF
  can't be selected, searched or read by applicant-tracking systems. While
  the dialog is open the page title is set to "<name> - CV", so Save as PDF
  suggests a sensible file name. The `@media print` rules
  in `index.css` hide everything except the resume sheet and force A4
  page size, giving you vector-quality text with zero extra
  dependencies. In the print dialog, disable "headers and footers" for a
  clean result.
- **`print-color-adjust: exact`** is set on `.resume-page` (and as a
  belt-and-suspenders measure, on `html`/`body` too under `@media
  print`). Without it, browsers silently strip "decorative" colors,
  including background fills and, in most engines, border colors, when
  printing, to save ink. That's why the Modern template's accent-colored
  ribbon (`.resume-page`'s `border-left`) and sidebar tint wouldn't show
  up in exported PDFs before this was added. It's an inherited property,
  so setting it once on `.resume-page` covers every colored element
  inside it, including a custom accent color: the ribbon isn't fixed to
  teal, it just uses the same `--accent` variable as everything else in
  the top bar's Accent picker. This is a *hint*, not a guarantee, since
  browser/OS print-driver combinations vary, so the Export PDF button
  also carries a tooltip reminding you to check "Background graphics"
  (Chrome/Edge) or "Print backgrounds" (Firefox) if a color ever looks
  missing.

## Resumes (save/load templates, switch between job applications)

The **Resumes** button (top-left, next to the app name) opens a window
for saving the current resume as a named template and loading a
different one, built for the common workflow of tailoring one base
resume per job application.

**Where templates are stored**, two modes:

- **Browser storage** (default, works everywhere): templates are kept
  in `localStorage` under a separate key from your main autosave, so
  they survive between sessions but are tied to this browser/device.
- **A real folder on disk** (Chrome/Edge only, via the File System
  Access API): click "Choose folder…" once to pick a folder, and every
  template saves there as an actual `.json` file you can see in File
  Explorer, back up, sync, or version-control. The chosen folder handle
  is remembered (via IndexedDB) across sessions, but browsers require
  permission to be re-confirmed with a click each time you return, so
  the window shows a one-click "Reconnect" button rather than silently
  re-prompting. If a folder isn't connected, or your browser doesn't
  support the API, everything transparently falls back to browser
  storage; nothing else in the app changes.

Each template file is just the same shape as a Backup file (see below)
plus a `name` and `savedAt`. That means a plain Backup export dropped
into a connected folder is automatically picked up as a template too.

**Switching applications quickly**: once you load a template, its name
shows right in the top bar, and the Resumes window offers an "Update
'\<name>'" shortcut so a quick edit resaves to the same file/entry
instead of always creating a new one.

## Backup (Save / Load a single file)

Separate from the Resumes window above, the **Backup** buttons in the
top bar export/import a single JSON snapshot (resume data, template,
accent, theme). Handy for a one-off download, moving to a machine
where you don't want to set up a folder connection, or a quick
snapshot before a big edit. **Save** downloads
`<your-name>-cv-backup.json`; **Load** reads one back in (after a
confirmation, since it replaces what's currently open).

## Data model

```js
{
  labels: { experience, education, certifications, skills, projects },
  sectionOrder: ['experience', 'education', 'certifications', 'skills', 'projects', /* + custom section ids */],
  basics: { name, title, email, phone, location, website, summary },
  experience: [{ id, company, role, location, start, end, bulletsText }],
  education: [{ id, school, degree, field, start, end }],
  certifications: [{ id, name, issuer, date, link }],
  skillsText: "Design: Figma, Prototyping\nTools: Git, Notion",
  projects: [{ id, name, description, link }],
  customSections: [{ id, title, items: [{ id, text }] }],
}
```

`bulletsText` and `skillsText` are plain multi-line strings that get
split/parsed at render time (one bullet per line; `Category: item, item`
per skills line). This keeps the form simple while still giving
structured output in the templates.

`sectionOrder` is a flat array mixing the five fixed section keys with
any custom section's `id`. It's the single source of truth for
rendering order in both the editor and both templates. Loading old
data missing this field (or missing entries added since, like a newer
custom section) repairs it automatically in `normalizeData()` in
`App.jsx`: existing valid entries are kept in place, anything missing
is appended, anything stale is dropped.

## Reordering entries and whole sections

Each Experience, Education, Certifications, and Projects card has a `⠿`
drag handle: drag it up or down within its own list to reorder. Items
inside a custom section have their own drag handle too. Each of those
same cards also has a **Duplicate** button next to Remove, handy for
near-identical entries (e.g. two similar certifications, or a role you
held twice at different levels).

Whole **sections** (Experience, Education, Certifications, Skills,
Projects, and each custom section) can also be dragged relative to each
other, via the `⠿⠿` handle next to each section's title in the editor,
so moving Skills above Experience, say, is a single drag. This writes
to `data.sectionOrder` and both templates read that same order, so the
reordering shows up in the actual resume, not just the editor. In the
Modern template, Skills/Education/Certifications always live in the
sidebar and Experience/Projects/custom sections always live in the main
column by design; dragging still reorders *within* whichever zone a
section belongs to.

## Certifications & custom sections

**Certifications** works exactly like Projects: name, issuing
organization, date, an optional credential link, drag-to-reorder, and
it appears on both templates (main column in Classic, sidebar in
Modern).

**Custom sections** let you add any section the built-in ones don't
cover, like Languages, Publications, or Volunteering. Each one gets
its own editable title, its own drag handle (so it can be repositioned
like any other section), and an ordered, draggable list of one-line
items, rendered as a bulleted list on the resume. Empty items are
skipped automatically so a half-filled section never appears blank.

## Gentle content hints

Two simple heuristics, both in `src/lib/hints.js`, surface as small
amber (never red/error-styled) suggestions right under the relevant
field, and they never block saving or exporting:

- **Summary length**: over ~60 words prompts "a bit long for a
  one-page resume, consider trimming to 2–3 sentences."
- **Sparse highlights**: an experience entry you've started filling in
  (has a company or role) but has only one bullet point prompts "Add
  1–2 more bullet points to strengthen this entry." A completely
  blank, freshly-added card stays quiet: no nagging before you've
  started.

## Multi-page resumes: smart page breaks

`src/lib/paginate.js` lays a long resume out over A4 pages, in the preview
and in the exported PDF alike. The templates mark their blocks with
`data-pg` attributes (`section`, `item`, `head`, `line`), and after every
change (and once web fonts have loaded) the preview measures them and
decides where each page starts:

- Every page keeps the same 48px top and bottom margin; nothing runs into
  the bottom margin or starts in the top one.
- A heading is never left alone at the bottom of a page: a section heading
  goes with its first entry, an entry's title row with its first bullet.
- A whole section or entry moves to the next page when at least half of it
  would end up there anyway, but only if that doesn't cost an extra page.
  Both outcomes are laid out and compared. Otherwise it splits between
  entries or bullets.
- A single last bullet is never carried over on its own (widow control).
- A resume that fits on one page is left exactly as it is.

Layout runs before the first paint and when you switch templates. While
you type, it is batched: it runs once typing pauses for ~160 ms, so each
keystroke stays cheap. Export PDF and Ctrl+P finish any pending layout
before the print dialog opens.

A block that moves gets `data-pg-pushed`. On screen that becomes a margin
(`--pg-m`) moving it to the next page in the preview; in print it becomes
`break-before: page` with the page's top margin, so the PDF breaks exactly
where the preview shows. Layout is skipped while printing, since print styles
would throw off the on-screen measurements.

The sheet is always a whole number of A4 pages tall (`--pg-count`, set by
the same code), so the accent ribbon and the Modern sidebar run to the
bottom of the last page. A badge above the preview and dashed red lines show
where pages start; both are hidden in the PDF. The page count is based on
where the last line of text ends, so the sheet only ever trims empty bottom
padding, which would otherwise print a blank extra page.

## Running the built app

`npm run build` writes `dist/`. Copy `serve.py` and `CV-Builder.bat` next to
`dist/index.html`, then double-click `CV-Builder.bat` (or run
`python serve.py`). It serves the app on http://localhost:8000 (localhost
only), opens the browser, and stops right away on Ctrl+C or when you close
the window. Plain `python -m http.server` often ignores Ctrl+C on Windows
while the browser has a connection open. The port stays 8000 because the
browser stores your resumes per address. If 8000 is already taken (an earlier
window still open), it just opens the browser to the running copy.

## Light / dark editor theme

The **Theme** toggle in the top bar switches the *editor chrome*
(top bar, sidebar, preview backdrop) between light and dark. This is
a separate token system (`--app-*` in `src/index.css`) from the one the
résumé itself uses (`--ink`, `--paper`, etc.), which never changes.
That's deliberate: a résumé should always look like a normal printable
document regardless of how you like your editor lit, and the print
stylesheet only ever renders `.resume-page` anyway. Your choice is
saved in `localStorage` alongside the rest of your settings.

## Section labels & language switching

`data.labels` holds the five section header strings shown on the resume
(`experience`, `education`, `certifications`, `skills`, `projects`). The **EN / NO** buttons
in the top bar (see `LANGUAGE_PRESETS` in `src/data/sampleData.js`) set all
five at once; the **Section labels** panel at the top of the editor lets
you override any of them by hand, useful for a language not in the
presets, or just a header you'd rather word differently ("Employment
History" instead of "Experience"). Old resumes saved in `localStorage`
before this feature existed are backfilled with the English defaults
automatically.

To add a new language preset, add an entry to `LANGUAGE_PRESETS` in
`src/data/sampleData.js`; the top bar picks it up automatically.

Note this only translates the section *headers*. Content you type
(job titles, bullet points, dates) stays exactly as written, so you're
free to write that in whatever language you like regardless of the
label preset. Custom section titles aren't part of this preset system
since you name them yourself.

## Hiding a section

Every reorderable section has an eye button in its header. Hiding a
section keeps everything you've written in the editor but leaves it off
the resume and the PDF; the header is struck through and marked "Hidden
from the resume" so it's easy to spot. Hidden keys are stored in
`data.hiddenSections` (saved in backups and templates too), and both
templates simply skip those keys when walking `sectionOrder`.

## Editing the same template in two places

When you load a saved resume, the app remembers which version of it you
opened (the file's modified time in a connected folder, or its saved
time in browser storage). Before "Update" overwrites it, the app checks
that version again. If another tab or device saved it in the meantime,
you get a choice instead of a silent overwrite: save yours as a copy
(which becomes the one you're editing), overwrite theirs, load their
version, or cancel. If the file was deleted elsewhere, you can save
yours as a new one.
