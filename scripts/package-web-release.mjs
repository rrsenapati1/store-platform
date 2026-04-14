#!/usr/bin/env node
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { copyTreeFiltered, createTarGz, ensureDirectory, parseCliArgs, removeIfExists } from './release-archive-utils.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');

export async function buildWebReleaseArchive({ appName, distDir, outputDir, version }) {
  const normalizedDistDir = path.resolve(distDir);
  const normalizedOutputDir = path.resolve(outputDir);
  const releaseName = `${appName}-${version}`;
  const stagingRoot = await fs.mkdtemp(path.join(os.tmpdir(), `${appName}-release-`));
  const stagedReleaseDir = path.join(stagingRoot, releaseName);
  const stagedDistDir = path.join(stagedReleaseDir, 'dist');
  const archivePath = path.join(normalizedOutputDir, `${releaseName}.tar.gz`);

  try {
    await ensureDirectory(normalizedOutputDir);
    await copyTreeFiltered(normalizedDistDir, stagedDistDir, () => true);
    await removeIfExists(archivePath);
    await createTarGz(stagedReleaseDir, archivePath);
    return archivePath;
  } finally {
    await removeIfExists(stagingRoot);
  }
}

function printHelp() {
  console.log(`Package a Store web release artifact

Usage:
  node scripts/package-web-release.mjs --app <platform-admin|owner-web> --version <version> [--dist-dir <path>] [--output-dir <path>]

Defaults:
  --dist-dir    apps/<app>/dist
  --output-dir  dist/releases/web
`);
}

async function main() {
  const args = parseCliArgs(process.argv.slice(2));
  if (args.has('--help') || args.has('-h')) {
    printHelp();
    return;
  }

  const appName = args.get('--app');
  if (appName !== 'platform-admin' && appName !== 'owner-web') {
    throw new Error('A valid --app <platform-admin|owner-web> is required.');
  }

  const version = args.get('--version');
  if (typeof version !== 'string' || !version.trim()) {
    throw new Error('A non-empty --version value is required.');
  }

  const distDir = typeof args.get('--dist-dir') === 'string'
    ? path.resolve(String(args.get('--dist-dir')))
    : path.join(repoRoot, 'apps', appName, 'dist');
  const outputDir = typeof args.get('--output-dir') === 'string'
    ? path.resolve(String(args.get('--output-dir')))
    : path.join(repoRoot, 'dist', 'releases', 'web');

  const archivePath = await buildWebReleaseArchive({
    appName,
    distDir,
    outputDir,
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
