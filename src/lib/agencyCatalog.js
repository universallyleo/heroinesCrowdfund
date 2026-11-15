// @ts-nocheck
export const localDataPath = (path) => path.replace('src/lib/', './');
export function validateCatalog(registry, snapshots, metadata) {
	if (registry.schemaVersion !== 1 || !Array.isArray(registry.agencies))
		throw new Error('Invalid registry');
	const ids = new Set();
	const result = registry.agencies.map((agency) => {
		const meta = metadata[localDataPath(agency.metadataPath)];
		if (
			!/^[a-z][a-z0-9_]*$/.test(agency.id) ||
			ids.has(agency.id) ||
			!agency.label ||
			!agency.sources?.length ||
			!snapshots[localDataPath(agency.databasePath)] ||
			meta?.agencyId !== agency.id ||
			meta.schemaVersion !== 1 ||
			(meta.updatedAt !== null && (!meta.updatedAt || !Number.isFinite(Date.parse(meta.updatedAt))))
		)
			throw new Error('Invalid agency configuration');
		ids.add(agency.id);
		return { ...agency, metadata: meta };
	});
	if (!ids.has(registry.defaultAgencyId)) throw new Error('Invalid default agency');
	return result;
}
export function createAgencyLoader(loaders) {
	const cache = new Map();
	return async (id) => {
		if (!Object.hasOwn(loaders, id)) throw new Error('Unknown agency');
		if (!cache.has(id)) {
			const data = (await loaders[id]()).default;
			if (!Array.isArray(data)) throw new Error('Invalid snapshot');
			cache.set(id, data);
		}
		return cache.get(id);
	};
}
export function createSelectionLoader(load) {
	let generation = 0;
	return async (id, publish) => {
		const request = ++generation;
		try {
			const data = await load(id);
			if (request === generation) publish({ status: 'ready', data });
		} catch (error) {
			if (request === generation) publish({ status: 'error' });
		}
	};
}
export function formatUpdateDate(iso) {
	return iso
		? new Intl.DateTimeFormat('ja-JP', {
				timeZone: 'Asia/Tokyo',
				year: 'numeric',
				month: '2-digit',
				day: '2-digit',
				hour: '2-digit',
				minute: '2-digit',
				hour12: false
			}).format(new Date(iso)) + '（日本時間）'
		: '更新日不明';
}
