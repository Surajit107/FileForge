(() => {
  const motion = window.FileForgeMotion;
  const canAnimate = () => Boolean(motion && !motion.reduceMotion);
  const terminal = new Set(["done", "failed"]);

  const statusToneClass = (status) => {
    if (status === "done") return "is-ok";
    if (status === "failed") return "is-danger";
    return "is-warn";
  };

  const headingFor = (status) => {
    if (status === "done") return "Your file is ready";
    if (status === "failed") return "Conversion failed";
    if (status === "processing" || status === "pending") return "Converting your file";
    return "Conversion result";
  };

  const leadFor = (data) => {
    const name = data.original_name || "Your file";
    const source = (data.source_format || "").toUpperCase();
    const target = (data.target_format || "").toUpperCase();
    if (data.status === "done") {
      return target ? `${name} → ${target}` : name;
    }
    if (data.status === "failed") {
      return `We couldn’t finish converting ${name}.`;
    }
    if (source && target) {
      return `${name} · ${source} → ${target}`;
    }
    return "Conversion in progress…";
  };

  const bindJobPanel = (panel) => {
    if (!panel) return null;

    const statusLabel = panel.querySelector("#job-status-label");
    const headingEl = panel.querySelector("#job-heading");
    const leadEl = panel.querySelector("#job-lead");
    const errorEl = panel.querySelector("#job-error");
    const downloadWrap = panel.querySelector("#job-download");
    const downloadLink = panel.querySelector("#job-download-link");
    const downloadLabel = panel.querySelector("#job-download-label");
    const filenameEl = panel.querySelector("#job-filename");
    const pairEl = panel.querySelector("#job-pair");
    const expiresEl = panel.querySelector("#job-expires");
    const steps = [...panel.querySelectorAll(".progress-step")];
    let timer = null;
    let lastStatus = panel.dataset.status || "pending";
    let downloadRevealed = Boolean(
      downloadWrap && !downloadWrap.classList.contains("hidden")
    );

    const paintSteps = (status) => {
      const order = ["pending", "processing", "done"];
      let activeIndex = order.indexOf(status);
      if (status === "failed") activeIndex = 1;

      steps.forEach((step) => {
        const stepName = step.dataset.step;
        const stepIndex = order.indexOf(stepName);
        const wasActive = step.classList.contains("is-active");

        // Done = all complete (success). Never paint Ready as ember-active —
        // that competed with the download CTA.
        const isComplete =
          status === "done"
            ? stepIndex <= activeIndex
            : stepIndex < activeIndex && status !== "failed";
        const isActive =
          status === "failed"
            ? stepName === "processing"
            : status !== "done" && stepIndex === activeIndex;
        const isFailed = status === "failed" && stepName === "processing";

        step.classList.toggle("is-complete", isComplete);
        step.classList.toggle("is-active", isActive);
        step.classList.toggle("is-failed", isFailed);

        if (canAnimate() && isActive && !wasActive) {
          motion.pulse(step, { scale: [1, 1.04, 1], duration: 360 });
        }
      });
    };

    const revealDownload = () => {
      if (!downloadWrap || downloadRevealed) return;
      downloadRevealed = true;
      downloadWrap.classList.remove("hidden");
      if (!canAnimate()) return;
      motion.settleIn(downloadWrap);
      const btn = downloadWrap.querySelector(".btn-primary");
      if (btn) {
        motion.pulse(btn, { scale: [0.96, 1], duration: 420 });
      }
    };

    const revealError = () => {
      if (!errorEl) return;
      errorEl.classList.remove("hidden");
      if (!canAnimate()) return;
      motion.settleIn(errorEl);
    };

    const syncStage = (status, source, target) => {
      const stage = window.FileForgeConvertStage;
      if (!stage) return;
      if (source && target) {
        stage.syncFormats(source, target, panel);
      }
      if (status === "pending" || status === "processing") {
        stage.playConvert(panel);
        return;
      }
      stage.playIdle(panel);
      const statusEl = panel.querySelector("[data-convert-stage] [data-stage-status]");
      if (!statusEl) return;
      statusEl.textContent =
        status === "done" ? "Conversion complete" : "Conversion stopped";
    };

    const apply = (data) => {
      const statusChanged = data.status !== lastStatus;
      panel.dataset.status = data.status;
      if (data.status_url) {
        panel.dataset.statusUrl = data.status_url;
      }

      if (filenameEl && data.original_name) {
        filenameEl.textContent = data.original_name;
      }
      if (pairEl && data.source_format && data.target_format) {
        pairEl.textContent = `${data.source_format} → ${data.target_format}`;
      }
      if (expiresEl && data.expires_at) {
        expiresEl.textContent = data.expires_at;
      }

      if (headingEl) {
        headingEl.textContent = headingFor(data.status);
      }
      if (leadEl) {
        leadEl.textContent = leadFor(data);
      }

      if (statusLabel) {
        statusLabel.textContent = data.progress || data.status;
        statusLabel.className = `page-kicker job-result__eyebrow ${statusToneClass(data.status)}`;
        if (canAnimate() && statusChanged) {
          motion.pulse(statusLabel, { scale: [1, 1.04, 1], duration: 300 });
        }
      }

      if (statusChanged || data.source_format) {
        syncStage(data.status, data.source_format, data.target_format);
      }

      paintSteps(data.status);

      if (errorEl) {
        const failed = data.status === "failed";
        if (failed) {
          errorEl.textContent = data.error_message || "Conversion failed.";
          if (errorEl.classList.contains("hidden")) {
            revealError();
          }
        } else {
          errorEl.classList.add("hidden");
        }
      }

      if (downloadWrap && downloadLink) {
        const ready = Boolean(data.is_downloadable && data.download_url);
        if (ready) {
          downloadLink.href = data.download_url;
          if (downloadLabel) {
            downloadLabel.textContent = `Download ${(data.target_format || "").toUpperCase()}`;
          }
          revealDownload();
        } else {
          downloadWrap.classList.add("hidden");
          downloadRevealed = false;
        }
      }

      lastStatus = data.status;
    };

    const stop = () => {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    };

    const pollOnce = async () => {
      const statusUrl = panel.dataset.statusUrl;
      if (!statusUrl) return null;
      const response = await fetch(statusUrl, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return null;
      const data = await response.json();
      apply(data);
      return data;
    };

    const startPolling = () => {
      stop();
      const statusUrl = panel.dataset.statusUrl;
      if (!statusUrl) return;
      if (terminal.has(panel.dataset.status || "")) {
        paintSteps(panel.dataset.status || "pending");
        syncStage(
          panel.dataset.status || "pending",
          panel.querySelector("[data-stage-source]")?.textContent,
          panel.querySelector("[data-stage-target]")?.textContent
        );
        return;
      }
      paintSteps(panel.dataset.status || "pending");
      syncStage(panel.dataset.status || "pending");
      pollOnce();
      timer = window.setInterval(async () => {
        try {
          const data = await pollOnce();
          if (data && terminal.has(data.status)) {
            stop();
          }
        } catch (_) {
          // Keep polling; transient network blips are fine.
        }
      }, 1500);
    };

    return {
      apply,
      startPolling,
      stop,
      panel,
    };
  };

  const panel = document.getElementById("job-panel");
  const autoController =
    panel && panel.dataset.statusUrl ? bindJobPanel(panel) : null;
  if (autoController) {
    autoController.startPolling();
    window.addEventListener("beforeunload", () => autoController.stop());
  }

  window.FileForgeJobPanel = {
    bind: bindJobPanel,
  };
})();
