(() => {
  /**
   * Conversion-themed intro: source/target sheets collide through an ember beam,
   * format chips flash, brand clip-reveals, then soft exit.
   * Plays every full load of pages that opt in via data-intro-splash.
   * @param {typeof window.anime} api
   * @param {{ reduceMotion: boolean }} options
   * @returns {Promise<void>}
   */
  window.FileForgeIntro = {
    play(api, options = {}) {
      const root = document.getElementById("intro-splash");
      if (!root) return Promise.resolve();

      const reduceMotion =
        options.reduceMotion ||
        document.documentElement.classList.contains("reduce-motion") ||
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const wantsIntro = document.body.hasAttribute("data-intro-splash");

      if (reduceMotion || !wantsIntro) {
        root.remove();
        return Promise.resolve();
      }

      const { animate, createTimeline, stagger, utils } = api;
      if (!animate || !createTimeline || !stagger || !utils) {
        root.remove();
        return Promise.resolve();
      }

      const beam = root.querySelector("[data-intro-beam]");
      const source = root.querySelector("[data-intro-sheet-source]");
      const target = root.querySelector("[data-intro-sheet-target]");
      const chips = root.querySelectorAll("[data-intro-chip]");
      const brandEl = root.querySelector("[data-intro-brand]");
      const tagEl = root.querySelector("[data-intro-tag]");
      const skipBtn = root.querySelector("[data-intro-skip]");

      if (!source || !target || !brandEl) {
        root.remove();
        return Promise.resolve();
      }

      const brandText = (root.dataset.siteName || brandEl.textContent || "").trim();
      brandEl.textContent = brandText;

      utils.set(beam, { opacity: 0, scaleY: 0.08, scaleX: 1 });
      utils.set(source, { opacity: 0, translateX: "-42vw", rotate: -18, scale: 0.86 });
      utils.set(target, { opacity: 0, translateX: "42vw", rotate: 18, scale: 0.86 });
      utils.set(chips, { opacity: 0, translateY: 18, scale: 0.8 });
      utils.set(brandEl, {
        opacity: 0,
        translateY: 28,
        filter: "blur(14px)",
        clipPath: "inset(0 100% 0 0)",
      });
      if (tagEl) utils.set(tagEl, { opacity: 0, translateY: 14 });

      root.hidden = false;
      root.classList.add("is-active");
      document.documentElement.classList.add("intro-playing");
      if (skipBtn) skipBtn.hidden = false;

      return new Promise((resolve) => {
        let settled = false;
        let tl = null;

        const finish = () => {
          if (settled) return;
          settled = true;
          document.documentElement.classList.remove("intro-playing");
          if (tl && typeof tl.pause === "function") {
            try {
              tl.pause();
            } catch {
              /* ignore */
            }
          }
          root.classList.remove("is-active");
          root.remove();
          resolve();
        };

        const exit = () => {
          if (settled) return;
          animate(root, {
            opacity: [1, 0],
            translateY: [0, -24],
            filter: ["blur(0px)", "blur(8px)"],
            duration: 560,
            ease: "inCubic",
            onComplete: finish,
          });
        };

        if (skipBtn) {
          skipBtn.addEventListener("click", () => exit(), { once: true });
        }

        tl = createTimeline({
          defaults: { ease: "outExpo" },
          onComplete: exit,
        });

        tl.add(beam, {
          opacity: [0, 1],
          scaleY: [0.08, 1],
          duration: 640,
          ease: "outCubic",
        });

        tl.add(
          source,
          {
            opacity: [0, 1],
            translateX: ["-42vw", "-4.5rem"],
            rotate: [-18, -8],
            scale: [0.86, 1],
            duration: 820,
            ease: "outExpo",
          },
          "-=420"
        );

        tl.add(
          target,
          {
            opacity: [0, 1],
            translateX: ["42vw", "4.5rem"],
            rotate: [18, 8],
            scale: [0.86, 1],
            duration: 820,
            ease: "outExpo",
          },
          "<"
        );

        tl.add(
          [source, target],
          {
            scale: [1, 0.94, 1.02, 1],
            duration: 520,
            ease: "outBack(1.6)",
          },
          "-=120"
        );

        tl.add(
          beam,
          {
            scaleX: [1, 14, 1],
            opacity: [1, 1, 0.55],
            duration: 640,
            ease: "inOutCubic",
          },
          "-=480"
        );

        tl.add(
          chips,
          {
            opacity: [0, 1],
            translateY: [18, 0],
            scale: [0.8, 1.08, 1],
            duration: 520,
            ease: "outBack(1.7)",
          },
          stagger(70, { start: "-=360" })
        );

        tl.add(
          source,
          {
            opacity: [1, 0],
            translateX: ["-4.5rem", "-18vw"],
            rotate: [-8, -22],
            filter: ["blur(0px)", "blur(8px)"],
            duration: 560,
            ease: "inCubic",
          },
          "+=80"
        );

        tl.add(
          target,
          {
            opacity: [1, 0],
            translateX: ["4.5rem", "18vw"],
            rotate: [8, 22],
            filter: ["blur(0px)", "blur(8px)"],
            duration: 560,
            ease: "inCubic",
          },
          "<"
        );

        tl.add(
          brandEl,
          {
            opacity: [0, 1],
            translateY: [28, 0],
            filter: ["blur(14px)", "blur(0px)"],
            // Negative right inset keeps glyph overhangs (final "e") visible
            // after the wipe; then clear clip-path so nothing stays clipped.
            clipPath: ["inset(0 100% 0 0)", "inset(0 -3% 0 0)"],
            duration: 780,
            ease: "outExpo",
            onComplete: () => {
              utils.set(brandEl, { clipPath: "none" });
            },
          },
          "-=420"
        );

        if (tagEl) {
          tl.add(
            tagEl,
            {
              opacity: [0, 1],
              translateY: [14, 0],
              duration: 480,
              ease: "outCubic",
            },
            "-=360"
          );
        }

        tl.add(
          chips,
          {
            opacity: [1, 0],
            translateY: [0, -10],
            scale: [1, 0.9],
            duration: 360,
            ease: "inCubic",
          },
          stagger(40, { start: "+=160" })
        );

        tl.add(
          beam,
          {
            opacity: [0.55, 0],
            scaleY: [1, 0.2],
            duration: 420,
            ease: "inCubic",
          },
          "-=280"
        );
      });
    },
  };
})();
