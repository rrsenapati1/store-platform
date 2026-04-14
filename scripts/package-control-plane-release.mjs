#!/usr/bin/env node
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { copyTreeFiltered, createTarGz, ensureDirectory, parseCliArgs, removeIfExists } from './release-archive-utils.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');

const EXCLUDED_SEGMENTS = new Set([
  '.git',
  '.venv',
  'venv',
  'ENV',
  'env',
  '__pycache__',
  '.pytest_cache',
  '.mypy_cache',
  '.ruff_cache',
  'node_modules',
  'dist',
  'build',
]);

const EXCLUDED_SUFFIXES = ['.sqlite', '.sqlite3', '.db', '.db-shm', '.db-wal', '.wal', '.shm', '.log'];

export function shouldIncludeControlPlanePath(relativePath) {
  const segments = relativePath.split(/[\\/]+/u).filter(Boolean);
  if (segments.some((segment) => EXCLUDED_SEGMENTS.has(segment))) {
    return false;
  }
  return !EXCLUDED_SUFFIXES.some((suffix) => relativePath.endsWith(suffix));
}

export async function buildControlPlaneReleaseArchive({ sourceDir, outputDir, version }) {
  const normalizedSourceDir = path.resolve(sourceDir);
  const normalizedOutputDir = path.resolve(outputDir);
  const releaseName = `store-control-plane-${version}`;
  const stagingRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'store-control-plane-release-'));
  const stagedReleaseDir = path.join(stagingRoot, releaseName);
  const archivePath = path.join(normalizedOutputDir, `${releaseName}.tar.gz`);

  try {
    await ensureDirectory(normalizedOutputDir);
    await copyTreeFiltered(normalizedSourceDir, stagedReleaseDir, (relativePath) => shouldIncludeControlPlanePath(relativePath));
    await removeIfExists(archivePath);
    await createTarGz(stagedReleaseDir, archivePath);
    return archivePath;
  } finally {
    await removeIfExists(stagingRoot);
  }
}

function printHelp() {
  console.log(`Package the Store control-plane release bundle

Usage:
  node scripts/package-control-plane-release.mjs --version <version> [--source-dir <path>] [--output-dir <path>]

Defaults:
  --source-dir  services/control-plane-api
  --output-dir  dist/releases/control-plane
`);
}

async function main() {
  const args = parseCliArgs(process.argv.slice(2));
  if (args.has('--help') || args.has('-h')) {
    printHelp();
    return;
  }

  const version = args.get('--version');
  if (typeof version !== 'string' || !version.trim()) {
    throw new Error('A non-empty --version value is required.');
  }

  const sourceDir = typeof args.get('--source-dir') === 'string'
    ? path.resolve(String(args.get('--source-dir')))
    : path.join(repoRoot, 'services', 'control-plane-api');
  const outputDir = typeof args.get('--output-dir') === 'string'
    ? path.resolve(String(args.get('--output-dir')))
    : path.join(repoRoot, 'dist', 'releases', 'control-plane');

  const archivePath = await buildControlPlaneReleaseArchive({
    outputDir,
    sourceDir,
    version: version.trim(),
  });
  console.log(archivePath);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
  });
}
