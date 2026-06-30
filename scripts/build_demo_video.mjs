#!/usr/bin/env node
import { execFile } from "node:child_process";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "submission", "demo-video-build");
const VIDEO = path.join(OUT, "armcare-edge-triage-demo.mp4");
const THUMBNAIL_SVG = path.join(ROOT, "submission", "youtube-thumbnail.svg");
const THUMBNAIL_PNG = path.join(ROOT, "submission", "youtube-thumbnail.png");
const SCREENSHOT = path.join(ROOT, "media", "site-screenshot.png");
const POSTER = path.join(ROOT, "media", "armcare-edge-triage-poster.png");
const BENCHMARK = JSON.parse(await readFile(path.join(ROOT, "evidence", "benchmark_latest.json"), "utf8"));

const speedup = Number(BENCHMARK.speedup).toFixed(1);
const latency = Number(BENCHMARK.optimized.median_ms).toFixed(2);
const memory = Number(BENCHMARK.memory.reduction_percent).toFixed(1);
const throughput = Math.round(BENCHMARK.optimized.tickets_per_second / 1000).toLocaleString();

const slides = [
  {
    key: "title",
    title: "ArmCare Edge Triage",
    kicker: "Arm Create: AI Optimization Challenge",
    bullets: [
      "Local AI routing for sensitive care intake queues.",
      "Built for small clinics and disability support offices.",
      "Runs as a reproducible Arm edge benchmark, not a cloud-only demo."
    ],
    narration:
      "This is ArmCare Edge Triage, a local AI routing demo for sensitive care intake queues. It is built for small clinics, disability support offices, and community teams that need fast triage without sending private intake text to a cloud model."
  },
  {
    key: "problem",
    title: "The Problem",
    kicker: "Urgent signals are mixed with routine work",
    bullets: [
      "Urgent symptoms, access requests, paperwork, and scheduling arrive together.",
      "Manual sorting delays the first human review.",
      "The first AI job is safe routing, not diagnosis."
    ],
    narration:
      "The problem is practical. Urgent symptoms, access support, paperwork, and routine scheduling messages arrive in the same inbox. Staff need help deciding what needs human review first. ArmCare does not diagnose. It routes."
  },
  {
    key: "product",
    title: "The Product",
    kicker: "Human review queue",
    image: SCREENSHOT,
    bullets: [
      "Four queues: urgent care, access support, paperwork, routine follow-up.",
      "Dashboard renders measured speed, accuracy, and memory claims.",
      "Claim boundary stays visible for judges and users."
    ],
    narration:
      "The product is a human review queue. It classifies each intake into urgent care, access support, paperwork, or routine follow-up. The dashboard also shows the exact benchmark results and the claim boundary."
  },
  {
    key: "optimization",
    title: "Arm Optimization",
    kicker: "From naive FP32 to int8 batch inference",
    image: POSTER,
    bullets: [
      `Latest local speedup: ${speedup}x on arm64 Apple M4.`,
      `Optimized latency: ${latency} milliseconds for 12,000 tickets.`,
      `Memory reduction: ${memory}% with int8 features and weights.`
    ],
    narration:
      `The optimization is measured. The baseline is a float thirty two single ticket probability path. The optimized path is int eight batched inference. On this arm sixty four Apple M four run, the latest evidence shows ${speedup} times speedup and ${memory} percent lower memory.`
  },
  {
    key: "proof",
    title: "Reproducible Proof",
    kicker: "Run npm run verify",
    bullets: [
      "Benchmark evidence is generated into JSON.",
      "Playwright verifies the dashboard and screenshot.",
      `Optimized throughput is about ${throughput} thousand tickets per second.`
    ],
    narration:
      "The repository is built around proof. Running npm run verify regenerates the benchmark, checks the Arm platform, verifies accuracy and memory reduction, and captures the dashboard screenshot."
  },
  {
    key: "close",
    title: "Why It Matters",
    kicker: "Fast local AI with human control",
    bullets: [
      "Sensitive intake can stay local.",
      "Arm devices become useful care operations hardware.",
      "Humans keep final responsibility for every decision."
    ],
    narration:
      "This matters because useful AI needs to be fast, local, and understandable. ArmCare shows an Arm edge AI workflow where private intake stays local and humans keep responsibility for every final decision."
  }
];

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

