/**
 * WayFi Web UI
 */

async function apiCall(method, path, body = null) {
	const opts = {
		method,
		headers: { 'Content-Type': 'application/json' },
	}
	if (body) opts.body = JSON.stringify(body)
	const resp = await fetch(path, opts)
	if (!resp.ok) {
		const err = await resp.json().catch(() => ({ detail: resp.statusText }))
		throw new Error(err.detail || 'Request failed')
	}
	return resp.json()
}

function formatTime(seconds) {
	if (!seconds || seconds < 0) return '--'
	if (seconds < 60) return seconds + 's'
	if (seconds < 3600) return Math.floor(seconds / 60) + 'm'
	const h = Math.floor(seconds / 3600)
	const m = Math.floor((seconds % 3600) / 60)
	return h + 'h ' + m + 'm'
}

function toast(msg, type = 'success') {
	const el = document.createElement('div')
	el.className = 'toast toast-' + type
	el.textContent = msg
	document.body.appendChild(el)
	setTimeout(() => el.remove(), 3000)
}

function signalBars(quality) {
	const bars = [1, 2, 3, 4]
	const level = quality > 75 ? 4 : quality > 50 ? 3 : quality > 25 ? 2 : 1
	return bars.map(b =>
		'<span class="' + (b <= level ? 'active' : '') + '"></span>'
	).join('')
}

function badge(text, type) {
	return '<span class="badge badge-' + type + '">' + text + '</span>'
}

// Highlight active nav link
document.addEventListener('DOMContentLoaded', () => {
	const path = location.pathname
	document.querySelectorAll('.nav-links a').forEach(a => {
		if (a.getAttribute('href') === path) a.classList.add('active')
	})
})
