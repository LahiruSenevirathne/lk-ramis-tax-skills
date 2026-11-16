/*
 * RAMIS Schedule 7 "Interest Income - A" row filler.
 *
 * Run in the page context of the RAMIS IIT return
 * (https://eservices.ird.gov.lk/Assessment/IIT2/IITSimplifiedReturn) with the
 * Interest Income table visible, AFTER the user has given an explicit go-ahead.
 *
 * It only ever clicks two controls:
 *   #btnS7A     the table's "Add" button (opens the pop-up)
 *   #btnS7AAdd  the pop-up's "Add" button (adds the row to the table)
 * It never clicks Save draft, Next, Submit, Remove, Update or Reset.
 * Nothing is saved to the IRD until the user presses Save draft themselves.
 *
 * Usage (one JavaScript evaluation per step; each row takes ~2 s and browser
 * tools usually time out at ~45 s, so send at most 8-10 rows per call):
 *
 *   1. Paste this file once to define window.ramisS7.
 *   2. await ramisS7.existing()            // rows already in the table
 *   3. await ramisS7.addOne(row)           // add ONE row, check the result
 *   4. await ramisS7.addMany(rows.slice(0, 8))  // then chunks; stops on first problem
 *   5. ramisS7.existing()                  // read back everything and compare
 *
 * A row is: { tin, agent, cert, amount, date, ait, source }
 *   tin     "134008059"            withholding agent TIN (cage 702)
 *   agent   "NATIONS TRUST BANK"   agent name, as RAMIS shows it (cage 707)
 *   cert    "WHT/2025/APR/..."     certificate number (cage 703)
 *   amount  724.75                 gross interest (cage 704)
 *   date    "2025-05-15" | ""      date of payment, YYYY-MM-DD (cage 705)
 *   ait     72.48                  AIT deducted (cage 706)
 *   source  "I-INTEREST"           source/type (cage 701), optional
 *
 * Field ids were observed on the 2025/26 return and may change in later years.
 * If a selector is missing, stop and inspect the pop-up instead of guessing.
 */
(() => {
  const P = '#Schedule7_Schedule7AModel_Sch7_2021Cage';
  const NAME = '#Schedule7_Schedule7AModel_Sch7_2526Cage707';
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const $ = window.jQuery;
  if (!$) throw new Error('jQuery not found: is this the RAMIS return page?');

  const tableRows = () =>
    [...document.querySelectorAll('tr')]
      .filter((t) => /I-INTEREST/.test(t.innerText))
      .map((t) => [...t.cells].slice(1).map((c) => c.innerText.trim()));

  const openPopups = () =>
    [...document.querySelectorAll('.k-window')].filter((x) => x.offsetParent !== null).length;

  const fmt = (n) => Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const setNumeric = (cage, v) => {
    const w = $(P + cage).data('kendoNumericTextBox');
    if (!w) throw new Error('numeric box ' + cage + ' not found');
    w.value(Number(v));
    w.trigger('change');
  };

  const setText = (sel, v) => {
    if (!$(sel).length) throw new Error('field ' + sel + ' not found');
    $(sel).val(v).trigger('change');
  };

  const setDate = (v) => {
    const d = $(P + '705').data('kendoDatePicker');
    if (!d) throw new Error('date picker 705 not found');
    if (!v) { d.value(null); d.trigger('change'); return; }
    const [y, m, dd] = v.split('-').map(Number);
    d.value(new Date(y, m - 1, dd));
    d.trigger('change');
  };

  async function addOne(r) {
    const before = tableRows().length;
    const btn = document.getElementById('btnS7A');
    if (!btn) throw new Error('#btnS7A (table Add button) not found');
    btn.click();
    await sleep(800);
    if (!openPopups()) throw new Error('pop-up did not open');

    setText(P + '701', r.source || 'I-INTEREST');
    setNumeric('702', r.tin);
    setText(NAME, r.agent);
    setText(P + '703', r.cert);
    setNumeric('704', r.amount);
    setDate(r.date || '');
    setNumeric('706', r.ait);
    await sleep(300);

    const add = document.getElementById('btnS7AAdd');
    if (!add) throw new Error('#btnS7AAdd (pop-up Add button) not found');
    add.click();
    await sleep(1200);

    const rows = tableRows();
    const found = rows.some((c) => c.includes(r.cert) && c.includes(fmt(r.amount)) && c.includes(fmt(r.ait)));
    return {
      cert: r.cert, amount: r.amount,
      ok: rows.length === before + 1 && found && openPopups() === 0,
      before, after: rows.length, found, popupStillOpen: openPopups() > 0,
    };
  }

  async function addMany(list) {
    const log = [];
    for (const r of list) {
      const res = await addOne(r);
      log.push(res);
      if (!res.ok) break; // stop on the first problem and report
    }
    return log;
  }

  window.ramisS7 = {
    existing: () => tableRows().map((c) => ({
      source: c[0], tin: c[1], agent: c[2], cert: c[3], amount: c[4], date: c[5], ait: c[6],
    })),
    addOne,
    addMany,
  };
  return 'ramisS7 ready';
})();