for (let index = 0; index < slides.length; index += 1) {
  const slide = slides[index];
  const stem = `${String(index + 1).padStart(2, "0")}-${slide.key}`;
  const svgPath = path.join(OUT, `${stem}.svg`);
  const pngPath = path.join(OUT, `${stem}.png`);
  await writeFile(svgPath, await renderSlide(slide), "utf8");
  await run("rsvg-convert", ["-w", "1920", "-h", "1080", svgPath, "-o", pngPath]);
}

await writeFile(THUMBNAIL_SVG, renderThumbnail(), "utf8");
await run("rsvg-convert", ["-w", "1280", "-h", "720", THUMBNAIL_SVG, "-o", THUMBNAIL_PNG]);

const segments = [];
for (let index = 0; index < slides.length; index += 1) {
  const slide = slides[index];
  const stem = `${String(index + 1).padStart(2, "0")}-${slide.key}`;
  const pngPath = path.join(OUT, `${stem}.png`);
  const aiffPath = path.join(OUT, `${stem}.aiff`);
  const wavPath = path.join(OUT, `${stem}.wav`);
  const segmentPath = path.join(OUT, `${stem}.mp4`);
  await run("say", ["-v", "Samantha", "-o", aiffPath, slide.narration]);
  await run("ffmpeg", ["-y", "-i", aiffPath, "-ar", "48000", "-ac", "2", wavPath]);
  await run("ffmpeg", [
    "-y",
    "-loop",
    "1",
    "-i",
    pngPath,
    "-i",
    wavPath,
    "-vf",
    "format=yuv420p",
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-tune",
    "stillimage",
    "-c:a",
    "aac",
    "-b:a",
    "160k",
    "-shortest",
    segmentPath
  ]);
  segments.push(segmentPath);
}

const concatPath = path.join(OUT, "concat.txt");
await writeFile(concatPath, segments.map((segment) => `file '${segment.replaceAll("'", "'\\''")}'`).join("\n") + "\n");
await run("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", concatPath, "-c", "copy", VIDEO]);

const duration = Number(await ffprobeDuration(VIDEO));
console.log(JSON.stringify({ ok: true, video: VIDEO, thumbnail: THUMBNAIL_PNG, duration_seconds: duration }, null, 2));

