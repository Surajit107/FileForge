(() => {
  const motion = window.FileForgeMotion;
  const stages = [...document.querySelectorAll("[data-convert-stage]")];
  if (!stages.length) return;

  const FALLBACK_PAIRS = [
    ["MD", "PDF"],
    ["DOCX", "MD"],
    ["PDF", "DOCX"],
    ["MD", "DOCX"],
    ["DOCX", "PDF"],
  ];

  const readPairs = (root) => {
    // Job-bound stages must lock to their formats. Never steal from page-wide
    // pair chips (those live on the convert form and caused DOCX↔PDF flicker).
    const source = (root.dataset.sourceFormat || "").toUpperCase();
    const target = (root.dataset.targetFormat || "").toUpperCase();
    if (source && target) return [[source, target]];
    if (root.dataset.locked === "true") return [["—", "—"]];

    const fromDom = [...document.querySelectorAll(".pair-chip")]
      .map((chip) => {
        const codes = [...chip.querySelectorAll("code")].map((el) =>
          el.textContent.trim().toUpperCase()
        );
        return codes.length >= 2 ? [codes[0], codes[1]] : null;
      })
      .filter(Boolean);

    if (fromDom.length) return fromDom;
    return FALLBACK_PAIRS;
  };

  const streamTravelPx = (stream) => {
    const width = stream?.clientWidth || 0;
    // % translate is relative to the particle itself — useless. Use real track width.
    return Math.max(width - 12, 96);
  };

  const waitForLayout = () =>
    new Promise((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(resolve);
      });
    });

  const bootStage = (root) => {
    const sourceExt = root.querySelector("[data-stage-source]");
    const targetExt = root.querySelector("[data-stage-target]");
    const sourceCard = root.querySelector("[data-stage-source-card]");
    const targetCard = root.querySelector("[data-stage-target-card]");
    const stream = root.querySelector("[data-stage-stream]");
    const status = root.querySelector("[data-stage-status]");
    const glow = root.querySelector("[data-stage-glow]");
    const reduceMotion =
      !motion ||
      motion.reduceMotion ||
      document.documentElement.classList.contains("reduce-motion");

    if (!sourceExt || !targetExt || !stream) return null;

    let pairs = readPairs(root);
    let pairIndex = 0;
    let converting = root.dataset.mode === "converting";
    const isFormatsLocked = () =>
      root.dataset.locked === "true" &&
      Boolean(root.dataset.sourceFormat && root.dataset.targetFormat);
    /** @type {Array<{pause?: Function, cancel?: Function, revert?: Function}>} */
    const loops = [];
    let pairTimer = 0;
    let progressRaf = 0;

    const setPair = (source, target) => {
      sourceExt.textContent = source;
      targetExt.textContent = target;
      root.dataset.sourceFormat = source.toLowerCase();
      root.dataset.targetFormat = target.toLowerCase();
    };

    const [initialSource, initialTarget] = pairs[0];
    setPair(initialSource, initialTarget);

    if (!stream.querySelector(".convert-stage__track")) {
      const track = document.createElement("span");
      track.className = "convert-stage__track";
      track.setAttribute("aria-hidden", "true");
      stream.appendChild(track);
    }

    const clearParticles = () => {
      [...stream.querySelectorAll(".convert-stage__particle")].forEach((node) =>
        node.remove()
      );
    };

    const rebuildParticles = (count) => {
      clearParticles();
      return Array.from({ length: count }, (_, index) => {
        const node = document.createElement("span");
        node.className = "convert-stage__particle";
        node.style.setProperty("--i", String(index));
        stream.appendChild(node);
        return node;
      });
    };

    const clearMorph = () => {
      stream.querySelector(".convert-stage__morph")?.remove();
    };

    const clearProgress = () => {
      root.querySelector("[data-stage-progress]")?.remove();
    };

    const ensureMorph = () => {
      clearParticles();
      let morph = stream.querySelector(".convert-stage__morph");
      if (!morph) {
        morph = document.createElement("span");
        morph.className = "convert-stage__morph";
        morph.setAttribute("aria-hidden", "true");
        morph.innerHTML = `
          <span class="convert-stage__morph-ring"></span>
          <span class="convert-stage__morph-card">
            <span class="convert-stage__morph-face is-from" data-morph-from></span>
            <span class="convert-stage__morph-face is-to" data-morph-to></span>
          </span>
        `;
        stream.appendChild(morph);
      }

      const from = morph.querySelector("[data-morph-from]");
      const to = morph.querySelector("[data-morph-to]");
      if (from) from.textContent = sourceExt.textContent || "—";
      if (to) to.textContent = targetExt.textContent || "—";
      return morph;
    };

    const ensureProgress = () => {
      let progress = root.querySelector("[data-stage-progress]");
      if (progress) return progress;

      progress = document.createElement("div");
      progress.className = "job-pair__progress";
      progress.setAttribute("data-stage-progress", "");
      progress.setAttribute("aria-hidden", "true");
      progress.innerHTML = `
        <div class="job-pair__progress-row">
          <span class="job-pair__progress-track">
            <span class="job-pair__progress-fill" data-progress-fill></span>
            <span class="job-pair__progress-sheen" aria-hidden="true"></span>
          </span>
          <span class="job-pair__progress-pct" data-progress-pct>0%</span>
        </div>
      `;

      if (status?.parentNode === root) {
        root.insertBefore(progress, status);
      } else {
        root.appendChild(progress);
      }
      return progress;
    };

    const setProgressPct = (value) => {
      const label = root.querySelector("[data-progress-pct]");
      if (!label) return;
      const clamped = Math.max(0, Math.min(99, Math.round(value)));
      label.textContent = `${clamped}%`;
    };

    let particles = converting ? [] : rebuildParticles(4);

    const setStatus = (text) => {
      if (status) status.textContent = text;
    };

    const clearLoops = () => {
      if (pairTimer) {
        window.clearInterval(pairTimer);
        pairTimer = 0;
      }
      if (progressRaf) {
        window.cancelAnimationFrame(progressRaf);
        progressRaf = 0;
      }
      while (loops.length) {
        const anim = loops.pop();
        try {
          anim?.pause?.();
          anim?.cancel?.();
          anim?.revert?.();
        } catch (_) {
          // Ignore teardown errors from already-finished animations.
        }
      }
    };

    const resetCards = () => {
      [sourceCard, targetCard].forEach((card) => {
        if (!card || !motion?.utils) return;
        motion.utils.set(card, {
          translateX: 0,
          translateY: 0,
          scale: 1,
          scaleX: 1,
          scaleY: 1,
          rotate: 0,
          rotateY: 0,
          opacity: 1,
        });
      });
    };

    /** Idle: soft orbit + slow drifting motes (preview / showcase). */
    const animateIdleParticles = () => {
      const travel = streamTravelPx(stream);
      particles.forEach((particle, index) => {
        const drift = 6 + (index % 2) * 4;
        const duration = 2200 + index * 180;
        motion.utils.set(particle, {
          opacity: 0,
          translateX: 0,
          translateY: 0,
          scale: 0.4,
          rotate: 0,
        });
        loops.push(
          motion.animate(particle, {
            opacity: [
              { to: 0, duration: 0 },
              { to: 0.85, duration: 220 },
              { to: 0.85, duration: duration * 0.55 },
              { to: 0, duration: 280 },
            ],
            translateX: [
              { to: travel * 0.45, duration: duration * 0.45, ease: "inOutSine" },
              { to: travel, duration: duration * 0.55, ease: "inOutSine" },
            ],
            translateY: [
              { to: index % 2 === 0 ? -drift : drift, duration: duration * 0.5 },
              { to: index % 2 === 0 ? drift * 0.4 : -drift * 0.4, duration: duration * 0.5 },
            ],
            scale: [
              { to: 1, duration: duration * 0.35 },
              { to: 0.55, duration: duration * 0.65 },
            ],
            delay: index * 420,
            ease: "linear",
            loop: true,
          })
        );
      });
    };

    const flipCard = (card, direction) => {
      if (!card || !motion?.animate) return;
      motion.animate(card, {
        rotateY: [0, direction * 78, 0],
        scaleX: [1, 0.12, 1],
        duration: 560,
        ease: "inOutCubic",
      });
    };

    const runIdleLoop = async () => {
      if (reduceMotion || !motion?.animate) {
        setStatus(
          isFormatsLocked() ? "Conversion complete" : "Format transformation preview"
        );
        return;
      }

      clearLoops();
      resetCards();
      clearMorph();
      clearProgress();
      root.classList.remove("is-converting");
      root.dataset.mode = "idle";

      // Locked job stages stay still — no format carousel, no bounce.
      if (isFormatsLocked()) {
        const panelStatus = root.closest("[data-status]")?.dataset.status;
        setStatus(
          panelStatus === "failed" ? "Conversion stopped" : "Conversion complete"
        );
        if (glow) {
          motion.utils.set(glow, { opacity: 0.18, scale: 1, translateX: 0 });
        }
        clearParticles();
        particles = [];
        return;
      }

      setStatus("Formats transform continuously");
      particles = rebuildParticles(4);
      await waitForLayout();
      if (converting) return;

      // Source: slow counter-orbit (calm showcase).
      if (sourceCard) {
        loops.push(
          motion.animate(sourceCard, {
            translateY: [
              { to: -7, duration: 1800 },
              { to: 4, duration: 1900 },
              { to: 0, duration: 1600 },
            ],
            translateX: [
              { to: -2, duration: 1700 },
              { to: 3, duration: 1800 },
              { to: 0, duration: 1700 },
            ],
            rotate: [
              { to: -5, duration: 2000 },
              { to: 2, duration: 1800 },
              { to: -2, duration: 1700 },
              { to: 0, duration: 1500 },
            ],
            ease: "inOutSine",
            loop: true,
          })
        );
      }

      // Target: mirrored orbit, slightly out of phase.
      if (targetCard) {
        loops.push(
          motion.animate(targetCard, {
            translateY: [
              { to: 6, duration: 1700 },
              { to: -8, duration: 1900 },
              { to: 0, duration: 1700 },
            ],
            translateX: [
              { to: 3, duration: 1800 },
              { to: -2, duration: 1700 },
              { to: 0, duration: 1800 },
            ],
            rotate: [
              { to: 5, duration: 1900 },
              { to: -3, duration: 1800 },
              { to: 2, duration: 1600 },
              { to: 0, duration: 1500 },
            ],
            ease: "inOutSine",
            loop: true,
            delay: 220,
          })
        );
      }

      // Glow breathes and drifts along the bridge.
      if (glow) {
        loops.push(
          motion.animate(glow, {
            opacity: [
              { to: 0.42, duration: 1800 },
              { to: 0.18, duration: 2000 },
              { to: 0.35, duration: 1700 },
            ],
            scale: [
              { to: 1.12, duration: 2000 },
              { to: 0.9, duration: 1900 },
              { to: 1, duration: 1700 },
            ],
            translateX: [
              { to: -10, duration: 2400 },
              { to: 12, duration: 2600 },
              { to: 0, duration: 2200 },
            ],
            ease: "inOutSine",
            loop: true,
          })
        );
      }

      animateIdleParticles();

      if (pairs.length < 2) return;

      pairTimer = window.setInterval(() => {
        if (converting) return;
        pairIndex = (pairIndex + 1) % pairs.length;
        const [nextSource, nextTarget] = pairs[pairIndex];
        setPair(nextSource, nextTarget);
        flipCard(sourceCard, -1);
        flipCard(targetCard, 1);

        if (status && motion?.animate) {
          motion.animate(status, {
            opacity: [1, 0.35, 1],
            translateY: [0, 3, 0],
            duration: 420,
            ease: "outQuad",
          });
        }
      }, 3200);
    };

    const runConvertBurst = async () => {
      converting = true;
      root.dataset.mode = "converting";
      root.classList.add("is-converting");

      clearLoops();
      resetCards();
      clearParticles();
      particles = [];
      ensureMorph();
      const progress = ensureProgress();
      const fill = progress.querySelector("[data-progress-fill]");
      const track = progress.querySelector(".job-pair__progress-track");

      const fromLabel = sourceExt.textContent || "—";
      const toLabel = targetExt.textContent || "—";
      setStatus(`Converting ${fromLabel} → ${toLabel}`);
      setProgressPct(8);

      const syncProgressLabel = () => {
        if (!converting || !fill || !track) return;
        const trackWidth = track.clientWidth || 1;
        const fillWidth = fill.getBoundingClientRect().width;
        setProgressPct((fillWidth / trackWidth) * 100);
        progressRaf = window.requestAnimationFrame(syncProgressLabel);
      };

      if (reduceMotion || !motion?.animate) {
        if (fill) fill.style.width = "42%";
        setProgressPct(42);
        return;
      }

      await waitForLayout();
      if (!converting) return;

      progressRaf = window.requestAnimationFrame(syncProgressLabel);

      if (glow) {
        loops.push(
          motion.animate(glow, {
            opacity: [
              { to: 0.4, duration: 1600 },
              { to: 0.22, duration: 1600 },
            ],
            scale: [
              { to: 1.06, duration: 1600 },
              { to: 0.94, duration: 1600 },
            ],
            ease: "inOutSine",
            loop: true,
          })
        );
      }

      if (sourceCard) {
        loops.push(
          motion.animate(sourceCard, {
            opacity: [
              { to: 1, duration: 1100 },
              { to: 0.5, duration: 1100 },
            ],
            scale: [
              { to: 1, duration: 1100 },
              { to: 0.96, duration: 1100 },
            ],
            ease: "inOutSine",
            loop: true,
          })
        );
      }

      if (targetCard) {
        loops.push(
          motion.animate(targetCard, {
            opacity: [
              { to: 0.55, duration: 1100 },
              { to: 1, duration: 1100 },
            ],
            scale: [
              { to: 0.96, duration: 1100 },
              { to: 1.03, duration: 1100 },
            ],
            ease: "inOutSine",
            loop: true,
            delay: 80,
          })
        );
      }
    };

    const syncFormats = (source, target) => {
      if (!source || !target) return;
      const nextSource = String(source).toUpperCase();
      const nextTarget = String(target).toUpperCase();
      setPair(nextSource, nextTarget);
      pairs = [[nextSource, nextTarget]];
      pairIndex = 0;
      root.dataset.locked = "true";
    };

    const isVisible = () => {
      if (root.closest("[hidden]")) return false;
      return root.getClientRects().length > 0;
    };

    if (converting) {
      runConvertBurst();
    } else if (isVisible()) {
      runIdleLoop();
    }

    root._convertStage = {
      root,
      playConvert: runConvertBurst,
      playIdle: () => {
        converting = false;
        root.dataset.mode = "idle";
        root.classList.remove("is-converting");
        if (isVisible()) {
          runIdleLoop();
        } else {
          clearLoops();
          clearMorph();
          clearProgress();
        }
      },
      syncFormats,
      destroy: () => {
        clearLoops();
        clearMorph();
        clearProgress();
      },
      isVisible,
    };

    return root._convertStage;
  };

  const controllers = stages.map(bootStage).filter(Boolean);

  const pickControllers = (scope) => {
    if (!scope) return controllers;
    if (typeof scope === "string") {
      const node = document.querySelector(scope);
      return controllers.filter((controller) => node?.contains(controller.root));
    }
    if (scope instanceof Element) {
      return controllers.filter(
        (controller) => controller.root === scope || scope.contains(controller.root)
      );
    }
    return controllers;
  };

  window.FileForgeConvertStage = {
    playConvert(scope) {
      const targets = pickControllers(scope);
      targets.forEach((controller) => controller.playConvert());
    },
    playIdle(scope) {
      const targets = pickControllers(scope);
      targets.forEach((controller) => controller.playIdle());
    },
    syncFormats(source, target, scope) {
      const targets = pickControllers(scope);
      targets.forEach((controller) => controller.syncFormats(source, target));
    },
    refreshVisible() {
      controllers.forEach((controller) => {
        if (controller.isVisible()) {
          if (controller.root.dataset.mode === "converting") {
            controller.playConvert();
          } else {
            controller.playIdle();
          }
        } else {
          controller.destroy();
        }
      });
    },
  };
})();
