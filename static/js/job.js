(() => {
  const motion = window.FileForgeMotion;
  const canAnimate = () => Boolean(motion && !motion.reduceMotion);
  const terminal = new Set(["done", "failed", "partial"]);

  const statusToneClass = (status) => {
    if (status === "done" || status === "partial") return "is-ok";
    if (status === "failed") return "is-danger";
    return "is-warn";
  };

  const headingFor = (status, kind) => {
    const plural = kind === "batch";
    if (status === "done" || status === "partial") {
      return plural ? "Your files are ready" : "Your file is ready";
    }
    if (status === "failed") return "Conversion failed";
    if (status === "processing" || status === "pending") {
      return plural ? "Converting your files" : "Converting your file";
    }
    return "Conversion result";
  };

  const leadFor = (data) => {
    const name = data.original_name || "Your file";
    const source = (data.source_format || "").toUpperCase();
    const target = (data.target_format || "").toUpperCase();
    const isBatch = data.kind === "batch";
    if (data.status === "done" || data.status === "partial") {
      if (isBatch && target) return `${name} → ${target} (ZIP)`;
      return target ? `${name} → ${target}` : name;
    }
    if (data.status === "failed") {
      return isBatch
        ? "We couldn’t finish converting this batch."
        : `We couldn’t finish converting ${name}.`;
    }
    if (isBatch && target) {
      return `${name} · → ${target}`;
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
    const previewWrap = panel.querySelector("#job-preview");
    const previewButton = panel.querySelector("#job-preview-button");
    const previewDialog = panel.querySelector("#preview-dialog");
    const previewTitle = panel.querySelector("#preview-dialog-title");
    const previewFullscreenBtn = panel.querySelector("[data-preview-fullscreen]");
    const previewFrame = panel.querySelector("[data-preview-frame]");
    const previewImage = panel.querySelector("[data-preview-image]");
    const previewText = panel.querySelector("[data-preview-text]");
    const previewStatus = panel.querySelector("[data-preview-status]");
    const filenameEl = panel.querySelector("#job-filename");
    const pairEl = panel.querySelector("#job-pair");
    const expiresEl = panel.querySelector("#job-expires");
    const steps = [...panel.querySelectorAll(".progress-step")];
    let timer = null;
    let lastStatus = panel.dataset.status || "pending";
    let downloadRevealed = Boolean(
      downloadWrap && !downloadWrap.classList.contains("hidden")
    );
    let previewRevealed = Boolean(
      previewWrap && !previewWrap.classList.contains("hidden")
    );
    let previewObjectUrl = null;

    const revokePreviewObjectUrl = () => {
      if (!previewObjectUrl) return;
      URL.revokeObjectURL(previewObjectUrl);
      previewObjectUrl = null;
    };

    const clearPreviewSurfaces = () => {
      revokePreviewObjectUrl();
      if (previewFrame) {
        previewFrame.classList.add("hidden");
        previewFrame.removeAttribute("src");
        previewFrame.removeAttribute("sandbox");
      }
      if (previewImage) {
        previewImage.classList.add("hidden");
        previewImage.removeAttribute("src");
      }
      if (previewText) {
        previewText.classList.add("hidden");
        previewText.textContent = "";
      }
      if (previewStatus) {
        previewStatus.classList.add("hidden");
        previewStatus.textContent = "Loading preview…";
      }
    };

    const setPreviewFullscreen = (enabled) => {
      if (!previewDialog) return;
      previewDialog.classList.toggle("is-fullscreen", enabled);
      if (previewFullscreenBtn) {
        previewFullscreenBtn.setAttribute("aria-pressed", enabled ? "true" : "false");
        previewFullscreenBtn.setAttribute(
          "aria-label",
          enabled ? "Exit full screen" : "Enter full screen"
        );
        previewFullscreenBtn.title = enabled ? "Exit full screen" : "Full screen";
      }
    };

    const closePreview = () => {
      if (!previewDialog) return;
      setPreviewFullscreen(false);
      if (typeof previewDialog.close === "function" && previewDialog.open) {
        previewDialog.close();
      }
      clearPreviewSurfaces();
    };

    const showPreviewStatus = (message) => {
      clearPreviewSurfaces();
      if (!previewStatus) return;
      previewStatus.textContent = message;
      previewStatus.classList.remove("hidden");
    };

    const openPreview = async () => {
      if (!previewDialog || !previewButton) return;
      const url = previewButton.dataset.previewUrl || "";
      const mode = previewButton.dataset.previewMode || "";
      const name = previewButton.dataset.previewName || "Converted file";
      if (!url || !mode) return;

      if (previewTitle) previewTitle.textContent = name;
      clearPreviewSurfaces();
      showPreviewStatus("Loading preview…");
      if (typeof previewDialog.showModal === "function") {
        previewDialog.showModal();
      } else {
        previewDialog.setAttribute("open", "");
      }

      try {
        if (mode === "image" && previewImage) {
          previewStatus?.classList.add("hidden");
          previewImage.src = url;
          previewImage.classList.remove("hidden");
          return;
        }

        if ((mode === "pdf" || mode === "html") && previewFrame) {
          // Fetch → blob URL avoids X-Frame-Options: DENY blocking the modal iframe
          // on production (site-wide clickjacking protection still applies elsewhere).
          const response = await fetch(url, {
            credentials: "same-origin",
            headers: { Accept: mode === "pdf" ? "application/pdf" : "text/html" },
          });
          if (!response.ok) throw new Error("Preview failed");
          const blob = await response.blob();
          revokePreviewObjectUrl();
          previewObjectUrl = URL.createObjectURL(blob);
          previewStatus?.classList.add("hidden");
          if (mode === "html") {
            previewFrame.setAttribute("sandbox", "");
          } else {
            previewFrame.removeAttribute("sandbox");
          }
          previewFrame.src = previewObjectUrl;
          previewFrame.classList.remove("hidden");
          return;
        }

        if (mode === "text" && previewText) {
          const response = await fetch(url, { headers: { Accept: "text/plain" } });
          if (!response.ok) throw new Error("Preview failed");
          const text = await response.text();
          previewStatus?.classList.add("hidden");
          previewText.textContent = text;
          previewText.classList.remove("hidden");
          return;
        }

        showPreviewStatus("Preview is not available for this format.");
      } catch (_) {
        showPreviewStatus("Could not load preview. Try downloading the file.");
      }
    };

    previewButton?.addEventListener("click", () => {
      openPreview();
    });
    previewFullscreenBtn?.addEventListener("click", () => {
      const next = !previewDialog?.classList.contains("is-fullscreen");
      setPreviewFullscreen(next);
    });
    panel.querySelectorAll("[data-preview-close]").forEach((node) => {
      node.addEventListener("click", closePreview);
    });
    previewDialog?.addEventListener("cancel", (event) => {
      event.preventDefault();
      // First Escape exits fullscreen; second closes the modal.
      if (previewDialog.classList.contains("is-fullscreen")) {
        setPreviewFullscreen(false);
        return;
      }
      closePreview();
    });
    previewDialog?.addEventListener("click", (event) => {
      if (event.target === previewDialog) closePreview();
    });

    const paintSteps = (status) => {
      const order = ["pending", "processing", "done"];
      let activeIndex = order.indexOf(status);
      if (status === "partial") activeIndex = 2;
      if (status === "failed") activeIndex = 1;

      steps.forEach((step) => {
        const stepName = step.dataset.step;
        const stepIndex = order.indexOf(stepName);
        const wasActive = step.classList.contains("is-active");

        // Done = all complete (success). Never paint Ready as ember-active —
        // that competed with the download CTA.
        const finished = status === "done" || status === "partial";
        const isComplete =
          finished
            ? stepIndex <= activeIndex
            : stepIndex < activeIndex && status !== "failed";
        const isActive =
          status === "failed"
            ? stepName === "processing"
            : !finished && stepIndex === activeIndex;
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

    const revealPreview = () => {
      if (!previewWrap || previewRevealed) return;
      previewRevealed = true;
      previewWrap.classList.remove("hidden");
      if (!canAnimate()) return;
      motion.settleIn(previewWrap);
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
        status === "done" || status === "partial"
          ? "Conversion complete"
          : "Conversion stopped";
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
        headingEl.textContent = headingFor(data.status, data.kind);
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
        const failed = data.status === "failed" || data.status === "partial";
        if (failed && data.error_message) {
          errorEl.textContent = data.error_message;
          if (errorEl.classList.contains("hidden")) {
            revealError();
          }
        } else if (data.status === "failed") {
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
            downloadLabel.textContent =
              data.kind === "batch"
                ? "Download ZIP"
                : `Download ${(data.target_format || "").toUpperCase()}`;
          }
          revealDownload();
        } else {
          downloadWrap.classList.add("hidden");
          downloadRevealed = false;
        }
      }

      if (previewWrap && previewButton) {
        const canPreview = Boolean(
          data.kind === "job" &&
            data.is_downloadable &&
            data.preview_url &&
            data.preview_mode
        );
        if (canPreview) {
          previewButton.dataset.previewUrl = data.preview_url;
          previewButton.dataset.previewMode = data.preview_mode;
          previewButton.dataset.previewName = `${data.original_name || "File"} → ${(
            data.target_format || ""
          ).toUpperCase()}`;
          revealPreview();
        } else {
          previewWrap.classList.add("hidden");
          previewRevealed = false;
          previewButton.dataset.previewUrl = "";
          previewButton.dataset.previewMode = "";
          closePreview();
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