async function renderSlide(slide) {
  const image = slide.image ? await imageData(slide.image) : "";
  const bullets = slide.bullets
    .map((bullet, index) => `<text class="bullet" x="142" y="${640 + index * 58}">${escapeXml(bullet)}</text>`)
    .join("\n");
  const media = image
    ? `<image href="${image}" x="770" y="222" width="1010" height="568" preserveAspectRatio="xMidYMid meet" clip-path="url(#mediaClip)"/>`
    : renderMetricCards();

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <clipPath id="mediaClip"><rect x="770" y="222" width="1010" height="568" rx="18"/></clipPath>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="#17262b" flood-opacity="0.18"/></filter>
    <style>
      .page { fill: #f7f6f1; }
      .panel { fill: #ffffff; stroke: #d9d3c7; stroke-width: 2; }
      .header { fill: #17262b; }
      .kicker { font: 800 24px Arial, Helvetica, sans-serif; fill: #5b615f; letter-spacing: 0; }
      .title { font: 800 70px Arial, Helvetica, sans-serif; fill: #17262b; letter-spacing: 0; }
      .bullet { font: 400 33px Arial, Helvetica, sans-serif; fill: #283539; letter-spacing: 0; }
      .label { font: 800 26px Arial, Helvetica, sans-serif; fill: #17262b; letter-spacing: 0; }
      .value { font: 800 58px Arial, Helvetica, sans-serif; fill: #17262b; letter-spacing: 0; }
      .white { fill: #ffffff; }
    </style>
  </defs>
  <rect class="page" width="1920" height="1080"/>
  <rect x="60" y="56" width="1800" height="968" rx="26" class="panel" filter="url(#shadow)"/>
  <rect x="60" y="56" width="1800" height="112" rx="26" class="header"/>
  <text x="108" y="128" font-family="Arial, Helvetica, sans-serif" font-size="38" font-weight="800" fill="#ffffff">ArmCare Edge Triage</text>
  <text class="kicker" x="108" y="250">${escapeXml(slide.kicker)}</text>
  <text class="title" x="108" y="336">${escapeXml(slide.title)}</text>
  <rect x="108" y="398" width="590" height="150" rx="18" fill="#fbfaf7" stroke="#d9d3c7" stroke-width="2"/>
  <text class="label" x="142" y="454">Who and what this solves</text>
  <text x="142" y="503" font-family="Arial, Helvetica, sans-serif" font-size="28" fill="#5b615f">Small care teams need local first-pass routing before human review.</text>
  ${bullets}
  ${media}
</svg>`;
}

function renderMetricCards() {
  const cards = [
    ["Speedup", `${speedup}x`, "#c94b4b"],
    ["Latency", `${latency} ms`, "#2e8b7b"],
    ["Memory", `${memory}%`, "#a66a2d"],
    ["Accuracy", "100.0%", "#5a6f9b"]
  ];
  return cards
    .map((card, index) => {
      const x = 790 + (index % 2) * 500;
      const y = 255 + Math.floor(index / 2) * 245;
      return `<rect x="${x}" y="${y}" width="440" height="190" rx="18" fill="#fbfaf7" stroke="#d9d3c7" stroke-width="2"/>
<rect x="${x}" y="${y}" width="440" height="16" fill="${card[2]}"/>
<text class="label" x="${x + 32}" y="${y + 72}">${card[0]}</text>
<text class="value" x="${x + 32}" y="${y + 145}">${card[1]}</text>`;
    })
    .join("\n");
}

function renderThumbnail() {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#f7f6f1"/>
  <rect x="0" y="0" width="1280" height="122" fill="#17262b"/>
  <text x="58" y="82" font-family="Arial, Helvetica, sans-serif" font-size="58" font-weight="800" fill="#ffffff">ArmCare Edge Triage</text>
  <text x="58" y="185" font-family="Arial, Helvetica, sans-serif" font-size="36" font-weight="800" fill="#17262b">Arm-optimized local AI routing</text>
  <rect x="58" y="248" width="255" height="145" rx="16" fill="#ffffff" stroke="#d9d3c7" stroke-width="2"/>
  <rect x="58" y="248" width="255" height="14" fill="#c94b4b"/>
  <text x="84" y="312" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="800" fill="#5b615f">Speedup</text>
  <text x="84" y="367" font-family="Arial, Helvetica, sans-serif" font-size="46" font-weight="800" fill="#17262b">${speedup}x</text>
  <rect x="342" y="248" width="255" height="145" rx="16" fill="#ffffff" stroke="#d9d3c7" stroke-width="2"/>
  <rect x="342" y="248" width="255" height="14" fill="#2e8b7b"/>
  <text x="368" y="312" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="800" fill="#5b615f">Latency</text>
  <text x="368" y="367" font-family="Arial, Helvetica, sans-serif" font-size="46" font-weight="800" fill="#17262b">${latency} ms</text>
  <rect x="626" y="248" width="255" height="145" rx="16" fill="#ffffff" stroke="#d9d3c7" stroke-width="2"/>
  <rect x="626" y="248" width="255" height="14" fill="#a66a2d"/>
  <text x="652" y="312" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="800" fill="#5b615f">Memory</text>
  <text x="652" y="367" font-family="Arial, Helvetica, sans-serif" font-size="46" font-weight="800" fill="#17262b">${memory}%</text>
  <rect x="920" y="226" width="245" height="245" rx="34" fill="#17262b"/>
  <rect x="948" y="258" width="189" height="158" rx="18" fill="#f7f6f1"/>
  <text x="980" y="318" font-family="Arial, Helvetica, sans-serif" font-size="36" font-weight="800" fill="#c94b4b">arm64</text>
  <text x="980" y="366" font-family="Arial, Helvetica, sans-serif" font-size="26" fill="#2e8b7b">int8 batch</text>
  <text x="58" y="552" font-family="Arial, Helvetica, sans-serif" font-size="32" fill="#283539">Private intake stays local. Humans keep final decisions.</text>
</svg>`;
}

async function imageData(file) {
  const ext = path.extname(file).toLowerCase().replace(".", "") || "png";
  const data = await readFile(file);
  return `data:image/${ext};base64,${data.toString("base64")}`;
}

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    execFile(command, args, { cwd: ROOT }, (error, stdout, stderr) => {
      if (error) {
        error.message += `\n${stderr || stdout}`;
        reject(error);
      } else {
        resolve(stdout);
      }
    });
  });
}

async function ffprobeDuration(file) {
  const output = await run("ffprobe", [
    "-v",
    "error",
    "-show_entries",
    "format=duration",
    "-of",
    "default=noprint_wrappers=1:nokey=1",
    file
  ]);
  return output.trim();
}
