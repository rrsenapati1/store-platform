import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { listArchiveEntries } from './release-archive-utils.mjs';
import { buildWebReleaseArchive } from './package-web-release.mjs';

async function createTempDir(prefix) {
  return fs.mkdtemp(path.join(os.tmpdir(), prefix));
}

test('buildWebReleaseArchive packages the built dist output for a web app', async () => {
  const root = await createTempDir('store-web-release-');
  const distDir = path.join(root, 'platform-admin', 'dist');
  const outputDir = path.join(root, 'release');

  await fs.mkdir(path.join(distDir, 'assets'), { recursive: true });
  await fs.writeFile(path.join(distDir, 'index.html'), '<html></html>');
  await fs.writeFile(path.join(distDir, 'assets', 'index.js'), 'console.log("platform-admin");');

  const archivePath = await buildWebReleaseArchive({
    appName: 'platform-admin',
    distDir,
    outputDir,
    version: '0.1.0',
  });

  assert.equal(path.basename(archivePath), 'platform-admin-0.1.0.tar.gz');

  const entries = await listArchiveEntries(archivePath);
  assert(entries.includes('platform-admin-0.1.0/dist/index.html'));
  assert(entries.includes('platform-admin-0.1.0/dist/assets/index.js'));
});
