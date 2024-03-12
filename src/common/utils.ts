/**
 * Encode just the components of a multi-segment uri,
 * leaving '/' separators
 *
 * @export
 * @param {string} uri
 * @return {string}
 */
export function encodeUriComponents(uri: string): string {
  return uri.split('/').map(encodeURIComponent).join('/');
}

export function formatTime(time: string): string {
  if (!time || time.length === 0) {
    return 'unknown';
  }
  const units: { [key: string]: number } = {
    year: 24 * 60 * 60 * 1000 * 365,
    month: (24 * 60 * 60 * 1000 * 365) / 12,
    day: 24 * 60 * 60 * 1000,
    hour: 60 * 60 * 1000,
    minute: 60 * 1000,
    second: 1000
  };
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const d1 = new Date(time);
  const d2 = new Date();
  const elapsed = d1.getTime() - d2.getTime();
  for (const u in units) {
    if (Math.abs(elapsed) > units[u] || u === 'second') {
      return rtf.format(Math.round(elapsed / units[u]), u as any);
    }
  }
  return 'unknown';
}
