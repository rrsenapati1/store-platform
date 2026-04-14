#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');

function printHelp() {
  console.log(`Store Desktop release builder

Usage:
  node scripts/build-store-desktop-release.mjs --profile <dev|staging|prod> [--bundles <nsis>] [--notes-file <path>]

Environment:
  TAURI_SIGNING_PRIVATE_KEY                 Required for signed updater artifacts
  TAURI_SIGNING_PRIVATE_KEY_PASSWORD        Optional
  STORE_DESKTOP_RELEASE_CONTROL_PLANE_BASE_URL  Optional override
  STORE_DESKTOP_RELEASE_UPDATER_ENDPOINT        Optional override
  STORE_DESKTOP_RELEASE_UPDATER_PUBLIC_KEY      Optional override

Examples:
  node scripts/build-store-desktop-release.mjs --profile staging
  node scripts/build-store-desktop-release.mjs --profile prod --bundles nsis
`);
}

function parseArgs(argv) {
  const parsed = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith('--')) {
      continue;
    }
    const next = argv[index + 1];
    if (!next || next.startsWith('--')) {
      parsed.set(value, true);
      continue;
    }
    parsed.set(value, next);
    index += 1;
  }
  return parsed;
}

const args = parseArgs(process.argv.slice(2));
if (args.has('--help') || args.has('-h')) {
  printHelp();
  process.exit(0);
}

const profile = args.get('--profile');
if (profile !== 'dev' && profile !== 'staging' && profile !== 'prod') {
  console.error('A valid --profile <dev|staging|prod> is required.');
  process.exit(1);
}

if (!process.env.TAURI_SIGNING_PRIVATE_KEY) {
  console.error('TAURI_SIGNING_PRIVATE_KEY is required to build signed updater artifacts.');
  process.exit(1);
}

const bundles = typeof args.get('--bundles') === 'string' ? args.get('--bundles') : 'nsis';
const npmExecutable = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const commandArgs = [
  'run',
  'tauri:build',
  '--workspace',
  '@store/store-desktop',
  '--',
  '--bundles',
  bundles,
];

const result = spawnSync(npmExecutable, commandArgs, {
  cwd: repoRoot,
  stdio: 'inherit',
  env: {
    ...process.env,
    STORE_DESKTOP_RELEASE_PROFILE: profile,
  },
});

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

console.log(`Store Desktop ${profile} release build completed.`);
