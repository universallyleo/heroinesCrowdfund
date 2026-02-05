const f = Bun.file('Scrape-page-details-from-camp-fire.jp--imaginate.json', {
	type: 'application/json'
});
const details = await f.json();
const result = details.map((obj) => {
	const pricePatrons = [];

	for (const key of Object.keys(obj)) {
		const m = key.match(/^price(?: \((\d+)\))?$/);
		if (!m) continue;

		const idx = m[1] ?? '';
		const patronsKey = idx ? `patrons (${idx})` : 'patrons';

		if (!(patronsKey in obj)) continue;

		const price = Number(obj[key].replace(/,/g, ''));
		const patrons = Number(obj[patronsKey].replace(/人/g, ''));

		pricePatrons.push({ price, patrons });
	}

	// keep non price/patrons keys
	// const rest = Object.fromEntries(
	// 	Object.entries(obj).filter(([k]) => !k.startsWith('price') && !k.startsWith('patrons'))
	// );

	return {
		// ...rest,
		url: obj.url,
		start: obj.start.replaceAll('/', '-'),
		end: obj.end.replaceAll('/', '-'),
		pricePatrons
	};
});

// await Bun.write("price_patron_grouped.json", JSON.stringify(result, null, 2));

// const [base, details] = await Promise.all( [
//     Bun.file("camp-fire-2026-01-14.json").json(),
//     Bun.file("price_patron_grouped.json").json(),
// ] )
const base = await Bun.file('camp-fire-imaginate-2026-02-05.json').json();

// Build index
const index = new Map(result.map((x) => [x.url, x]));

const merged = base.map((b) => {
	if (!('url' in b)) return { ...b };
	const s = ('per' in b ? b.per === '終了' : true) ? extractGroupMB(b.title) : null;
	const d = index.get(b.url);
	const y = Number(b.sub.slice(0, 4));
	if (isNaN(y)) {
		console.log(b.title, b.sub);
	}
	return d
		? { ...b, ...d, ...(s != null && { subject: s }), eventYear: y }
		: { ...b, ...(s != null && { subject: s }), eventYear: y };
});

// console.log(merged);

function extractGroupMB(str) {
	const m = str.match(/^(.+?)(?:【|＜)(.+?)(?:】|＞)(.*)?$/);
	// "A【1】abc" or "A＜1＞abc"   ->  { group: 'A', member: '1', extra: 'abc' }

	if (!m) {
		console.log('Cannot extract group/mb: ', str);
		return null;
	}

	let res = {
		group: m[1].trim(),
		member: m[2].trim()
	};
	if (m[3]) res.type = m[3].match(/^(.*)応援プロジェクト$/)[1];

	return res;
}

await Bun.write('processed.json', JSON.stringify(merged, null, 2));
