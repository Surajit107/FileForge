(() => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = dropzone?.querySelector('input[type="file"]');
  const fileName = document.getElementById("file-name");
  const targetSelect = document.getElementById("id_target_format");
  const pickerRoot = document.querySelector("[data-format-picker]");
  const form = document.getElementById("convert-form");
  const submitBtn = form?.querySelector('button[type="submit"].btn-primary');
  const motion = window.FileForgeMotion;
  const canAnimate = Boolean(motion && !motion.reduceMotion);

  if (!dropzone || !fileInput) return;

  let dragDepth = 0;

  const selectedFiles = () => [...(fileInput.files || [])];

  const showName = (files) => {
    const list = Array.isArray(files) ? files : files ? [files] : selectedFiles();
    if (!fileName || !list.length) return;
    fileName.textContent =
      list.length === 1 ? list[0].name : `${list.length} files selected`;
    fileName.classList.remove("hidden");
    if (canAnimate) {
      motion.settleIn(fileName);
    }
    const source = list[0].name.includes(".") ? list[0].name.split(".").pop() : "";
    const target = targetSelect?.value || "";
    if (source && target) {
      window.FileForgeConvertStage?.syncFormats?.(source, target);
    }
  };

  const createFormatPicker = (root, select) => {
    if (!root || !select) return null;

    const picker = root.querySelector(".format-picker");
    const trigger = root.querySelector("#format-trigger");
    const triggerValue = root.querySelector("#format-trigger-value");
    const panel = root.querySelector("#format-panel");
    const list = root.querySelector("#format-list");
    const searchInput = root.querySelector("#format-search");
    const emptyState = root.querySelector("#format-empty");

    if (!picker || !trigger || !panel || !list || !triggerValue) return null;

    let open = false;

    const optionNodes = () => [...list.querySelectorAll('[role="option"]')];

    const visibleOptions = () =>
      optionNodes().filter((node) => !node.classList.contains("is-filtered-out"));

    const syncFromSelect = () => {
      const value = select.value;
      optionNodes().forEach((node) => {
        const selected = node.dataset.value === value;
        node.setAttribute("aria-selected", selected ? "true" : "false");
      });
      triggerValue.textContent = value ? value.toUpperCase() : "—";
    };

    const setFilter = (query) => {
      const needle = query.trim().toLowerCase();
      let visibleCount = 0;

      optionNodes().forEach((node) => {
        const haystack = `${node.dataset.value ?? ""} ${node.dataset.label ?? ""}`.toLowerCase();
        const match = !needle || haystack.includes(needle);
        node.classList.toggle("is-filtered-out", !match);
        if (match) visibleCount += 1;
      });

      if (emptyState) {
        emptyState.hidden = visibleCount > 0;
      }
      list.hidden = visibleCount === 0;
    };

    const animatePanelOpen = () => {
      if (!canAnimate || !motion?.utils?.set || !motion?.animate) return;
      try {
        motion.utils.set(panel, {
          opacity: 0,
          translateY: -16,
          scaleY: 0.86,
          filter: "blur(6px)",
        });
        motion.animate(panel, {
          opacity: [0, 1],
          translateY: [-16, 0],
          scaleY: [0.86, 1.02, 1],
          filter: ["blur(6px)", "blur(0px)"],
          duration: 380,
          ease: "outBack(1.4)",
        });

        const options = visibleOptions();
        if (!options.length) return;
        motion.utils.set(options, { opacity: 0, scale: 0.75, translateY: 10 });
        motion.animate(options, {
          opacity: [0, 1],
          scale: [0.75, 1.06, 1],
          translateY: [10, 0],
          duration: 420,
          ease: "outBack(1.6)",
          delay: motion.stagger(32, { from: "center" }),
        });
      } catch (_) {
        // Keep the panel usable if motion fails.
        panel.style.opacity = "1";
      }
    };

    const setOpen = (nextOpen) => {
      if (open === nextOpen) return;
      open = nextOpen;
      root.classList.toggle("is-open", open);
      picker.classList.toggle("is-open", open);
      const currentTrigger = root.querySelector("#format-trigger") || trigger;
      currentTrigger.setAttribute("aria-expanded", open ? "true" : "false");
      panel.hidden = !open;

      if (open) {
        if (searchInput) {
          searchInput.value = "";
          setFilter("");
          searchInput.focus();
        }
        animatePanelOpen();
        return;
      }

      currentTrigger.focus();
    };

    const choose = (value, optionEl) => {
      if (![...select.options].some((opt) => opt.value === value)) return;
      select.value = value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      syncFromSelect();
      setOpen(false);

      if (canAnimate && motion?.pulse) {
        const currentTrigger = root.querySelector("#format-trigger");
        if (currentTrigger) {
          motion.animate(currentTrigger, {
            scaleX: [1, 0.12, 1],
            rotateY: [0, -55, 0],
            duration: 460,
            ease: "inOutCubic",
          });
        }
        if (optionEl) {
          motion.pulse(optionEl, {
            scale: [1, 1.12, 1],
            rotate: [0, -3, 0],
            duration: 360,
          });
        }
      }
    };

    const rebuildOptions = () => {
      list.replaceChildren();
      [...select.options].forEach((opt) => {
        const label = opt.textContent.trim();
        const item = document.createElement("li");
        item.className = "format-picker__option";
        item.setAttribute("role", "option");
        item.dataset.value = opt.value;
        item.dataset.label = label;
        item.setAttribute("aria-label", label);
        item.setAttribute(
          "aria-selected",
          opt.value === select.value ? "true" : "false"
        );
        item.tabIndex = -1;

        const code = document.createElement("span");
        code.className = "format-picker__option-code";
        code.textContent = opt.value.toUpperCase();
        item.appendChild(code);

        if (/best effort/i.test(label)) {
          const hint = document.createElement("span");
          hint.className = "format-picker__option-hint";
          hint.textContent = "best effort";
          item.appendChild(hint);
        }

        list.appendChild(item);
      });

      syncFromSelect();
      setFilter(searchInput?.value ?? "");

      if (canAnimate && open) {
        animatePanelOpen();
      } else if (canAnimate && motion?.animate) {
        const currentTrigger = root.querySelector("#format-trigger");
        if (currentTrigger) {
          motion.animate(currentTrigger, {
            scale: [1, 1.04, 1],
            rotate: [0, -1, 0],
            duration: 360,
            ease: "outBack(1.5)",
          });
        }
      }
    };

    // Delegate so bindings survive any later DOM swaps/clones.
    root.addEventListener("click", (event) => {
      if (event.target.closest("#format-trigger")) {
        event.preventDefault();
        setOpen(!open);
        return;
      }

      const option = event.target.closest('[role="option"]');
      if (!option || !list.contains(option) || option.classList.contains("is-filtered-out")) {
        return;
      }
      choose(option.dataset.value, option);
    });

    root.addEventListener("keydown", (event) => {
      if (event.target.closest("#format-trigger")) {
        if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          setOpen(true);
        }
        return;
      }

      if (event.target === searchInput) {
        const options = visibleOptions();
        if (event.key === "ArrowDown" && options[0]) {
          event.preventDefault();
          options[0].focus();
          return;
        }
        if (event.key === "Escape") {
          event.preventDefault();
          setOpen(false);
        }
        return;
      }

      if (!list.contains(event.target)) return;

      const options = visibleOptions();
      const currentIndex = options.indexOf(document.activeElement);
      if (currentIndex < 0) return;

      if (event.key === "ArrowRight" || event.key === "ArrowDown") {
        event.preventDefault();
        options[(currentIndex + 1) % options.length]?.focus();
        return;
      }

      if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
        event.preventDefault();
        if (currentIndex <= 0) {
          searchInput?.focus();
          return;
        }
        options[(currentIndex - 1 + options.length) % options.length]?.focus();
        return;
      }

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        choose(document.activeElement.dataset.value, document.activeElement);
        return;
      }

      if (event.key === "Escape") {
        event.preventDefault();
        setOpen(false);
      }
    });

    searchInput?.addEventListener("input", () => {
      setFilter(searchInput.value);
    });

    document.addEventListener("pointerdown", (event) => {
      if (!open) return;
      if (root.contains(event.target)) return;
      setOpen(false);
    });

    document.addEventListener("keydown", (event) => {
      if (!open || event.key !== "Escape") return;
      setOpen(false);
    });

    syncFromSelect();
    root.dataset.formatPickerReady = "true";

    return {
      rebuildOptions,
      syncFromSelect,
      setOpen,
    };
  };

  // Defer one frame so entrance-motion setup finishes before we bind.
  const bootPicker = () => createFormatPicker(pickerRoot, targetSelect);
  let formatPicker = null;
  if (pickerRoot && targetSelect) {
    formatPicker = bootPicker();
    if (!formatPicker) {
      requestAnimationFrame(() => {
        formatPicker = bootPicker();
      });
    }
  }

  const refreshTargets = async (filename) => {
    if (!targetSelect || !filename) return;
    try {
      const response = await fetch(
        `/api/formats/?filename=${encodeURIComponent(filename)}`
      );
      if (!response.ok) return;
      const data = await response.json();
      if (!Array.isArray(data.targets) || data.targets.length === 0) return;

      const previous = targetSelect.value;
      targetSelect.innerHTML = "";
      for (const target of data.targets) {
        const option = document.createElement("option");
        option.value = target.format;
        option.textContent = target.best_effort
          ? `${target.label} (best effort)`
          : target.label;
        targetSelect.appendChild(option);
      }
      if ([...targetSelect.options].some((opt) => opt.value === previous)) {
        targetSelect.value = previous;
      }
      formatPicker?.rebuildOptions();
    } catch (_) {
      // Keep server-rendered choices if the API is unavailable.
    }
  };

  const setDragState = (active) => {
    dropzone.classList.toggle("is-dragover", active);
    if (!canAnimate) return;
    motion.animate(dropzone, {
      scale: active ? 1.03 : 1,
      rotate: active ? -0.6 : 0,
      duration: 280,
      ease: "outBack(1.5)",
    });
  };

  fileInput.addEventListener("change", () => {
    const files = selectedFiles();
    showName(files);
    if (files[0]) refreshTargets(files[0].name);
  });

  dropzone.addEventListener("dragenter", (event) => {
    event.preventDefault();
    dragDepth += 1;
    setDragState(true);
  });

  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
  });

  dropzone.addEventListener("dragleave", (event) => {
    event.preventDefault();
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) setDragState(false);
  });

  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dragDepth = 0;
    setDragState(false);

    const dropped = [...(event.dataTransfer?.files || [])];
    if (!dropped.length) return;
    const transfer = new DataTransfer();
    dropped.forEach((file) => transfer.items.add(file));
    fileInput.files = transfer.files;
    showName(dropped);
    refreshTargets(dropped[0].name);

    if (canAnimate) {
      motion.animate(dropzone, {
        scale: [1, 1.05, 0.98, 1],
        rotate: [0, -1.2, 0.8, 0],
        duration: 560,
        ease: "outElastic(1, 0.75)",
      });
    }
  });

  const app = document.getElementById("convert-app");
  const viewForm = document.getElementById("view-form");
  const viewConverting = document.getElementById("view-converting");
  const viewResult = document.getElementById("view-result");
  const sourceErrors = document.getElementById("source-file-errors");
  const targetErrors = document.getElementById("target-format-errors");
  const formErrors = document.getElementById("form-errors");
  const MIN_CONVERT_MS = canAnimate ? 4200 : 600;
  const POLL_MS = 1000;
  let jobController = null;
  let submitting = false;

  const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

  const waitForPaint = () =>
    new Promise((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(resolve));
    });

  const currentFormats = () => {
    const file = selectedFiles()[0];
    const source = file?.name?.includes(".")
      ? file.name.split(".").pop()
      : "";
    const target = targetSelect?.value || "";
    return { source, target };
  };

  const syncStageFormats = (scope) => {
    const stage = window.FileForgeConvertStage;
    if (!stage?.syncFormats) return;
    const { source, target } = currentFormats();
    if (source && target) {
      stage.syncFormats(source, target, scope);
    }
  };

  const setErrorList = (el, messages) => {
    if (!el) return;
    el.replaceChildren();
    if (!messages?.length) {
      el.classList.add("hidden");
      return;
    }
    messages.forEach((message) => {
      const item = document.createElement("li");
      item.textContent = message;
      el.appendChild(item);
    });
    el.classList.remove("hidden");
  };

  const clearFormErrors = () => {
    setErrorList(sourceErrors, []);
    setErrorList(targetErrors, []);
    setErrorList(formErrors, []);
  };

  const applyFormErrors = (errors = {}, message = "") => {
    const fieldMessage = (field) =>
      (errors[field] || []).map((entry) => entry.message || String(entry));

    setErrorList(sourceErrors, fieldMessage("source_file"));
    setErrorList(targetErrors, fieldMessage("target_format"));

    const nonField = fieldMessage("__all__");
    if (message && !nonField.length) nonField.push(message);
    setErrorList(formErrors, nonField);
  };

  const setView = (name) => {
    if (!app) return;
    app.dataset.view = name;
    const map = {
      form: viewForm,
      converting: viewConverting,
      result: viewResult,
    };
    Object.entries(map).forEach(([key, node]) => {
      if (!node) return;
      const active = key === name;
      node.hidden = !active;
      node.classList.toggle("is-active-view", active);
      if (active) {
        node.style.opacity = "1";
        node.style.transform = "none";
        if (canAnimate && motion?.utils?.set && motion?.animate) {
          motion.utils.set(node, {
            opacity: 0,
            translateY: 22,
            scale: 0.96,
            filter: "blur(8px)",
          });
          motion.animate(node, {
            opacity: [0, 1],
            translateY: [22, 0],
            scale: [0.96, 1],
            filter: ["blur(8px)", "blur(0px)"],
            duration: 520,
            ease: "outExpo",
          });
        } else if (motion?.utils?.set) {
          motion.utils.set(node, {
            opacity: 1,
            translateX: 0,
            translateY: 0,
            scale: 1,
            filter: "blur(0px)",
          });
        }
      }
    });
  };

  const showConverting = async () => {
    setView("converting");
    syncStageFormats("#view-converting");
    await waitForPaint();
    window.FileForgeConvertStage?.playConvert?.("#view-converting");
  };

  const showResult = (job) => {
    const panel = document.getElementById("job-panel");
    if (!panel || !window.FileForgeJobPanel?.bind) {
      // Stay on-page if possible; only hard-navigate as last resort.
      if (job.detail_url) window.location.assign(job.detail_url);
      return;
    }

    jobController?.stop?.();
    jobController = window.FileForgeJobPanel.bind(panel);
    jobController.apply(job);
    setView("result");
    window.FileForgeConvertStage?.syncFormats?.(
      job.source_format,
      job.target_format,
      "#view-result"
    );
    window.FileForgeConvertStage?.playIdle?.("#view-result");

    // Update URL after the result is already visible — never during the convert anim.
    if (job.detail_url) {
      window.history.replaceState({ jobId: job.id }, "", job.detail_url);
    }

    if (!["done", "failed"].includes(job.status)) {
      jobController.startPolling();
    }
  };

  const resetToForm = () => {
    jobController?.stop?.();
    jobController = null;
    submitting = false;
    submitBtn?.classList.remove("is-busy");
    clearFormErrors();
    setView("form");
    window.FileForgeConvertStage?.playIdle?.("#view-form");
    if (window.location.pathname !== "/") {
      window.history.replaceState({}, "", "/");
    }
  };

  const waitForTerminalJob = async (job) => {
    let current = job;
    const terminal = new Set(["done", "failed", "partial"]);
    while (!terminal.has(current.status) && current.status_url) {
      await sleep(POLL_MS);
      const response = await fetch(current.status_url, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) continue;
      current = await response.json();
    }
    return current;
  };

  targetSelect?.addEventListener("change", syncStageFormats);

  document.getElementById("job-convert-another")?.addEventListener("click", (event) => {
    if (!app) return;
    event.preventDefault();
    resetToForm();
  });

  window.addEventListener("popstate", () => {
    if (!app) return;
    if (window.location.pathname === "/" || window.location.pathname === "") {
      resetToForm();
    }
  });

  if (form && submitBtn) {
    form.addEventListener("submit", async (event) => {
      // Always block native navigation when the SPA shell is present.
      event.preventDefault();
      if (!app || submitting) return;
      if (!window.fetch || !window.FormData) return;

      submitting = true;
      clearFormErrors();
      submitBtn.classList.add("is-busy");

      if (canAnimate) {
        motion.animate(submitBtn, {
          scale: [1, 0.92, 1.04, 1],
          rotate: [0, -1.5, 1, 0],
          duration: 420,
          ease: "outBack(1.7)",
        });
      }

      const startedAt = Date.now();
      await showConverting();

      try {
        const response = await fetch(form.action || window.location.pathname || "/", {
          method: "POST",
          body: new FormData(form),
          headers: {
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        const data = await response.json().catch(() => ({}));
        const result = data.job || data.result;
        if (!response.ok || !data.ok || !result) {
          setView("form");
          window.FileForgeConvertStage?.playIdle?.("#view-form");
          applyFormErrors(
            data.errors || {},
            data.message || (response.status === 429 ? "Too many conversions." : "Conversion failed.")
          );
          return;
        }

        // Conversion is often done in <500ms. Hold the converting scene until
        // both the job is terminal AND the animation has had time to play.
        const holdMs = Math.max(0, MIN_CONVERT_MS - (Date.now() - startedAt));
        const [job] = await Promise.all([
          waitForTerminalJob(result),
          sleep(holdMs),
        ]);

        showResult(job);
      } catch (_) {
        setView("form");
        window.FileForgeConvertStage?.playIdle?.("#view-form");
        applyFormErrors({}, "Network error while converting. Try again.");
      } finally {
        submitting = false;
        submitBtn.classList.remove("is-busy");
      }
    });
  }
})();
