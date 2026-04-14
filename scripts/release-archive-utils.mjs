#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

export async function ensureDirectory(directory) {
  await fs.mkdir(directory, { recursive: true });
}

export async function removeIfExists(targetPath) {
  await fs.rm(targetPath, { recursive: true, force: true });
}

export async function copyTreeFiltered(sourceDir, targetDir, shouldInclude) {
  const entries = await fs.readdir(sourceDir, { withFileTypes: true });
  await ensureDirectory(targetDir);

  for (const entry of entries) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);
    const relativePath = path.relative(sourceDir, sourcePath);

    if (!shouldInclude(relativePath, entry)) {
      continue;
    }

    if (entry.isDirectory()) {
      await copyTreeFiltered(sourcePath, targetPath, (nestedRelativePath, nestedEntry) =>
        shouldInclude(path.join(relativePath, nestedRelativePath), nestedEntry),
      );
      continue;
    }

    await ensureDirectory(path.dirname(targetPath));
    await fs.copyFile(sourcePath, targetPath);
  }
}

function runTar(args) {
  const result = spawnSync('tar', args, {
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout || `tar failed with status ${result.status ?? 'unknown'}`);
  }
  return result.stdout;
}

export async function createTarGz(sourceDir, outputFile) {
  await ensureDirectory(path.dirname(outputFile));
  runTar(['-czf', outputFile, '-C', path.dirname(sourceDir), path.basename(sourceDir)]);
  return outputFile;
}

export async function listArchiveEntries(archiveFile) {
  const output = runTar(['-tf', archiveFile]);
  return output
    .split(/\r?\n/u)
    .map((line) => line.trim())
    .filter(Boolean);
}

export function parseCliArgs(argv) {
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

export function writeJsonFile(filePath, payload) {
  return fs.writeFile(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}
