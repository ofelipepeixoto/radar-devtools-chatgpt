// Candidate correction for CorentinTh/it-tools, GPL-3.0. Audit 2026-10-21.
export { getHeaders, convertArrayToCsv };

function getHeaders({ array }: { array: Record<string, unknown>[] }): string[] {
  const headers = new Set<string>();
  array.forEach(item => Object.keys(item).forEach(key => headers.add(key)));
  return Array.from(headers);
}

function serializeValue(value: unknown): string {
  if (value === null) return 'null';
  if (value === undefined) return '';
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function convertArrayToCsv({ array }: { array: Record<string, unknown>[] }): string {
  const headers = getHeaders({ array });
  const rows = array.map(item => headers.map(header => serializeValue(item[header])).join(','));
  return [headers.map(serializeValue).join(','), ...rows].join('\n');
}
