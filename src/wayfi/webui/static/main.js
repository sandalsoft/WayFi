/**
 * WayFi Web UI — shared utilities
 */

async function apiCall(method, path, body = null) {
	const opts = {
		method,
		headers: { 'Content-Type': 'application/json' },
	};
	if (body) opts.body = JSON.stringify(body);
	const resp = await fetch(path, opts);
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({ detail: resp.statusText }));
		throw new Error(err.detail || 'Request failed');
	}
	return resp.json();
}

function formatTime(seconds) {
	if (seconds < 60) return seconds + 's';
	if (seconds < 3600) return Math.floor(seconds / 60) + 'm';
	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	return h + 'h ' + m + 'm';
}
