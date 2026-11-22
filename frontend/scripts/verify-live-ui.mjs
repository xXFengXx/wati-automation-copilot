// Opt-in smoke test against the NORMAL app. Makes one REAL, billed inference call.
// No network routes or provider functions are replaced.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium, expect } from '@playwright/test';

const browser = await chromium.launch({channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge', headless: true});
try {
  const page = await browser.newPage({viewport: {width: 1440, height: 1050}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:8000/');
  await page.getByRole('button', {name: 'DeepSeek configured', exact: true}).waitFor();
  const responsePromise = page.waitForResponse(r => r.url().endsWith('/api/flows/generate') && r.request().method() === 'POST', {timeout: 150000});
  await page.getByRole('button', {name: 'Generate flow', exact: true}).click();
  const response = await responsePromise;
  assert.equal(response.status(), 200, 'Live generation failed');
  const record = await response.json();
  assert.equal(record.status, 'generated');
  assert.equal(record.valid, true, 'Generated flow has blocking validation errors');
  assert.notEqual(record.model, 'contract-test-only');
  await page.locator('.react-flow__node').first().waitFor();
  assert.equal(await page.locator('.react-flow__node').count(), record.flow.nodes.length);
  await page.getByRole('button', {name: 'Start simulation', exact: true}).click();
  await page.getByRole('button', {name: 'buyer', exact: true}).click();
  await page.locator('.conversation-complete').waitFor();
  assert.match(await page.locator('.chat-body').innerText(), /assignment to Sales/i);
  await page.getByRole('button', {name: 'Execution trace'}).click();
  assert.match(await page.locator('.trace-list').innerText(), /Sales/);
  await page.getByRole('button', {name: 'Conversation', exact: true}).click();
  assert.deepEqual(errors, [], 'Browser reported a JavaScript error');
  await mkdir('../output', {recursive: true});
  await page.screenshot({path: '../output/live-ui-desktop.png', fullPage: true});
  await page.setViewportSize({width: 390, height: 844});
  await page.evaluate(() => document.fonts.ready);
  // ResizeObserver and graph fitting settle asynchronously after a viewport change.
  await expect.poll(() => page.evaluate(() => {
    const canvas = document.querySelector('.react-flow').getBoundingClientRect();
    return [...document.querySelectorAll('.react-flow__node')].every(node => {
      const b = node.getBoundingClientRect();
      return b.left >= canvas.left + 5 && b.right <= canvas.right - 5 && b.top >= canvas.top + 5 && b.bottom <= canvas.bottom - 5;
    });
  })).toBe(true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await page.screenshot({path: '../output/live-ui-mobile.png', fullPage: true});
  const evidence = {checked_at_utc: new Date().toISOString(), model: record.model, flow_id: record.id, flow_name: record.flow.name, nodes: record.flow.nodes.length, passed: ['real generation', 'graph rendering', 'buyer → Sales', 'execution trace', 'no page errors', 'mobile layout'], request_id: response.headers()['x-request-id']};
  await writeFile('../output/live-ui-result.json', JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  await browser.close();
}
