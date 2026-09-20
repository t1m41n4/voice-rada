import { afterEach, expect, test } from 'vitest';
import { pendingReportCount, pendingReports, queueReport, removeQueuedReport } from '../app/offline-queue';

afterEach(async () => {
  const pending = await pendingReports();
  await Promise.all(pending.map((item) => removeQueuedReport(item.id)));
});

test('stores a text report locally until it can be delivered', async () => {
  await queueReport({ text: 'Flooding near the river', location_name: 'Kibera', source_type: 'PWA' });
  const pending = await pendingReports();
  expect(pending).toHaveLength(1);
  expect(await pendingReportCount()).toBe(1);
  await removeQueuedReport(pending[0].id);
  expect(await pendingReportCount()).toBe(0);
});
