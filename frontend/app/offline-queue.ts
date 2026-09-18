export type PendingReport = { id: string; text: string; location_name: string; source_type: 'PWA' };
const database = 'voicerada-offline';
const store = 'reports';

function open() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(database, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(store, { keyPath: 'id' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueReport(report: Omit<PendingReport, 'id'>) {
  const db = await open();
  const item = { ...report, id: crypto.randomUUID() };
  await new Promise<void>((resolve, reject) => {
    const request = db.transaction(store, 'readwrite').objectStore(store).put(item);
    request.onsuccess = () => resolve(); request.onerror = () => reject(request.error);
  });
  db.close();
}

export async function pendingReports(): Promise<PendingReport[]> {
  const db = await open();
  const items = await new Promise<PendingReport[]>((resolve, reject) => {
    const request = db.transaction(store).objectStore(store).getAll();
    request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
  });
  db.close(); return items;
}

export async function removeQueuedReport(id: string) {
  const db = await open();
  await new Promise<void>((resolve, reject) => {
    const request = db.transaction(store, 'readwrite').objectStore(store).delete(id);
    request.onsuccess = () => resolve(); request.onerror = () => reject(request.error);
  });
  db.close();
}
