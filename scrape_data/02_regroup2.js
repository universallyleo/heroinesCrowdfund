const details = await Bun.file('Scrape-page-details-starts_ends_dates.json').json();

// Build index
const index = new Map(
	details
		.map((x) => {
			return { url: x.url, start: x.start.replaceAll('/', '-'), end: x.end.replaceAll('/', '-') };
		})
		.map((x) => [x.url, x])
);

const base = await Bun.file('20260114.json').json();

// const newbase = base.map((x) => {
// 	return { ...x, eventYear: Number(x.sub.slice(0, 4)) };
// });
// await Bun.write('20260114new.json', JSON.stringify(newbase, null, 2));

const merged = base.map((b) => {
	if (!('url' in b)) return { ...b };
	b.rest = Number(b.rest.replace('人', ''));
	const d = index.get(b.url);
	return d ? { ...b, ...d } : { ...b };
});

// console.log(merged);

await Bun.write('processed3.json', JSON.stringify(merged, null, 2));
