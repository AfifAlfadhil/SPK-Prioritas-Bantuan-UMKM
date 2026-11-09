// Skrip pendukung: semua halaman tetap berfungsi tanpa JavaScript.
(function () {
  "use strict";

  // Konfirmasi sebelum kirim formulir / klik tombol.
  document.addEventListener("submit", function (e) {
    var msg = e.target.getAttribute("data-confirm");
    if (msg && !window.confirm(msg)) e.preventDefault();
  });
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-confirm-click]");
    if (btn && !window.confirm(btn.getAttribute("data-confirm-click"))) e.preventDefault();
    var pr = e.target.closest("[data-print]");
    if (pr) { e.preventDefault(); window.print(); }
  });

  // Matriks AHP: sel kebalikan ikut berubah saat nilai dipilih.
  function reciprocal(label) {
    if (label === "1") return "1";
    return label.indexOf("1/") === 0 ? label.slice(2) : "1/" + label;
  }
  document.querySelectorAll("select[data-i][data-j]").forEach(function (sel) {
    sel.addEventListener("change", function () {
      var cell = document.getElementById("r_" + sel.dataset.j + "_" + sel.dataset.i);
      if (cell) cell.textContent = reciprocal(sel.value);
    });
  });

  // Pemilihan alternatif: pilih semua / kosongkan, saring baris, hitung terpilih.
  var boxes = Array.prototype.slice.call(document.querySelectorAll("input[name=pilih]"));
  var counter = document.getElementById("picked-count");
  function updateCount() {
    if (counter) counter.textContent = boxes.filter(function (b) { return b.checked; }).length;
  }
  boxes.forEach(function (b) { b.addEventListener("change", updateCount); });
  document.querySelectorAll("[data-check]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var on = btn.dataset.check === "all";
      boxes.forEach(function (b) {
        if (!b.disabled && b.closest("tr").style.display !== "none") b.checked = on;
      });
      updateCount();
    });
  });
  var filter = document.getElementById("row-filter");
  if (filter) {
    filter.addEventListener("input", function () {
      var q = filter.value.trim().toLowerCase();
      document.querySelectorAll("tr[data-text]").forEach(function (tr) {
        tr.style.display = !q || tr.dataset.text.indexOf(q) !== -1 ? "" : "none";
      });
    });
  }
  updateCount();
})();
