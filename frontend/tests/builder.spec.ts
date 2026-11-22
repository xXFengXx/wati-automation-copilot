import { test, expect } from '@playwright/test';

test.beforeEach(async ({page}) => {
  await page.goto('/');
  await expect(page.getByRole('button', {name: 'DeepSeek configured'})).toBeVisible();
});

test('generates a graph, inspects JSON, exports and routes both answers', async ({page}) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await expect(page.locator('.react-flow__node')).toHaveCount(6);
  await expect.poll(async () => page.evaluate(() => {
    const canvas = document.querySelector('.react-flow')!.getBoundingClientRect();
    return [...document.querySelectorAll('.react-flow__node')].flatMap(node => {
      const bounds = node.getBoundingClientRect();
      return bounds.top >= canvas.top + 5 && bounds.bottom <= canvas.bottom - 5 ? [] : [{node: node.getAttribute('data-id'), top: bounds.top, bottom: bounds.bottom, canvasTop: canvas.top, canvasBottom: canvas.bottom}];
    });
  })).toEqual([]);
  await page.locator('.react-flow__node').filter({hasText: 'Condition'}).click();
  await expect(page.locator('.node-details')).toContainText('buyer');
  await page.getByRole('button', {name: 'JSON', exact: true}).click();
  await expect(page.locator('.json-view')).toContainText('assign_team');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', {name: 'Download flow JSON'}).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('automation-flow.json');
  await page.getByRole('button', {name: 'Flow', exact: true}).click();
  await page.getByRole('button', {name: 'Start simulation'}).click();
  await page.getByRole('button', {name: 'buyer', exact: true}).click();
  await expect(page.locator('.conversation-complete')).toBeVisible();
  await expect(page.locator('.chat-body')).toContainText('SIMULATED assignment to Sales');
  await expect(page.locator('.flow-card.visited')).toHaveCount(5);
  await page.getByRole('button', {name: 'Restart simulation'}).click();
  await page.getByRole('button', {name: 'seller', exact: true}).click();
  await expect(page.locator('.chat-body')).toContainText('https://example.com/help');
  await expect(page.locator('.chat-body')).not.toContainText('assignment to Sales');
  await page.screenshot({path: '../tmp/browser-tests/routing-desktop.png', fullPage: true});
  expect(errors).toEqual([]);
});

test('virtual wait and no-reply take different paths', async ({page}) => {
  await page.getByRole('button', {name: 'Follow up gently'}).click();
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await page.getByRole('button', {name: 'Start simulation'}).click();
  await page.getByRole('button', {name: 'yes', exact: true}).click();
  await expect(page.locator('.virtual-clock')).toHaveText('+30m');
  await expect(page.locator('.chat-body')).toContainText('demo reminder');
  await page.getByRole('button', {name: 'Restart simulation'}).click();
  await page.getByRole('button', {name: 'Simulate no reply'}).click();
  await expect(page.locator('.virtual-clock')).toHaveText('+1h');
  await expect(page.locator('.chat-body')).toContainText('Just checking in');
  await page.getByRole('button', {name: 'Execution trace'}).click();
  await expect(page.locator('.trace-list')).toContainText('Followup');
});

test('API failure shows safe handoff without a success result', async ({page}) => {
  await page.getByRole('button', {name: 'Handle API failures'}).click();
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await page.getByLabel('Business API outcome').selectOption('api_failure');
  await page.getByRole('button', {name: 'Start simulation'}).click();
  await page.getByRole('textbox', {name: 'Your reply'}).fill('A123');
  await page.getByRole('button', {name: 'Send reply'}).click();
  await expect(page.locator('.chat-body')).toContainText('assignment to Support');
  await expect(page.locator('.chat-body')).not.toContainText('in transit');
  await page.getByRole('button', {name: 'Execution trace'}).click();
  await expect(page.locator('.trace-list')).toContainText('No business request sent');
});

test('clarifications, invalid flows and model errors are visible', async ({page}) => {
  await page.getByLabel('Describe your automation').fill('Send a help article with missing URL.');
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await expect(page.locator('.clarification')).toContainText('What is your help article URL?');
  await expect(page.getByRole('button', {name: 'Start simulation'})).toBeDisabled();
  await page.getByLabel('Describe your automation').fill('Generate a broken buyer routing flow.');
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await expect(page.locator('.review-summary')).toContainText('blocking issue');
  await expect(page.getByRole('button', {name: 'Start simulation'})).toBeDisabled();
  await page.getByLabel('Describe your automation').fill('A model error should be shown.');
  await page.getByRole('button', {name: 'Regenerate flow'}).click();
  await expect(page.getByRole('alert')).toContainText('rate limiting');
});

test('mobile layout remains usable without horizontal overflow', async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await expect(page.locator('.react-flow__node')).toHaveCount(6);
  await page.getByRole('button', {name: 'Start simulation'}).click();
  await page.getByRole('button', {name: 'seller', exact: true}).click();
  await expect(page.locator('.conversation-complete')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path: '../tmp/browser-tests/routing-mobile.png', fullPage: true});
});

test('a dangling connection remains inspectable without crashing the graph', async ({page}) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.getByLabel('Describe your automation').fill('Show a dangling buyer routing flow.');
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await expect(page.locator('.review-view')).toContainText('missing node');
  await page.getByRole('button', {name: 'Flow', exact: true}).click();
  await expect(page.locator('.react-flow__node')).toHaveCount(6);
  await expect(page.getByRole('button', {name: 'Start simulation'})).toBeDisabled();
  expect(errors).toEqual([]);
});

test('an existing flow recenters after resizing from desktop to mobile', async ({page}) => {
  await page.getByRole('button', {name: 'Generate flow'}).click();
  await expect(page.locator('.react-flow__node')).toHaveCount(6);
  await page.setViewportSize({width: 390, height: 844});
  await expect.poll(() => page.evaluate(() => {
    const canvas = document.querySelector('.react-flow')!.getBoundingClientRect();
    return [...document.querySelectorAll('.react-flow__node')].flatMap(node => {
      const b = node.getBoundingClientRect();
      return b.left >= canvas.left + 5 && b.right <= canvas.right - 5 && b.top >= canvas.top + 5 && b.bottom <= canvas.bottom - 5 ? [] : [node.getAttribute('data-id')];
    });
  })).toEqual([]);
});
