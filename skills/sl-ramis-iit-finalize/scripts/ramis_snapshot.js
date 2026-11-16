/*
 * READ-ONLY snapshot of a RAMIS IIT return for review and record-keeping.
 *
 * Run in the page context of the user's return
 * (https://eservices.ird.gov.lk/Assessment/IIT2/IITSimplifiedReturn or the
 * standard return). It clicks nothing, changes nothing and sends nothing. It only
 * reads the Kendo grids and numeric/checkbox fields that are already in the page
 * (RAMIS keeps every tab of the return in the DOM).
 *
 * Usage (one JavaScript evaluation per step):
 *   1. Paste this file:  returns {chars, chunks}
 *   2. ramisSnapshot.chunk(0), chunk(1), … : concatenate the strings in order
 *      into one file (e.g. ramis/snapshot.json). Browser tools truncate long
 *      results, hence the chunks.
 *   3. (only with the user's OK) ramisSnapshot.download() saves the same JSON
 *      through a normal browser download, instead of assembling chunks.
 *   4. ramisSnapshot.capture() again later to refresh.
 *
 * Privacy: digit runs of 6 or more inside text (account, certificate, NIC and
 * TIN numbers) are masked to their last 4 digits ("…1234"), and the characters
 * = & ? % are replaced. Amounts (numbers) are kept as numbers.
 *
 * Shape: {captured, page, tabs, header:{label: value}, grids:[{id, tab, title,
 *         columns:[[field, title, kind]], rows:[[values…]]}],
 *         fields:[[tab, id, label, value]], checkboxes:[[tab, label, checked]]}
 */
(() => {
  const $ = window.jQuery;
  if (!$) throw new Error('jQuery not found: is this the RAMIS return page?');
  const CHUNK = 900;

  const clean = (t) => String(t == null ? '' : t)
    .replace(/\d{6,}/g, (m) => '…' + m.slice(-4))
    .replace(/&/g, ' and ').replace(/[=?%]/g, ' ')
    .replace(/\s+/g, ' ').trim();
  const val = (v) => {
    if (v == null || v === '') return null;
    if (v instanceof Date) return v.toLocaleDateString('en-CA');
    if (typeof v === 'number' || typeof v === 'boolean') return v;
    return clean(v);
  };
  const panes = [...document.querySelectorAll('[role=tabpanel]')];
  const tabNames = [...document.querySelectorAll('[role=tab]')].map((t) => clean(t.innerText));
  const tabOf = (el) => {
    const p = el.closest('[role=tabpanel]');
    const i = panes.indexOf(p);
    return i >= 0 ? (tabNames[i] || 'tab ' + i) : '';
  };
  const titleOf = (g) => {
    // nearest heading-like text before the grid
    let el = g;
    for (let hops = 0; el && hops < 40; hops++) {
      let prev = el.previousElementSibling;
      while (prev) {
        const h = prev.matches('h1,h2,h3,h4,b,strong,label,legend,p,div,span') ? prev : null;
        const t = h ? clean(h.innerText) : '';
        if (t && t.length < 160 && /[A-Za-z]{3}/.test(t) && !/^(Add Row|Remove)/.test(t)) return t.split(' | ')[0];
        prev = prev.previousElementSibling;
      }
      el = el.parentElement;
    }
    return '';
  };
  const labelOf = (input) => {
    const lab = document.querySelector('label[for="' + input.id + '"]');
    if (lab) return clean(lab.innerText);
    const tr = input.closest('tr');
    if (tr) return clean([...tr.querySelectorAll('td,th,label,span')]
      .filter((x) => !x.childElementCount).map((x) => x.innerText).join(' ')
      .replace(/Increase value|Decrease value/g, ''));
    return '';
  };

  function capture() {
    const grids = [...document.querySelectorAll('div[id]')]
      .filter((g) => $(g).data('kendoGrid'))
      .map((g) => {
        const kg = $(g).data('kendoGrid');
        const model = (kg.dataSource.options.schema && kg.dataSource.options.schema.model
          && kg.dataSource.options.schema.model.fields) || {};
        const cols = kg.columns.filter((c) => c.field && c.field !== 'SerialNo')
          .map((c) => [c.field, clean((c.title || '').replace(/<[^>]+>/g, ' ')), (model[c.field] || {}).type || '']);
        const rows = kg.dataSource.data().filter((d) => !d.IsDeleted)
          .map((d) => cols.map(([f]) => val(d[f])));
        return { id: g.id.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}$/, '*'), tab: tabOf(g), title: titleOf(g), columns: cols, rows };
      });
    const inGrid = (el) => !!el.closest('.k-window, [id^=Statement][id$=DIV]');
    const fields = [...document.querySelectorAll('input[data-role=numerictextbox]')]
      .filter((i) => !inGrid(i) && !/Model_/.test(i.id))
      .map((i) => { const w = $(i).data('kendoNumericTextBox'); return [tabOf(i), i.id, labelOf(i), w ? w.value() : null]; })
      .filter((f) => f[3] != null && f[3] !== 0);
    const checkboxes = [...document.querySelectorAll('input[type=checkbox]')]
      .filter((c) => !c.closest('.k-grid') && c.id && !/select.*All/i.test(c.id))
      .map((c) => [tabOf(c), labelOf(c) || clean(c.parentElement && c.parentElement.innerText), c.checked]);
    const header = {};
    document.querySelectorAll('td, th, label').forEach((td) => {
      const t = clean(td.innerText);
      if (/^(Taxpayer Identification Number|Name of taxpayer|Year of assessment)/i.test(t) && td.nextElementSibling) {
        header[t.replace(/\s*\(.*\)$/, '')] = clean(td.nextElementSibling.innerText);
      }
    });
    const snap = { captured: new Date().toISOString(), page: location.pathname, tabs: tabNames, header, grids, fields, checkboxes };
    window.__ramisSnap = JSON.stringify(snap);
    return { chars: window.__ramisSnap.length, chunks: Math.ceil(window.__ramisSnap.length / CHUNK),
      grids: grids.map((g) => g.id + ':' + g.rows.length).join(', ') };
  }

  // Only with the user's explicit OK: saves the (masked) snapshot as a JSON file
  // through the browser's normal download (usually ~/Downloads). Nothing is sent
  // anywhere else.
  const download = (name) => {
    const blob = new Blob([window.__ramisSnap || '{}'], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name || ('ramis-snapshot-' + new Date().toISOString().slice(0, 10) + '.json');
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    return a.download;
  };

  window.ramisSnapshot = {
    capture,
    download,
    chunk: (i) => (window.__ramisSnap || '').slice(i * CHUNK, (i + 1) * CHUNK),
  };
  return capture();
})();
