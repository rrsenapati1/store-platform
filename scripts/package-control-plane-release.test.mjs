import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { listArchiveEntries } from './release-archive-utils.mjs';
import { buildControlPlaneReleaseArchive } from './package-control-plane-release.mjs';

async function createTempDir(prefix) {
  return fs.mkdtemp(path.join(os.tmpdir(), prefix));
}

test('buildControlPlaneReleaseArchive packages the service tree and excludes local-only files', async () => {
  const root = await createTempDir('store-control-plane-release-');
  const sourceDir = path.join(root, 'control-plane-api');
  const outputDir = path.join(root, 'dist');

  await fs.mkdir(path.join(sourceDir, 'alembic', 'versions'), { recursive: true });
  await fs.mkdir(path.join(sourceDir, 'store_control_plane'), { recursive: true });
  await fs.mkdir(path.join(sourceDir, '.venv', 'Scripts'), { recursive: true });
  await fs.mkdir(path.join(sourceDir, '__pycache__'), { recursive: true });
  await fs.mkdir(path.join(sourceDir, '.pytest_cache'), { recursive: true });
  await fs.mkdir(path.join(sourceDir, 'node_modules', 'left-pad'), { recursive: true });

  await fs.writeFile(path.join(sourceDir, 'README.md'), '# control plane\n');
  await fs.writeFile(path.join(sourceDir, 'alembic.ini'), '[alembic]\n');
  await fs.writeFile(path.join(sourceDir, 'alembic', 'versions', '001_initial.py'), '# migration\n');
  await fs.writeFile(path.join(sourceDir, 'store_control_plane', '__init__.py'), '__all__ = []\n');
  await fs.writeFile(path.join(sourceDir, '.venv', 'Scripts', 'python.exe'), 'binary');
  await fs.writeFile(path.join(sourceDir, '__pycache__', 'ignored.pyc'), 'cache');
  await fs.writeFile(path.join(sourceDir, '.pytest_cache', 'state'), 'cache');
  await fs.writeFile(path.join(sourceDir, 'node_modules', 'left-pad', 'index.js'), 'module.exports = 1;\n');
  await fs.writeFile(path.join(sourceDir, 'local.sqlite'), 'sqlite');

  const archivePath = await buildControlPlaneReleaseArchive({
    outputDir,
    sourceDir,
    version: '0.1.0',
  });

  assert.equal(path.basename(archivePath), 'store-control-plane-0.1.0.tar.gz');

  const entries = await listArchiveEntries(archivePath);

  assert(entries.includes('store-control-plane-0.1.0/README.md'));
  assert(entries.includes('store-control-plane-0.1.0/alembic.ini'));
  assert(entries.includes('store-control-plane-0.1.0/alembic/versions/001_initial.py'));
  assert(entries.includes('store-control-plane-0.1.0/store_control_plane/__init__.py'));
  assert.equal(entries.some((entry) => entry.includes('.venv')), false);
  assert.equal(entries.some((entry) => entry.includes('__pycache__')), false);
  assert.equal(entries.some((entry) => entry.includes('.pytest_cache')), false);
  assert.equal(entries.some((entry) => entry.includes('node_modules')), false);
  assert.equal(entries.some((entry) => entry.includes('local.sqlite')), false);
});
