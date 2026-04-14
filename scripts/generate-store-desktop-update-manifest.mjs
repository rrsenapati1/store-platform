#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

function printHelp() {
  console.log(`Store Desktop updater manifest generator

Usage:
  node scripts/generate-store-desktop-update-manifest.mjs --version <semver> --url <artifact-url> --signature-file <path> --output <path> [--platform windows-x86_64] [--notes-file <path>] [--pub-date <RFC3339>]

Example:
  node scripts/generate-store-desktop-update-manifest.mjs \\
    --version 0.1.0 \\
    --url https://updates.store.korsenex.com/prod/store-runtime-setup.exe \\
    --signature-file apps/store-desktop/src-tauri/target/release/bundle/nsis/store-runtime-setup.exe.sig \\
    --output dist/latest.json
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

export function buildManifest({ version, url, signature, platform = 'windows-x86_64', notes = '', pubDate = new Date().toISOString() }) {
  return {
    version,
    notes,
    pub_date: pubDate,
    platforms: {
      [platform]: {
        signature,
        url,
      },
    },
  };
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, '/'))) {
  const args = parseArgs(process.argv.slice(2));
  if (args.has('--help') || args.has('-h')) {
    printHelp();
    process.exit(0);
  }

  const version = args.get('--version');
  const url = args.get('--url');
  const signatureFile = args.get('--signature-file');
  const output = args.get('--output');
  const platform = typeof args.get('--platform') === 'string' ? args.get('--platform') : 'windows-x86_64';
  const notesFile = args.get('--notes-file');
  const pubDate = typeof args.get('--pub-date') === 'string' ? args.get('--pub-date') : new Date().toISOString();

  if (typeof version !== 'string' || typeof url !== 'string' || typeof signatureFile !== 'string' || typeof output !== 'string') {
    console.error('Required flags: --version, --url, --signature-file, --output');
    process.exit(1);
  }

  const signature = fs.readFileSync(signatureFile, 'utf8').trim();
  const notes = typeof notesFile === 'string' ? fs.readFileSync(notesFile, 'utf8').trim() : '';
  const manifest = buildManifest({ version, url, signature, platform, notes, pubDate });

  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(`Wrote updater manifest to ${output}`);
}
