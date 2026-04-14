import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildManifest } from './generate-store-desktop-update-manifest.mjs';

test('buildManifest creates a windows static updater manifest', () => {
  const manifest = buildManifest({
    version: '0.1.0',
    url: 'https://updates.store.korsenex.com/prod/store-runtime-setup.exe',
    signature: 'signature-value',
    notes: 'Release notes',
    pubDate: '2026-04-14T00:00:00Z',
  });

  assert.deepEqual(manifest, {
    version: '0.1.0',
    notes: 'Release notes',
    pub_date: '2026-04-14T00:00:00Z',
    platforms: {
      'windows-x86_64': {
        signature: 'signature-value',
        url: 'https://updates.store.korsenex.com/prod/store-runtime-setup.exe',
      },
    },
  });
});

test('manifest output can be written with a signature file payload', () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'store-desktop-manifest-'));
  const signaturePath = path.join(tempDir, 'store-runtime-setup.exe.sig');
  fs.writeFileSync(signaturePath, 'signed-value\n');
  const manifest = buildManifest({
    version: '0.2.0',
    url: 'https://updates.store.korsenex.com/staging/store-runtime-setup.exe',
    signature: fs.readFileSync(signaturePath, 'utf8').trim(),
    platform: 'windows-x86_64',
    pubDate: '2026-04-14T08:00:00Z',
  });

  assert.equal(manifest.platforms['windows-x86_64'].signature, 'signed-value');
});
