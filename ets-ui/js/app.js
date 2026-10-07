(function () {
  "use strict";
  var latestBtn = document.getElementById("latestBtn");
  var refreshBtn = document.getElementById("refreshBtn");
  var dirBtn = document.getElementById("dirBtn");
  var resetBtn = document.getElementById("resetBtn");
  var curDir = document.getElementById("curDir");
  var pathInfo = document.getElementById("pathInfo");
  var statusEl = document.getElementById("status");
  var paperList = document.getElementById("paperList");
  var viewerTitle = document.getElementById("viewerTitle");
  var countsEl = document.getElementById("counts");
  var copyBtn = document.getElementById("copyBtn");
  var downloadBtn = document.getElementById("downloadBtn");
  var sectionsEl = document.getElementById("sections");
  var dirModal = document.getElementById("dirModal");
  var modalCur = document.getElementById("modalCur");
  var dirInput = document.getElementById("dirInput");
  var dirCancel = document.getElementById("dirCancel");
  var dirSave = document.getElementById("dirSave");
  var dirMsg = document.getElementById("dirMsg");

  var papers = [];
  var current = null;
  var currentText = "";

  var TYPE_NAMES = { choose: "听后选择", role: "听后回答", picture: "听后转述", read: "朗读短文", word: "词汇", repeat_essay: "背诵短文", repeat_dialogue: "背诵对话" };
  var TYPE_ORDER = ["choose", "role", "picture", "read"];

  function setStatus(s) { statusEl.textContent = s || ""; }

  function loadPapers() {
    pathInfo.textContent = "加载中…";
    setStatus("");
    fetch("/api/papers").then(function (r) { return r.json(); }).then(function (list) {
      papers = list;
      pathInfo.textContent = "共 " + papers.length + " 套试卷";
      renderList();
      if (papers.length) selectPaper(papers[0].id);
      else showEmpty("数据目录下未找到试卷");
    }).catch(function () {
      pathInfo.textContent = "连接失败";
      showEmpty("无法连接本地服务，请确认服务已启动");
    });
  }

  function loadDir() {
    fetch("/api/current-dir").then(function (r) { return r.json(); }).then(function (d) {
      curDir.textContent = d.root;
    }).catch(function () { curDir.textContent = "读取失败"; });
  }

  latestBtn.addEventListener("click", function () {
    if (!papers.length) { setStatus("列表为空"); return; }
    selectPaper(papers[0].id);
  });
  refreshBtn.addEventListener("click", function () { loadDir(); loadPapers(); });

  dirBtn.addEventListener("click", function () {
    dirInput.value = curDir.textContent === "加载中…" ? "" : curDir.textContent;
    modalCur.textContent = curDir.textContent;
    dirMsg.textContent = "";
    dirModal.classList.remove("hidden");
    dirInput.focus();
    dirInput.select();
  });

  function closeModal() { dirModal.classList.add("hidden"); }

  dirCancel.addEventListener("click", closeModal);
  dirModal.addEventListener("click", function (e) { if (e.target === dirModal) closeModal(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !dirModal.classList.contains("hidden")) closeModal(); });

  dirSave.addEventListener("click", function () {
    var d = dirInput.value.trim();
    if (!d) { dirMsg.textContent = "请输入目录路径"; return; }
    dirSave.disabled = true;
    dirMsg.textContent = "";
    fetch("/api/set-dir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dir: d })
    }).then(function (r) { return r.json(); }).then(function (res) {
      dirSave.disabled = false;
      if (res.error) { dirMsg.textContent = res.error; return; }
      curDir.textContent = res.root;
      closeModal();
      loadPapers();
    }).catch(function () {
      dirSave.disabled = false;
      dirMsg.textContent = "保存失败";
    });
  });

  resetBtn.addEventListener("click", function () {
    fetch("/api/reset-dir", { method: "POST" }).then(function (r) { return r.json(); }).then(function (res) {
      if (res.error) { setStatus(res.error); return; }
      curDir.textContent = res.root;
      setStatus("已恢复默认目录");
      loadPapers();
    }).catch(function () { setStatus("恢复失败"); });
  });

  function renderList() {
    paperList.innerHTML = "";
    papers.forEach(function (p, i) {
      var li = document.createElement("li");
      li.dataset.pid = p.id;
      li.setAttribute("role", "button");
      li.setAttribute("tabindex", "0");
      li.setAttribute("aria-label", p.id + (i === 0 ? "（最新）" : ""));
      if (p.id === current) li.classList.add("active");
      var pid = document.createElement("div");
      pid.className = "pid";
      pid.textContent = p.id;
      if (i === 0) {
        var b = document.createElement("span");
        b.className = "badge";
        b.textContent = "最新";
        pid.appendChild(b);
      }
      li.appendChild(pid);
      var meta = document.createElement("div");
      meta.className = "meta";
      meta.innerHTML = typeSummary(p.counts);
      li.appendChild(meta);
      (function (id) {
        li.addEventListener("click", function () { selectPaper(id); });
        li.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectPaper(id); }
        });
      })(p.id);
      paperList.appendChild(li);
    });
    if (!papers.length) {
      var e = document.createElement("li");
      e.textContent = "（无试卷）";
      e.style.color = "#67806f";
      paperList.appendChild(e);
    }
  }

  function typeSummary(counts) {
    var arr = TYPE_ORDER.concat(Object.keys(counts).filter(function (s) { return TYPE_ORDER.indexOf(s) < 0; }));
    var parts = [];
    arr.forEach(function (s) {
      if (counts[s]) parts.push((TYPE_NAMES[s] || s) + "×" + counts[s]);
    });
    return parts.join(" · ") || "无内容";
  }

  function selectPaper(id) {
    setStatus("读取中…");
    fetch("/api/paper?id=" + encodeURIComponent(id)).then(function (r) { return r.json(); }).then(function (d) {
      if (d.error) { setStatus("读取失败"); return; }
      current = id;
      currentText = d.rawText;
      viewerTitle.textContent = "试卷 " + id;
      countsEl.textContent = typeSummary(d.counts);
      copyBtn.disabled = false;
      downloadBtn.disabled = false;
      sectionsEl.innerHTML = "";
      d.sections.forEach(function (s) {
        var sec = document.createElement("div");
        sec.className = "sec";
        var h = document.createElement("h3");
        h.textContent = s.title;
        sec.appendChild(h);
        var pre = document.createElement("pre");
        pre.textContent = s.text;
        sec.appendChild(pre);
        sectionsEl.appendChild(sec);
      });
      Array.prototype.forEach.call(paperList.children, function (li) {
        li.classList.toggle("active", li.dataset.pid === id);
      });
      setStatus("完成");
    }).catch(function () { setStatus("读取失败"); });
  }

  function showEmpty(msg) {
    current = null;
    currentText = "";
    copyBtn.disabled = true;
    downloadBtn.disabled = true;
    viewerTitle.textContent = "未选择试卷";
    countsEl.textContent = "";
    sectionsEl.innerHTML = "<div class=\"empty\">" + msg + "</div>";
  }

  function txtCRLF() { return currentText.replace(/\n/g, "\r\n"); }

  copyBtn.addEventListener("click", function () {
    if (!currentText) return;
    var done = function () { setStatus("已复制"); setTimeout(function () { setStatus(""); }, 1500); };
    var t = txtCRLF();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(t).then(done, function () { fallbackCopy(t, done); });
    } else { fallbackCopy(t, done); }
  });

  function fallbackCopy(t, done) {
    var ta = document.createElement("textarea");
    ta.value = t;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
    done();
  }

  downloadBtn.addEventListener("click", function () {
    if (!currentText) return;
    var blob = new Blob(["\ufeff" + txtCRLF()], { type: "text/plain;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = current + ".txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
    setStatus("已下载 " + a.download);
    setTimeout(function () { setStatus(""); }, 2000);
  });

  loadDir();
  loadPapers();
})();
