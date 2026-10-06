/**
 * Best-effort local Redis for FileForge.
 * Starts `fileforge-redis` via Docker when available; never fails quickstart.
 */
const { execSync, spawnSync } = require("child_process");

function hasDocker() {
  const result = spawnSync("docker", ["version"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  return result.status === 0;
}

function containerRunning() {
  try {
    const out = execSync(
      'docker ps --filter "name=^fileforge-redis$" --format "{{.Names}}"',
      { encoding: "utf8" }
    ).trim();
    return out.includes("fileforge-redis");
  } catch {
    return false;
  }
}

function containerExists() {
  try {
    const out = execSync(
      'docker ps -a --filter "name=^fileforge-redis$" --format "{{.Names}}"',
      { encoding: "utf8" }
    ).trim();
    return out.includes("fileforge-redis");
  } catch {
    return false;
  }
}

if (!hasDocker()) {
  console.log(
    "[redis] Docker not found — using LocMem cache (set CACHE_URL only when Redis is up)."
  );
  process.exit(0);
}

if (containerRunning()) {
  console.log("[redis] fileforge-redis already running on :6379");
  process.exit(0);
}

try {
  if (containerExists()) {
    execSync("docker start fileforge-redis", { stdio: "inherit" });
  } else {
    execSync(
      "docker run -d -p 6379:6379 --name fileforge-redis redis:7-alpine",
      { stdio: "inherit" }
    );
  }
  console.log("[redis] Ready at redis://127.0.0.1:6379");
} catch (err) {
  console.warn(
    "[redis] Could not start container — continuing without Redis.",
    err.message || err
  );
}
process.exit(0);
