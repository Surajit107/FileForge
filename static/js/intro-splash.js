(() => {
  /**
   * Conversion intro: blank file sheet lands → ember scan → boom
   * transmute, then brand. Timed so the sequence can be read.
   * Plays on pages that opt in via data-intro-splash.
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

      const { animate, createTimeline, utils } = api;
      if (!animate || !createTimeline || !utils) {
        root.remove();
        return Promise.resolve();
      }

      const sheet = root.querySelector("[data-intro-sheet]");
      const scan = root.querySelector("[data-intro-scan]");
      const flash = root.querySelector("[data-intro-flash]");
      const brandEl = root.querySelector("[data-intro-brand]");
      const tagEl = root.querySelector("[data-intro-tag]");
      const skipBtn = root.querySelector("[data-intro-skip]");

      if (!sheet || !brandEl) {
        root.remove();
        return Promise.resolve();
      }

      const brandText = (root.dataset.siteName || brandEl.textContent || "").trim();
      brandEl.textContent = brandText;

      const scanTravel = () => {
        const height = sheet.getBoundingClientRect().height || 220;
        return Math.max(140, height * 0.78);
      };

      utils.set(sheet, {
        opacity: 0,
        translateY: 28,
        scale: 0.94,
        rotate: -2,
      });
      if (scan) utils.set(scan, { opacity: 0, translateY: 0 });
      if (flash) utils.set(flash, { opacity: 0, scale: 0.75 });
      utils.set(brandEl, { opacity: 0, translateY: 14, scale: 0.98 });
      if (tagEl) utils.set(tagEl, { opacity: 0, translateY: 8 });

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
            duration: 620,
            ease: "inOutCubic",
            onComplete: finish,
          });
        };

        if (skipBtn) {
          skipBtn.addEventListener("click", () => exit(), { once: true });
        }

        const markConverted = () => {
          sheet.classList.add("is-converted");
        };

        const SCAN_MS = 1700;
        const travel = scanTravel();

        tl = createTimeline({
          defaults: { ease: "outCubic" },
          onComplete: exit,
        });

        // 1. File appears — soft settle, then brief hold
        tl.add(sheet, {
          opacity: [0, 1],
          translateY: [28, 0],
          scale: [0.94, 1],
          rotate: [-2, 0],
          duration: 780,
          ease: "outCubic",
        });

        tl.add(sheet, { duration: 380 });

        // 2. Ember scan across blank page
        if (scan) {
          tl.add(scan, {
            opacity: [0, 1, 1, 0],
            translateY: [12, travel * 0.4, travel, travel + 6],
            duration: SCAN_MS,
            ease: "inOutSine",
          });
        }

        tl.add(
          sheet,
          {
            duration: SCAN_MS,
            ease: "linear",
            onBegin: () => {
              sheet.classList.add("is-scanning");
            },
            onComplete: () => {
              sheet.classList.remove("is-scanning");
            },
          },
          scan ? `-=${SCAN_MS}` : undefined
        );

        // Beat after scan before convert
        tl.add(sheet, { duration: 220 });

        // 3. Convert flash
        if (flash) {
          tl.add(flash, {
            opacity: [0, 0.85, 0],
            scale: [0.82, 1.12, 1.28],
            duration: 560,
            ease: "inOutCubic",
            onBegin: markConverted,
          });
        } else {
          tl.add(sheet, {
            duration: 1,
            onBegin: markConverted,
          });
        }

        tl.add(
          sheet,
          {
            scale: [1, 1.04, 1],
            duration: 640,
            ease: "outCubic",
          },
          "-=420"
        );

        // 4. Brand + tag
        tl.add(
          brandEl,
          {
            opacity: [0, 1],
            translateY: [14, 0],
            scale: [0.98, 1],
            duration: 720,
            ease: "outCubic",
          },
          "-=120"
        );

        if (tagEl) {
          tl.add(
            tagEl,
            {
              opacity: [0, 1],
              translateY: [8, 0],
              duration: 560,
              ease: "outCubic",
            },
            "-=420"
          );
        }

        tl.add(sheet, { duration: 1100 });
      });
    },
  };
})();
