// Skrip pendukung aplikasi SPK
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

  // Skala Saaty 1-9 untuk perbandingan AHP
  var SAATY_SCALE = [
    { val: -8, label: "9", ratio: "9:1", text: "mutlak lebih penting (9x)", side: "left" },
    { val: -7, label: "8", ratio: "8:1", text: "mendekati mutlak lebih penting (8x)", side: "left" },
    { val: -6, label: "7", ratio: "7:1", text: "sangat jelas lebih penting (7x)", side: "left" },
    { val: -5, label: "6", ratio: "6:1", text: "mendekati sangat penting (6x)", side: "left" },
    { val: -4, label: "5", ratio: "5:1", text: "jelas lebih penting (5x)", side: "left" },
    { val: -3, label: "4", ratio: "4:1", text: "mendekati lebih penting (4x)", side: "left" },
    { val: -2, label: "3", ratio: "3:1", text: "sedikit lebih penting (3x)", side: "left" },
    { val: -1, label: "2", ratio: "2:1", text: "mendekati sedikit lebih penting (2x)", side: "left" },
    { val: 0,  label: "1", ratio: "1:1", text: "sama pentingnya (seimbang 1:1)", side: "center" },
    { val: 1,  label: "1/2", ratio: "1:2", text: "mendekati sedikit lebih penting (2x)", side: "right" },
    { val: 2,  label: "1/3", ratio: "1:3", text: "sedikit lebih penting (3x)", side: "right" },
    { val: 3,  label: "1/4", ratio: "1:4", text: "mendekati lebih penting (4x)", side: "right" },
    { val: 4,  label: "1/5", ratio: "1:5", text: "jelas lebih penting (5x)", side: "right" },
    { val: 5,  label: "1/6", ratio: "1:6", text: "mendekati sangat penting (6x)", side: "right" },
    { val: 6,  label: "1/7", ratio: "1:7", text: "sangat jelas lebih penting (7x)", side: "right" },
    { val: 7,  label: "1/8", ratio: "1:8", text: "mendekati mutlak lebih penting (8x)", side: "right" },
    { val: 8,  label: "1/9", ratio: "1:9", text: "mutlak lebih penting (9x)", side: "right" }
  ];

  function getScaleByVal(val) {
    var v = parseInt(val, 10);
    for (var i = 0; i < SAATY_SCALE.length; i++) {
      if (SAATY_SCALE[i].val === v) return SAATY_SCALE[i];
    }
    return SAATY_SCALE[8];
  }

  function getScaleByLabel(lbl) {
    var clean = String(lbl).trim();
    for (var i = 0; i < SAATY_SCALE.length; i++) {
      if (SAATY_SCALE[i].label === clean) return SAATY_SCALE[i];
    }
    return SAATY_SCALE[8];
  }

  function reciprocal(label) {
    if (label === "1") return "1";
    return label.indexOf("1/") === 0 ? label.slice(2) : "1/" + label;
  }

  // Perbarui kalimat narasi dan status visual pada kartu slider
  function updateCardVerdict(card, scaleItem) {
    if (!card) return;
    var nameLeft = card.dataset.nameLeft || "";
    var codeLeft = card.dataset.codeLeft || "";
    var nameRight = card.dataset.nameRight || "";
    var codeRight = card.dataset.codeRight || "";
    var verdict = card.querySelector(".ahp-verdict");
    if (!verdict) return;

    verdict.className = "ahp-verdict side-" + scaleItem.side;
    if (scaleItem.side === "center") {
      verdict.innerHTML = '<strong>' + codeLeft + '</strong> dan <strong>' + codeRight + '</strong> sama pentingnya <span class="badge-ratio">(1 : 1)</span>';
    } else if (scaleItem.side === "left") {
      verdict.innerHTML = '<strong>' + codeLeft + ' (' + nameLeft + ')</strong> ' + scaleItem.text + ' dibanding ' + codeRight + ' <span class="badge-ratio">(' + scaleItem.ratio + ')</span>';
    } else {
      verdict.innerHTML = '<strong>' + codeRight + ' (' + nameRight + ')</strong> ' + scaleItem.text + ' dibanding ' + codeLeft + ' <span class="badge-ratio">(' + scaleItem.ratio + ')</span>';
    }

    // Ubah visual border / glow pada kartu berdasarkan sisi
    card.classList.remove("focus-left", "focus-right", "focus-center");
    card.classList.add("focus-" + scaleItem.side);
  }

  // Sinkronisasi Slider -> Matriks & Narasi
  function setupAhpSliders() {
    var sliders = document.querySelectorAll(".ahp-slider");
    if (!sliders.length) return;

    sliders.forEach(function (slider) {
      var i = slider.dataset.i;
      var j = slider.dataset.j;
      var card = document.getElementById("card_" + i + "_" + j);

      function applyChange(val, syncSelect) {
        var scale = getScaleByVal(val);
        updateCardVerdict(card, scale);

        if (syncSelect) {
          var sel = document.getElementById("sel_" + i + "_" + j) ||
                    document.querySelector('select[name="a_' + i + '_' + j + '"]');
          if (sel) sel.value = scale.label;

          var cell = document.getElementById("r_" + j + "_" + i);
          if (cell) cell.textContent = reciprocal(scale.label);
        }
      }

      // Event saat slider digeser secara real-time
      slider.addEventListener("input", function () {
        applyChange(slider.value, true);
      });

      // Inisialisasi awal tampilan narasi
      applyChange(slider.value, false);
    });

    // Sinkronisasi Tabel Matriks -> Slider
    document.querySelectorAll("select[data-i][data-j]").forEach(function (sel) {
      sel.addEventListener("change", function () {
        var i = sel.dataset.i;
        var j = sel.dataset.j;
        var scale = getScaleByLabel(sel.value);

        var slider = document.getElementById("slider_" + i + "_" + j);
        if (slider) slider.value = scale.val;

        var card = document.getElementById("card_" + i + "_" + j);
        if (card) updateCardVerdict(card, scale);

        var cell = document.getElementById("r_" + j + "_" + i);
        if (cell) cell.textContent = reciprocal(sel.value);
      });
    });

    // Tombol: Set Seimbang (1:1) per kartu
    document.querySelectorAll(".btn-reset-pair").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var i = btn.dataset.i;
        var j = btn.dataset.j;
        var slider = document.getElementById("slider_" + i + "_" + j);
        if (slider) {
          slider.value = 0;
          slider.dispatchEvent(new Event("input"));
        }
      });
    });

    // Tombol: Reset Semua ke 1:1
    var btnResetAll = document.getElementById("btn-reset-all");
    if (btnResetAll) {
      btnResetAll.addEventListener("click", function () {
        if (!window.confirm("Reset semua perbandingan kriteria ke Seimbang (1:1)?")) return;
        sliders.forEach(function (s) {
          s.value = 0;
          s.dispatchEvent(new Event("input"));
        });
      });
    }

    // Tombol: Terapkan Saran Inkonsistensi (implied value)
    document.querySelectorAll(".btn-apply-implied").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var targetI = btn.dataset.targetI;
        var targetJ = btn.dataset.targetJ;
        var val = btn.dataset.val;
        var scale = getScaleByLabel(val);

        var slider = document.getElementById("slider_" + targetI + "_" + targetJ);
        if (slider) {
          slider.value = scale.val;
          slider.dispatchEvent(new Event("input"));
        }

        // Tampilkan feedback visual pada tombol
        var originalText = btn.textContent;
        btn.textContent = "✓ Diterapkan";
        btn.classList.add("btn-applied");
        setTimeout(function () {
          btn.textContent = originalText;
          btn.classList.remove("btn-applied");
        }, 1500);
      });
    });

    // Pengalih Mode Tampilan (Slider vs Matriks)
    var btnSlider = document.getElementById("btn-mode-slider");
    var btnMatrix = document.getElementById("btn-mode-matrix");
    var viewSlider = document.getElementById("view-slider");
    var viewMatrix = document.getElementById("view-matrix");

    function switchMode(mode) {
      if (mode === "matrix") {
        btnSlider.classList.remove("is-active");
        btnSlider.setAttribute("aria-selected", "false");
        btnMatrix.classList.add("is-active");
        btnMatrix.setAttribute("aria-selected", "true");
        viewSlider.classList.remove("is-active");
        viewMatrix.classList.add("is-active");
      } else {
        btnMatrix.classList.remove("is-active");
        btnMatrix.setAttribute("aria-selected", "false");
        btnSlider.classList.add("is-active");
        btnSlider.setAttribute("aria-selected", "true");
        viewMatrix.classList.remove("is-active");
        viewSlider.classList.add("is-active");
      }
    }

    if (btnSlider && btnMatrix) {
      btnSlider.addEventListener("click", function () { switchMode("slider"); });
      btnMatrix.addEventListener("click", function () { switchMode("matrix"); });
    }

    // Filter Chips: Fokus kriteria tertentu
    var chips = document.querySelectorAll(".filter-chips-list .chip");
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        chips.forEach(function (c) { c.classList.remove("is-active"); });
        chip.classList.add("is-active");

        var filterVal = chip.dataset.filter;
        var cards = document.querySelectorAll(".ahp-card");
        cards.forEach(function (card) {
          if (filterVal === "all") {
            card.style.display = "";
          } else {
            var i = card.dataset.pairI;
            var j = card.dataset.pairJ;
            if (i === filterVal || j === filterVal) {
              card.style.display = "";
            } else {
              card.style.display = "none";
            }
          }
        });
      });
    });
  }

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

  // Jalankan inisialisasi AHP Slider saat DOM siap
  setupAhpSliders();
})();
