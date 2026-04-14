#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { ensureDirectory, parseCliArgs, removeIfExists, writeJsonFile } from './release-archive-utils.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');

async function resolveInstallerFiles(bundleDir) {
  const fileNames = await fs.readdir(bundleDir);
  const installerFileName = fileNames.find((fileName) => fileName.endsWith('-setup.exe'));
  if (!installerFileName) {
    throw new Error(`No Windows installer was found in ${bundleDir}`);
  }
  const signatureFileName = `${installerFileName}.sig`;
  if (!fileNames.includes(signatureFileName)) {
    throw new Error(`Missing signature file ${signatureFileName} in ${bundleDir}`);
  }
  return { installerFileName, signatureFileName };
}

export async function stageStoreDesktopReleaseArtifacts({ bundleDir, outputDir, profile, version }) {
  const normalizedBundleDir = path.resolve(bundleDir);
  const normalizedOutputDir = path.resolve(outputDir);
  const stageName = `store-desktop-${version}-${profile}`;
  const stagedDir = path.join(normalizedOutputDir, stageName);

  const { installerFileName, signatureFileName } = await resolveInstallerFiles(normalizedBundleDir);

  await removeIfExists(stagedDir);
  await ensureDirectory(stagedDir);

  await fs.copyFile(path.join(normalizedBundleDir, installerFileName), path.join(stagedDir, installerFileName));
  await fs.copyFile(path.join(normalizedBundleDir, signatureFileName), path.join(stagedDir, signatureFileName));
  await writeJsonFile(path.join(stagedDir, 'release-metadata.json'), {
    installerFileName,
    profile,
    signatureFileName,
    version,
  });
  return stagedDir;
}

function printHelp() {
  console.log(`Stage Store Desktop release artifacts for CI upload

Usage:
  node scripts/stage-store-desktop-release-artifacts.mjs --version <version> --profile <staging|prod> [--bundle-dir <path>] [--output-dir <path>]

Defaults:
  --bundle-dir  apps/store-desktop/src-tauri/target/release/bundle/nsis
  --output-dir  dist/releases/store-desktop
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

  const profile = args.get('--profile');
  if (profile !== 'staging' && profile !== 'prod' && profile !== 'dev') {
    throw new Error('A valid --profile <dev|staging|prod> is required.');
  }

  const bundleDir = typeof args.get('--bundle-dir') === 'string'
    ? path.resolve(String(args.get('--bundle-dir')))
    : path.join(repoRoot, 'apps', 'store-desktop', 'src-tauri', 'target', 'release', 'bundle', 'nsis');
  const outputDir = typeof args.get('--output-dir') === 'string'
    ? path.resolve(String(args.get('--output-dir')))
    : path.join(repoRoot, 'dist', 'releases', 'store-desktop');

  const stagedDir = await stageStoreDesktopReleaseArtifacts({
    bundleDir,
    outputDir,
    profile,
    version: version.trim(),
  });
  console.log(stagedDir);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
  });
}
