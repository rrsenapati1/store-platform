#!/usr/bin/env node
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

import { copyTreeFiltered, createTarGz, ensureDirectory, parseCliArgs, removeIfExists, writeJsonFile } from './release-archive-utils.mjs';

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

function resolveAlembicHead({ sourceDir, pythonCommand = process.env.PYTHON || 'python' }) {
  const script = [
    'from pathlib import Path',
    'import sys',
    `source_dir = Path(r"""${sourceDir}""")`,
    'sys.path.insert(0, str(source_dir))',
    'from store_control_plane.ops.postgres_backup import resolve_alembic_head',
    'print(resolve_alembic_head(service_root=source_dir))',
  ].join('\n');
  const result = spawnSync(pythonCommand, ['-c', script], {
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout || `failed to resolve alembic head using ${pythonCommand}`);
  }
  return result.stdout.trim();
}

function runGitCommand(args, { optional = false } = {}) {
  const result = spawnSync('git', args, {
    cwd: repoRoot,
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    if (optional) {
      return null;
    }
    throw new Error(result.stderr || result.stdout || `git ${args.join(' ')} failed with status ${result.status ?? 'unknown'}`);
  }
  return result.stdout.trim();
}

function resolveGitMetadata() {
  const dirtyStatus = runGitCommand(['status', '--porcelain']);
  return {
    commit: runGitCommand(['rev-parse', 'HEAD']),
    tree: runGitCommand(['rev-parse', 'HEAD^{tree}']),
    ref: runGitCommand(['rev-parse', '--abbrev-ref', 'HEAD']),
    remote: runGitCommand(['remote', 'get-url', 'origin'], { optional: true }),
    worktreeClean: dirtyStatus === '',
  };
}

async function sha256File(filePath) {
  const content = await fs.readFile(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

function buildReleaseProvenanceReport({
  archivePath,
  bundleName,
  gitMetadata,
  manifestPath,
  manifest,
  archiveSha256,
  manifestSha256,
  archiveSizeBytes,
}) {
  const normalizedMetadata = {
    commit: typeof gitMetadata?.commit === 'string' ? gitMetadata.commit.trim() : '',
    tree: typeof gitMetadata?.tree === 'string' ? gitMetadata.tree.trim() : '',
    ref: typeof gitMetadata?.ref === 'string' ? gitMetadata.ref.trim() : '',
    remote: typeof gitMetadata?.remote === 'string' ? gitMetadata.remote.trim() : '',
    worktreeClean: gitMetadata?.worktreeClean === true,
  };
  const failureReasons = [];
  if (!normalizedMetadata.commit) {
    failureReasons.push('missing source commit');
  }
  if (!normalizedMetadata.tree) {
    failureReasons.push('missing source tree');
  }
  if (!normalizedMetadata.ref) {
    failureReasons.push('missing source ref');
  }
  if (!normalizedMetadata.remote) {
    failureReasons.push('missing source remote');
  }
  if (!normalizedMetadata.worktreeClean) {
    failureReasons.push('source worktree was not clean at packaging time');
  }
  const failureReason = failureReasons.length > 0 ? failureReasons.join('; ') : null;
  return {
    status: failureReason === null ? 'passed' : 'failed',
    generated_at: manifest.built_at,
    release_version: manifest.release_version,
    bundle_name: bundleName,
    archive_path: archivePath,
    archive_sha256: archiveSha256,
    archive_size_bytes: archiveSizeBytes,
    manifest_path: manifestPath,
    manifest_sha256: manifestSha256,
    source_commit: normalizedMetadata.commit,
    source_tree: normalizedMetadata.tree,
    source_ref: normalizedMetadata.ref,
    source_remote: normalizedMetadata.remote,
    source_worktree_clean: normalizedMetadata.worktreeClean,
    summary: failureReason === null ? 'release provenance verified' : failureReason,
    failure_reason: failureReason,
  };
}

export async function buildControlPlaneReleaseArchive({ sourceDir, outputDir, version, alembicHead, builtAt, gitMetadata }) {
  const normalizedSourceDir = path.resolve(sourceDir);
  const normalizedOutputDir = path.resolve(outputDir);
  const releaseName = `store-control-plane-${version}`;
  const stagingRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'store-control-plane-release-'));
  const stagedReleaseDir = path.join(stagingRoot, releaseName);
  const archivePath = path.join(normalizedOutputDir, `${releaseName}.tar.gz`);
  const manifestPath = path.join(normalizedOutputDir, `${releaseName}.manifest.json`);
  const provenancePath = path.join(normalizedOutputDir, `${releaseName}.provenance.json`);
  const effectiveGitMetadata = gitMetadata ?? resolveGitMetadata();
  const releaseManifest = {
    release_version: version,
    bundle_name: releaseName,
    alembic_head: alembicHead || resolveAlembicHead({ sourceDir: normalizedSourceDir }),
    built_at: builtAt || new Date().toISOString(),
  };

  try {
    await ensureDirectory(normalizedOutputDir);
    await copyTreeFiltered(normalizedSourceDir, stagedReleaseDir, (relativePath) => shouldIncludeControlPlanePath(relativePath));
    await writeJsonFile(path.join(stagedReleaseDir, 'release-manifest.json'), releaseManifest);
    await writeJsonFile(manifestPath, releaseManifest);
    await removeIfExists(archivePath);
    await removeIfExists(provenancePath);
    await createTarGz(stagedReleaseDir, archivePath);
    const archiveSha256 = await sha256File(archivePath);
    const manifestSha256 = await sha256File(manifestPath);
    const archiveStats = await fs.stat(archivePath);
    const provenanceReport = buildReleaseProvenanceReport({
      archivePath,
      archiveSha256,
      archiveSizeBytes: archiveStats.size,
      bundleName: releaseName,
      gitMetadata: effectiveGitMetadata,
      manifest: releaseManifest,
      manifestPath,
      manifestSha256,
    });
    await writeJsonFile(provenancePath, provenanceReport);
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
