import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { stageStoreDesktopReleaseArtifacts } from './stage-store-desktop-release-artifacts.mjs';

async function createTempDir(prefix) {
  return fs.mkdtemp(path.join(os.tmpdir(), prefix));
}

test('stageStoreDesktopReleaseArtifacts collects the installer, signature, and metadata', async () => {
  const root = await createTempDir('store-desktop-release-');
  const bundleDir = path.join(root, 'bundle', 'nsis');
  const outputDir = path.join(root, 'dist');

  await fs.mkdir(bundleDir, { recursive: true });
  await fs.writeFile(path.join(bundleDir, 'Store Runtime_0.1.0_x64-setup.exe'), 'installer');
  await fs.writeFile(path.join(bundleDir, 'Store Runtime_0.1.0_x64-setup.exe.sig'), 'signature');

  const stagedDir = await stageStoreDesktopReleaseArtifacts({
    bundleDir,
    outputDir,
    profile: 'staging',
    version: '0.1.0',
  });

  const files = await fs.readdir(stagedDir);
  assert(files.includes('Store Runtime_0.1.0_x64-setup.exe'));
  assert(files.includes('Store Runtime_0.1.0_x64-setup.exe.sig'));
  assert(files.includes('release-metadata.json'));

  const metadata = JSON.parse(await fs.readFile(path.join(stagedDir, 'release-metadata.json'), 'utf8'));
  assert.equal(metadata.version, '0.1.0');
  assert.equal(metadata.profile, 'staging');
  assert.equal(metadata.installerFileName, 'Store Runtime_0.1.0_x64-setup.exe');
  assert.equal(metadata.signatureFileName, 'Store Runtime_0.1.0_x64-setup.exe.sig');
});
