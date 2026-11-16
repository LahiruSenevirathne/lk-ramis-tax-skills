/*
 * RAMIS IIT return, "Statement of assets & liabilities" tab: row filler for
 *   - shares   : Part 1 "iii. Shares/stocks/securities as at 31.03.YYYY"  (#gridStatement1B3)
 *   - disposals: Part 2 "B. Disposal of assets including shares (sale/transfer/gift)
 *                during the year"                                        (#gridStatement2B)
 *
 * Run in the page context of
 * https://eservices.ird.gov.lk/Assessment/IIT2/IITSimplifiedReturn, AFTER the
 * user has given an explicit go-ahead.
 *
 * Per section it only ever clicks two controls:
 *   #btnStatement<ID>AddRow  "Add Row" (opens the shared editor window)
 *   #btnStatement<ID>Add     the editor's "Add" (commits the row to the grid)
 * It never clicks Save draft, Next, Back, Cancel, Submit, Remove, Update or Reset.
 * Nothing is saved to the IRD until the user presses Save draft themselves.
 *
 * Usage (one JavaScript evaluation per step; keep chunks to ~8 rows):
 *   1. Paste this file once to define window.ramisStocks.
 *   2. ramisStocks.existing('shares')                 // or 'disposals'
 *   3. await ramisStocks.addOne('shares', row)        // ONE row; check ok:true
 *   4. await ramisStocks.addMany('shares', chunk)     // stops on the first problem
 *   5. ramisStocks.existing('shares')                 // read back and compare
 *
 * Row shapes (dates "YYYY-MM-DD" or null; amounts numbers or null):
 *   shares    { type, company, shares, date, value, dividend }
 *   disposals { type, description, disposal_date, proceeds, acquired, cost }
 * type is "A" (local, default) or "B" (foreign).
 *
 * Field ids were observed on the 2025/26 return and may change in later years.
 * If a selector is missing, stop and inspect the page instead of guessing.
 */
(() => {
  const $ = window.jQuery;
  if (!$) throw new Error('jQuery not found: is this the RAMIS return page?');

  // key -> [field, widget kind]; kind is text | number | date
  const SECTIONS = {
    shares: {
      id: '1B3',
      fields: {
        company: ['Sta_Cage1014', 'text'],
        shares: ['Sta_Cage1015', 'text'],
        date: ['Sta_Cage1016', 'date'],
        value: ['Sta_Cage1017', 'number'],
        dividend: ['Sta_Cage1018', 'number'],
      },
    },
    disposals: {
      id: '2B',
      fields: {
        description: ['Sta_Cage1035', 'text'],
        disposal_date: ['Sta_Cage1036', 'date'],
        proceeds: ['Sta_Cage1037', 'number'],
        acquired: ['Sta_Cage1038', 'date'],
        cost: ['Sta_Cage1039', 'number'],
      },
    },
  };

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const iso = (d) => (d ? new Date(d).toLocaleDateString('en-CA') : null);
  const near = (a, b) => (a == null && b == null) ||
    (a != null && b != null && Math.abs(Number(a) - Number(b)) < 0.005);

  const sec = (name) => {
    const s = SECTIONS[name];
    if (!s) throw new Error('unknown section ' + name + ' (use shares | disposals)');
    return s;
  };
  const sel = (s, f) => '#StatementPart' + s.id + 'Model_' + f;
  const grid = (s) => {
    const g = $('#gridStatement' + s.id).data('kendoGrid');
    if (!g) throw new Error('#gridStatement' + s.id + ' grid not found');
    return g;
  };
  const live = (s) => grid(s).dataSource.data().filter((d) => !d.IsDeleted);
  // "Add Row" moves the editor fields into a shared Kendo window
  // (#statementWindow); the section's own DIV stays hidden, so test the fields.
  const panelOpen = (s) => {
    const first = Object.values(s.fields)[0][0];
    const el = document.querySelector(sel(s, first));
    return !!(el && el.offsetParent !== null);
  };
  const errText = (s) =>
    ((document.getElementById('Statement' + s.id + 'Error') || {}).innerText || '').trim();

  const widget = (s, f, kind) => {
    const w = $(sel(s, f)).data(kind);
    if (!w) throw new Error(f + ' ' + kind + ' not found');
    return w;
  };
  const setField = (s, f, kind, v) => {
    if (kind === 'text') {
      if (!$(sel(s, f)).length) throw new Error('field ' + f + ' not found');
      $(sel(s, f)).val(v == null ? '' : String(v)).trigger('change');
    } else if (kind === 'number') {
      const w = widget(s, f, 'kendoNumericTextBox');
      w.value(v == null || v === '' ? null : Number(v));
      w.trigger('change');
    } else {
      const w = widget(s, f, 'kendoDatePicker');
      if (!v) w.value(null);
      else { const [y, m, d] = v.split('-').map(Number); w.value(new Date(y, m - 1, d)); }
      w.trigger('change');
    }
  };
  const matches = (s, d, r) => Object.entries(s.fields).every(([k, [f, kind]]) => {
    const want = r[k] == null || r[k] === '' ? null : r[k];
    if (kind === 'number') return near(d[f], want);
    if (kind === 'date') return iso(d[f]) === want;
    // RAMIS upper-cases some text fields (e.g. the disposal Description).
    return String(d[f] == null ? '' : d[f]).toUpperCase() === String(want == null ? '' : want).toUpperCase();
  });

  async function addOne(name, r) {
    const s = sec(name);
    const before = live(s).length;
    if (!panelOpen(s)) {
      const btn = document.getElementById('btnStatement' + s.id + 'AddRow');
      if (!btn) throw new Error('#btnStatement' + s.id + 'AddRow not found');
      btn.click();
      await sleep(800);
    }
    if (!panelOpen(s)) throw new Error('editor did not open for ' + name);

    const t = widget(s, 'Sta_AssetType', 'kendoDropDownList');
    t.value(r.type || 'A');
    t.trigger('change');
    for (const [k, [f, kind]] of Object.entries(s.fields)) setField(s, f, kind, r[k]);
    await sleep(300);

    const add = document.getElementById('btnStatement' + s.id + 'Add');
    if (!add) throw new Error('#btnStatement' + s.id + 'Add not found');
    add.click();
    await sleep(1200);

    const rows = live(s);
    const hit = rows.some((d) => matches(s, d, r));
    return {
      section: name, label: r.company || r.description,
      ok: rows.length === before + 1 && hit && !errText(s),
      before, after: rows.length, found: hit,
      error: errText(s) || undefined, editorStillOpen: panelOpen(s),
    };
  }

  async function addMany(name, list) {
    const log = [];
    for (const r of list) {
      const res = await addOne(name, r);
      log.push(res);
      if (!res.ok) break;
    }
    return log;
  }

  const existing = (name) => {
    const s = sec(name);
    return live(s).map((d) => {
      const o = { sn: d.SerialNo, type: d.Sta_AssetType };
      for (const [k, [f, kind]] of Object.entries(s.fields)) o[k] = kind === 'date' ? iso(d[f]) : d[f];
      return o;
    });
  };

  window.ramisStocks = { existing, addOne, addMany, SECTIONS };
  return 'ramisStocks ready';
})();
