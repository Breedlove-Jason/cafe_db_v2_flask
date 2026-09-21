export function validateCafe(data) {
  if (!data || typeof data.name !== 'string' || !data.name.trim() || data.name.trim().length > 120) throw new Error('Enter a cafe name (up to 120 characters).');
  if (typeof data.location !== 'string' || data.location.length > 500) throw new Error('Map links must be 500 characters or fewer.');
  let url; try { url = new URL(data.location); } catch { throw new Error('Enter a valid HTTPS map link.'); }
  if (url.protocol !== 'https:' || url.username || url.password) throw new Error('Use an HTTPS map link without credentials.');
  const cafe = { name: data.name.trim(), location: url.href, sample: false };
  for (const key of ['open_time','close_time']) { if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(data[key])) throw new Error('Enter valid opening and closing times.'); cafe[key] = data[key]; }
  for (const key of ['coffee_rating','wifi_rating','power_rating']) { const value = data[key]; if (!Number.isInteger(value) || value < 0 || value > 5) throw new Error('Ratings must be whole numbers from 0 to 5.'); cafe[key] = value; }
  return cafe;
}
export function filterCafes(cafes, {q='',coffee=0,wifi=0,power=0,sort='work'} = {}) {
  const rows = cafes.filter(c => c.name.toLowerCase().includes(q.trim().toLowerCase()) && c.coffee_rating >= Number(coffee) && c.wifi_rating >= Number(wifi) && c.power_rating >= Number(power));
  return rows.sort((a,b) => { let difference = 0; if (sort === 'work') difference = b.wifi_rating+b.power_rating-a.wifi_rating-a.power_rating; else if (sort !== 'name') difference = b[`${sort}_rating`]-a[`${sort}_rating`]; return difference || a.name.localeCompare(b.name); });
}
export function readWorkspace(raw) {
  const empty = { cafes: [], saved: [] };
  if (!raw) return empty;
  try { const data = JSON.parse(raw); if (!Array.isArray(data.cafes) || !Array.isArray(data.saved)) return empty;
    const ids = new Set();
    const cafes = data.cafes.slice(0,100).flatMap(c => { try { if (typeof c.id !== 'string' || !/^local-[\w-]+$/.test(c.id) || ids.has(c.id)) return []; const value = validateCafe(c); ids.add(c.id); return [{ ...value, id: c.id }]; } catch { return []; } });
    return { cafes, saved: [...new Set(data.saved.filter(id => typeof id === 'number' && Number.isSafeInteger(id) && id > 0 || typeof id === 'string' && ids.has(id)))].slice(0,300) };
  } catch { return empty; }
}
