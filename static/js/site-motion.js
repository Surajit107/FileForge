(() => {
  const api = window.anime;
  if (!api?.animate || !api?.createTimeline || !api?.utils) {
    document.documentElement.classList.remove("js-motion");
    document.getElementById("intro-splash")?.remove();
    return;
  }

  const { animate, createTimeline, stagger, utils } = api;
  const reduceMotion =
    document.documentElement.classList.contains("reduce-motion") ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const nodes = (...groups) =>
    [...groups]
      .flatMap((group) => {
        if (!group) return [];
        if (typeof group.length === "number" && !group.tagName) return [...group];
        return [group];
      })
      .filter(Boolean);

  const clearMotionProps = {
    opacity: 1,
    translateX: 0,
    translateY: 0,
    scale: 1,
    scaleX: 1,
    scaleY: 1,
    rotate: 0,
    rotateX: 0,
    rotateY: 0,
    filter: "blur(0px)",
  };

  const reveal = (targets) => {
    if (!targets.length) return;
    utils.set(targets, clearMotionProps);
  };

  const brand = document.querySelector(".brand-mark");
  const tagline = document.querySelector("header p");
  const nav = document.querySelector("header nav");
  const panel = document.querySelector("main.panel-enter");
  const footer = document.querySelector("footer");
  const messages = document.querySelectorAll(".message");
  const pageKicker = document.querySelector(
    "#view-form .page-kicker, .job-panel > .page-kicker, .history-panel > .page-kicker"
  );
  const heading = document.querySelector(
    "#view-form h1, .job-panel > h1, .history-panel > h1, main h1"
  );
  const lead = document.querySelector(
    "#view-form .page-lead, .job-panel > .page-lead, .history-panel > .page-lead"
  );
  const convertFields = document.querySelectorAll("#convert-form > *");
  const pairRibbon = document.querySelector(".pair-ribbon__stack");
  const supportedHeading = document.querySelector("#supported-heading");
  const supportedLead = document.querySelector("#supported-heading + p");
  const homeSections = document.querySelectorAll("[data-home-section]");
  const convertStages = document.querySelectorAll(
    "#view-form .job-pair, .job-panel .job-pair"
  );
  const metaBlocks = document.querySelectorAll(".job-panel .job-meta");
  const jobExtras = document.querySelectorAll(
    ".job-panel .progress-rail, .job-panel .alert-error:not(.hidden), .job-panel .action-row"
  );
  const historyRows = document.querySelectorAll(".history-row");
  const historyExtras = document.querySelectorAll(
    ".history-empty, .history-panel > div, .pagination"
  );
  const ambientOrb = document.querySelector(".ambient-orb");

  const allMotionTargets = nodes(
    brand,
    tagline,
    nav,
    panel,
    footer,
    pageKicker,
    heading,
    lead,
    supportedHeading,
    supportedLead,
    ambientOrb,
    messages,
    convertFields,
    pairRibbon,
    homeSections,
    convertStages,
    metaBlocks,
    jobExtras,
    historyRows,
    historyExtras
  );

  if (reduceMotion) {
    document.getElementById("intro-splash")?.remove();
    reveal(allMotionTargets);
    window.FileForgeMotion = {
      animate,
      createTimeline,
      stagger,
      utils,
      reduceMotion: true,
      pulse() {},
      settleIn(el) {
        if (el) utils.set(el, clearMotionProps);
      },
    };
    return;
  }

  const runPageEntrance = () => {
  if (allMotionTargets.length) {
    utils.set(allMotionTargets, {
      opacity: 0,
      translateX: 0,
      translateY: 0,
      scale: 1,
      rotate: 0,
      filter: "blur(0px)",
    });
  }

  const tl = createTimeline({
    defaults: {
      ease: "outExpo",
      duration: 780,
    },
  });

  if (brand) {
    utils.set(brand, {
      opacity: 0,
      scale: 0.72,
      rotate: -6,
      filter: "blur(16px)",
      translateY: 8,
    });
    tl.add(brand, {
      opacity: [0, 1],
      scale: [0.72, 1.06, 1],
      rotate: [-6, 1.5, 0],
      filter: ["blur(16px)", "blur(0px)"],
      translateY: [8, 0],
      duration: 1100,
      ease: "outElastic(1, 0.72)",
    });
  }

  if (tagline) {
    utils.set(tagline, { opacity: 0, translateX: -28, filter: "blur(8px)" });
    tl.add(
      tagline,
      {
        opacity: [0, 1],
        translateX: [-28, 0],
        filter: ["blur(8px)", "blur(0px)"],
        duration: 700,
        ease: "outCubic",
      },
      "-=820"
    );
  }

  if (nav) {
    utils.set(nav, { opacity: 0, translateX: 36, filter: "blur(8px)" });
    tl.add(
      nav,
      {
        opacity: [0, 1],
        translateX: [36, 0],
        filter: ["blur(8px)", "blur(0px)"],
        duration: 680,
        ease: "outCubic",
      },
      "-=640"
    );
  }

  if (messages.length) {
    utils.set(messages, { opacity: 0, scaleX: 0.92, translateY: -12 });
    tl.add(
      messages,
      {
        opacity: [0, 1],
        scaleX: [0.92, 1],
        translateY: [-12, 0],
        duration: 560,
        ease: "outBack(1.4)",
      },
      stagger(90, { start: "-=520" })
    );
  }

  if (panel) {
    utils.set(panel, {
      opacity: 0,
      scale: 0.94,
      translateY: 36,
      rotateX: 8,
      filter: "blur(12px)",
    });
    tl.add(
      panel,
      {
        opacity: [0, 1],
        scale: [0.94, 1.01, 1],
        translateY: [36, 0],
        rotateX: [8, 0],
        filter: ["blur(12px)", "blur(0px)"],
        duration: 980,
        ease: "outExpo",
      },
      "-=560"
    );
  }

  if (pageKicker) {
    utils.set(pageKicker, { opacity: 0, translateY: 10, letterSpacing: "0.32em" });
    tl.add(
      pageKicker,
      {
        opacity: [0, 1],
        translateY: [10, 0],
        letterSpacing: ["0.32em", "0.14em"],
        duration: 520,
        ease: "outQuad",
      },
      "-=640"
    );
  }

  if (heading) {
    utils.set(heading, {
      opacity: 0,
      translateY: 28,
      scale: 0.92,
      filter: "blur(10px)",
    });
    tl.add(
      heading,
      {
        opacity: [0, 1],
        translateY: [28, 0],
        scale: [0.92, 1],
        filter: ["blur(10px)", "blur(0px)"],
        duration: 720,
        ease: "outBack(1.5)",
      },
      "-=560"
    );
  }

  if (lead) {
    utils.set(lead, { opacity: 0, translateY: 16 });
    tl.add(
      lead,
      {
        opacity: [0, 1],
        translateY: [16, 0],
        duration: 560,
        ease: "outCubic",
      },
      "-=480"
    );
  }

  if (convertFields.length) {
    utils.set(convertFields, {
      opacity: 0,
      translateY: 28,
      scale: 0.94,
      rotate: 1.5,
    });
    tl.add(
      convertFields,
      {
        opacity: [0, 1],
        translateY: [28, 0],
        scale: [0.94, 1],
        rotate: [1.5, 0],
        duration: 640,
        ease: "outBack(1.35)",
      },
      stagger(110, { start: "-=420", from: "first" })
    );
  }

  if (metaBlocks.length) {
    utils.set(metaBlocks, { opacity: 0, translateX: -24, filter: "blur(6px)" });
    tl.add(
      metaBlocks,
      {
        opacity: [0, 1],
        translateX: [-24, 0],
        filter: ["blur(6px)", "blur(0px)"],
        duration: 620,
        ease: "outCubic",
      },
      stagger(100, { start: "-=400" })
    );
  }

  if (jobExtras.length) {
    utils.set(jobExtras, { opacity: 0, scale: 0.9, translateY: 18 });
    tl.add(
      jobExtras,
      {
        opacity: [0, 1],
        scale: [0.9, 1],
        translateY: [18, 0],
        duration: 580,
        ease: "outBack(1.45)",
      },
      stagger(90, { start: "-=320" })
    );
  }

  if (historyRows.length) {
    historyRows.forEach((row, index) => {
      utils.set(row, {
        opacity: 0,
        translateX: index % 2 === 0 ? -36 : 36,
        filter: "blur(6px)",
      });
    });
    tl.add(
      historyRows,
      {
        opacity: [0, 1],
        translateX: 0,
        filter: ["blur(6px)", "blur(0px)"],
        duration: 620,
        ease: "outCubic",
      },
      stagger(70, { start: "-=360" })
    );
  }

  if (historyExtras.length) {
    utils.set(historyExtras, { opacity: 0, scale: 0.96, translateY: 16 });
    tl.add(
      historyExtras,
      {
        opacity: [0, 1],
        scale: [0.96, 1],
        translateY: [16, 0],
        duration: 560,
        ease: "outBack(1.3)",
      },
      stagger(80, { start: "-=300" })
    );
  }

  if (convertStages.length) {
    utils.set(convertStages, {
      opacity: 0,
      scale: 0.88,
      rotateY: -12,
      filter: "blur(8px)",
    });
    tl.add(
      convertStages,
      {
        opacity: [0, 1],
        scale: [0.88, 1.03, 1],
        rotateY: [-12, 0],
        filter: ["blur(8px)", "blur(0px)"],
        duration: 820,
        ease: "outExpo",
      },
      stagger(120, { start: "-=420" })
    );
  }

  if (supportedHeading) {
    utils.set(supportedHeading, { opacity: 0, translateX: -18 });
    tl.add(
      supportedHeading,
      {
        opacity: [0, 1],
        translateX: [-18, 0],
        duration: 520,
        ease: "outCubic",
      },
      "-=280"
    );
  }

  if (supportedLead) {
    utils.set(supportedLead, { opacity: 0, translateX: -12 });
    tl.add(
      supportedLead,
      {
        opacity: [0, 1],
        translateX: [-12, 0],
        duration: 480,
        ease: "outCubic",
      },
      "-=360"
    );
  }

  if (pairRibbon) {
    utils.set(pairRibbon, { opacity: 0, translateY: 16 });
    tl.add(
      pairRibbon,
      {
        opacity: [0, 1],
        translateY: [16, 0],
        duration: 640,
        ease: "outCubic",
      },
      "-=300"
    );
  }

  if (homeSections.length) {
    utils.set(homeSections, { opacity: 0, translateY: 18 });
    tl.add(
      homeSections,
      {
        opacity: [0, 1],
        translateY: [18, 0],
        duration: 620,
        ease: "outCubic",
        delay: stagger(90),
      },
      "-=240"
    );
  }

  if (footer) {
    utils.set(footer, { opacity: 0, translateY: 12, filter: "blur(4px)" });
    tl.add(
      footer,
      {
        opacity: [0, 1],
        translateY: [12, 0],
        filter: ["blur(4px)", "blur(0px)"],
        duration: 560,
        ease: "outQuad",
      },
      "-=360"
    );
  }

  if (ambientOrb) {
    utils.set(ambientOrb, { opacity: 0.4, scale: 1, translateX: 0, translateY: 0, rotate: 0 });
    animate(ambientOrb, {
      translateX: [
        { to: "6vw", duration: 7000 },
        { to: "-3vw", duration: 9000 },
        { to: "2vw", duration: 8000 },
        { to: "0vw", duration: 7000 },
      ],
      translateY: [
        { to: "4vh", duration: 8000 },
        { to: "-3vh", duration: 7000 },
        { to: "2vh", duration: 9000 },
        { to: "0vh", duration: 8000 },
      ],
      scale: [
        { to: 1.14, duration: 8000 },
        { to: 0.9, duration: 9000 },
        { to: 1.06, duration: 7000 },
        { to: 1, duration: 8000 },
      ],
      rotate: [
        { to: 8, duration: 10000 },
        { to: -6, duration: 11000 },
        { to: 0, duration: 9000 },
      ],
      opacity: [
        { to: 0.62, duration: 7000 },
        { to: 0.28, duration: 8000 },
        { to: 0.5, duration: 7000 },
        { to: 0.4, duration: 7000 },
      ],
      ease: "inOutSine",
      loop: true,
    });
  }
  };

  window.FileForgeMotion = {
    animate,
    createTimeline,
    stagger,
    utils,
    reduceMotion: false,
    pulse(el, options = {}) {
      if (!el) return null;
      return animate(el, {
        scale: [1, 1.06, 0.98, 1],
        rotate: [0, -1.5, 1, 0],
        duration: 480,
        ease: "outElastic(1, 0.8)",
        ...options,
      });
    },
    settleIn(el, options = {}) {
      if (!el) return null;
      utils.set(el, {
        opacity: 0,
        translateY: 14,
        scale: 0.96,
        filter: "blur(6px)",
      });
      return animate(el, {
        opacity: [0, 1],
        translateY: [14, 0],
        scale: [0.96, 1],
        filter: ["blur(6px)", "blur(0px)"],
        duration: 520,
        ease: "outBack(1.4)",
        ...options,
      });
    },
  };

  const intro = window.FileForgeIntro;
  const introPromise =
    intro && typeof intro.play === "function"
      ? intro.play(api, { reduceMotion: false })
      : Promise.resolve();

  introPromise.then(runPageEntrance).catch(() => {
    document.documentElement.classList.remove("intro-playing");
    const splash = document.getElementById("intro-splash");
    if (splash) splash.remove();
    runPageEntrance();
  });
})();
