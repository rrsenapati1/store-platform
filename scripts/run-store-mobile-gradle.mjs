#!/usr/bin/env node
import { spawn } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';

const repoRoot = path.resolve(import.meta.dirname, '..');
const appDir = path.join(repoRoot, 'apps', 'store-mobile');

function printHelp() {
  console.log(`Run the Store Mobile Gradle wrapper from the repo root

Usage:
  node scripts/run-store-mobile-gradle.mjs <gradle-task> [additional-args...]

Examples:
  node scripts/run-store-mobile-gradle.mjs testDebugUnitTest
  node scripts/run-store-mobile-gradle.mjs testDebugUnitTest --tests com.store.mobile.ui.runtime.RuntimeStatusScreenTest
`);
}

const args = process.argv.slice(2);
if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  printHelp();
  process.exit(args.length === 0 ? 1 : 0);
}

const child = process.platform === 'win32'
  ? spawn('cmd.exe', ['/d', '/s', '/c', 'gradlew.bat', ...args], {
      cwd: appDir,
      stdio: 'inherit',
    })
  : spawn('./gradlew', args, {
      cwd: appDir,
      stdio: 'inherit',
    });

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

child.on('error', (error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
