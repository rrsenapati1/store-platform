import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

const repoRoot = path.resolve(import.meta.dirname, '..');

async function readWorkflow(fileName) {
  return fs.readFile(path.join(repoRoot, '.github', 'workflows', fileName), 'utf8');
}

test('ci workflow runs pull-request verification for backend, web, desktop, and automation jobs', async () => {
  const workflow = await readWorkflow('ci.yml');

  assert.match(workflow, /pull_request:/);
  assert.match(workflow, /backend:/);
  assert.match(workflow, /web:/);
  assert.match(workflow, /desktop:/);
  assert.match(workflow, /release-automation:/);
  assert.match(workflow, /npm run ci:platform-admin/);
  assert.match(workflow, /npm run ci:owner-web/);
  assert.match(workflow, /npm run ci:store-desktop/);
  assert.match(workflow, /npm run ci:release-automation/);
  assert.match(workflow, /python -m pytest services\/control-plane-api\/tests -q/);
});

test('release workflow builds artifacts on tags and publishes them to GitHub releases', async () => {
  const workflow = await readWorkflow('release-artifacts.yml');

  assert.match(workflow, /workflow_dispatch:/);
  assert.match(workflow, /tags:/);
  assert.match(workflow, /- 'v\*'/);
  assert.match(workflow, /control-plane-release:/);
  assert.match(workflow, /web-release:/);
  assert.match(workflow, /desktop-release:/);
  assert.match(workflow, /publish-release:/);
  assert.match(workflow, /node scripts\/package-control-plane-release\.mjs/);
  assert.match(workflow, /node scripts\/package-web-release\.mjs --app platform-admin/);
  assert.match(workflow, /node scripts\/package-web-release\.mjs --app owner-web/);
  assert.match(workflow, /node scripts\/build-store-desktop-release\.mjs --profile/);
  assert.match(workflow, /node scripts\/stage-store-desktop-release-artifacts\.mjs/);
  assert.match(workflow, /softprops\/action-gh-release@/);
});
