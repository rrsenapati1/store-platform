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
    alembicHead: '20260418_0049_rollback_verification_foundation',
    builtAt: '2026-04-18T12:00:00.000Z',
    gitMetadata: {
      commit: '8a1a8103f0d7d4633ef97bd43af3e0cd91f36f51',
      tree: 'a95d5c1c3b1ff8c6c5af0fc22d7c4b3f2d85c011',
      ref: 'main',
      remote: 'https://github.com/korsenex/store.git',
      worktreeClean: true,
    },
  });

  assert.equal(path.basename(archivePath), 'store-control-plane-0.1.0.tar.gz');
  const manifestPath = path.join(outputDir, 'store-control-plane-0.1.0.manifest.json');
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
  assert.equal(manifest.release_version, '0.1.0');
  assert.equal(manifest.bundle_name, 'store-control-plane-0.1.0');
  assert.equal(manifest.alembic_head, '20260418_0049_rollback_verification_foundation');
  assert.equal(manifest.built_at, '2026-04-18T12:00:00.000Z');
  const provenancePath = path.join(outputDir, 'store-control-plane-0.1.0.provenance.json');
  const provenance = JSON.parse(await fs.readFile(provenancePath, 'utf8'));
  assert.equal(provenance.status, 'passed');
  assert.equal(provenance.release_version, '0.1.0');
  assert.equal(provenance.bundle_name, 'store-control-plane-0.1.0');
  assert.equal(provenance.source_commit, '8a1a8103f0d7d4633ef97bd43af3e0cd91f36f51');
  assert.equal(provenance.source_tree, 'a95d5c1c3b1ff8c6c5af0fc22d7c4b3f2d85c011');
  assert.equal(provenance.source_ref, 'main');
  assert.equal(provenance.source_remote, 'https://github.com/korsenex/store.git');
  assert.equal(provenance.source_worktree_clean, true);
  assert.equal(typeof provenance.archive_sha256, 'string');
  assert.equal(provenance.archive_sha256.length, 64);
  assert.equal(typeof provenance.manifest_sha256, 'string');
  assert.equal(provenance.manifest_sha256.length, 64);

  const entries = await listArchiveEntries(archivePath);

  assert(entries.includes('store-control-plane-0.1.0/README.md'));
  assert(entries.includes('store-control-plane-0.1.0/alembic.ini'));
  assert(entries.includes('store-control-plane-0.1.0/alembic/versions/001_initial.py'));
  assert(entries.includes('store-control-plane-0.1.0/store_control_plane/__init__.py'));
  assert(entries.includes('store-control-plane-0.1.0/release-manifest.json'));
  assert.equal(entries.some((entry) => entry.includes('.venv')), false);
  assert.equal(entries.some((entry) => entry.includes('__pycache__')), false);
  assert.equal(entries.some((entry) => entry.includes('.pytest_cache')), false);
  assert.equal(entries.some((entry) => entry.includes('node_modules')), false);
  assert.equal(entries.some((entry) => entry.includes('local.sqlite')), false);
});
