/*
 * RAMIS IIT return, "Statement of assets & liabilities" tab: generic row filler.
 *
 * Sections (see SECTIONS below): property (Part 01 A), bank (Part 01 B ii),
 * shares (Part 01 B iii), liabilities (Part 01 D), acquired (Part 02 A),
 * disposals (Part 02 B).
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
 *   1. Paste this file once to define window.ramisStocks (alias window.ramisStatement).
 *   2. ramisStatement.existing('bank')
 *   3. await ramisStatement.addOne('bank', row)       // ONE row; check ok:true
 *   4. await ramisStatement.addMany('bank', chunk)    // stops on the first problem
 *   5. ramisStatement.existing('bank')                // read back and compare
 *
 * Row keys per section are the keys of SECTIONS[section].fields, plus
 * type "A" (local, default) or "B" (foreign). Dates "YYYY-MM-DD" or null.
 */
(() => {
  const $ = window.jQuery;
  if (!$) throw new Error('jQuery not found: is this the RAMIS return page?');

  // key -> [field, widget kind]; kind is text | number | date
  // One entry per grid on the "Statement of assets & liabilities" tab that a
  // skill in this collection fills. Field ids observed on the Y/A 2025/26 return.
  const SECTIONS = {
    property: {   // Part 01 A  Immovable Properties
      id: '1A',
      fields: {
        situation: ['Sta_Cage1001', 'text'],
        date: ['Sta_Cage1002', 'date'],
        cost: ['Sta_Cage1003', 'number'],
        market_value: ['Sta_Cage1004', 'number'],
      },
    },
    bank: {       // Part 01 B ii  Bank balances including term deposits
      id: '1B2',
      fields: {
        institution: ['Sta_Cage1009', 'text'],
        account: ['Sta_Cage1010', 'text'],
        invested: ['Sta_Cage1011', 'number'],
        interest: ['Sta_Cage1012', 'number'],
        balance: ['Sta_Cage1013', 'number'],
      },
    },
    shares: {     // Part 01 B iii  Shares/stocks/securities
      id: '1B3',
      fields: {
        company: ['Sta_Cage1014', 'text'],
        shares: ['Sta_Cage1015', 'text'],
        date: ['Sta_Cage1016', 'date'],
        value: ['Sta_Cage1017', 'number'],
        dividend: ['Sta_Cage1018', 'number'],
      },
    },
    liabilities: { // Part 01 D  Liabilities as at end of the Y/A
      id: '1D',
      fields: {
        description: ['Sta_Cage1025', 'text'],
        security: ['Sta_Cage1026', 'text'],
        commenced: ['Sta_Cage1027', 'date'],
        original: ['Sta_Cage1028', 'number'],
        outstanding: ['Sta_Cage1029', 'number'],
        repaid: ['Sta_Cage1030', 'number'],
      },
    },
    acquired: {   // Part 02 A  Any other assets acquired or gifts received during the year
      id: '2A',
      fields: {
        description: ['Sta_Cage1031', 'text'],
        how: ['Sta_Cage1032', 'text'],
        date: ['Sta_Cage1033', 'date'],
        value: ['Sta_Cage1034', 'number'],
      },
    },
    disposals: {  // Part 02 B  Disposal of assets including shares
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
    if (!s) throw new Error('unknown section ' + name + ' (use ' + Object.keys(SECTIONS).join(' | ') + ')');
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
      section: name, label: r.company || r.description || r.situation || r.institution,
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

  window.ramisStocks = window.ramisStatement = { existing, addOne, addMany, SECTIONS };
  return 'ramisStatement ready: ' + Object.keys(SECTIONS).join(', ');
})();
