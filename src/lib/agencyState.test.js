// @ts-nocheck
import { expect, test } from 'bun:test';
import * as state from './agencyState.js';
import * as catalog from './agencyCatalog.js';

const view = {
	gpMap: new Map([['A', {}]]),
	processedData: [
		{ group: ['A'], member: '甲, 乙', eventYear: 2026, total: 155500 },
		{ group: ['A'], member: '丙', eventYear: 2025, total: 0 }
	]
};
test('draft edits stay unapplied; reset preserves sort and size and resets page', () => {
	expect(typeof state.createAgencyState).toBe('function');
	const a = state.createAgencyState(view),
		b = state.createAgencyState(view);
	expect(a.draft.minFund).toBe(0);
	expect(a.draft.maxFund).toBe(156);
	a.draft.member = '乙';
	expect(state.filterAgencyRows(view.processedData, a.applied)).toHaveLength(2);
	state.applyDraft(a);
	expect(state.filterAgencyRows(view.processedData, a.applied)).toHaveLength(1);
	a.draft.member = '丙';
	expect(a.applied.member).toBe('乙');
	expect(b.applied.member).toBe('');
	a.sort = { field: 'total', direction: 'desc' };
	a.pageSize = 5;
	a.page = 2;
	state.resetFilters(a, view);
	expect(a.page).toBe(1);
	expect(a.pageSize).toBe(5);
	expect(a.sort.direction).toBe('desc');
	expect(state.filterAgencyRows(view.processedData, a.applied)).toHaveLength(2);
	a.draft.minFund = 999;
	expect(() => state.applyDraft(a)).toThrow();
});
test('loader retries failures, caches success, and selection suppresses stale completion', async () => {
	expect(typeof catalog.createAgencyLoader).toBe('function');
	let attempts = 0;
	const loader = catalog.createAgencyLoader({
		a: async () => {
			if (++attempts === 1) throw Error('network');
			return { default: [] };
		}
	});
	await expect(loader('a')).rejects.toThrow('network');
	expect(await loader('a')).toEqual([]);
	await loader('a');
	expect(attempts).toBe(2);
	await expect(loader('unknown')).rejects.toThrow();
	let finish;
	const selected = catalog.createSelectionLoader((id) =>
		id === 'slow' ? new Promise((resolve) => (finish = resolve)) : Promise.resolve(['fast'])
	);
	const seen = [];
	const slow = selected('slow', (result) => seen.push(result));
	await selected('fast', (result) => seen.push(result));
	finish(['slow']);
	await slow;
	expect(seen).toEqual([{ status: 'ready', data: ['fast'] }]);
});

test('invalid catalogue configuration is rejected before rendering a default agency', () => {
	expect(typeof catalog.validateCatalog).toBe('function');
	const registry = {
		schemaVersion: 1,
		defaultAgencyId: 'a',
		agencies: [
			{
				id: 'a',
				label: 'A',
				sources: [{ label: 'A', url: 'https://example.com' }],
				databasePath: 'src/lib/data/agencies/a/projects.json',
				metadataPath: 'src/lib/data/agencies/a/metadata.json'
			}
		]
	};
	const files = { './data/agencies/a/projects.json': async () => ({ default: [] }) };
	const metadata = {
		'./data/agencies/a/metadata.json': { schemaVersion: 1, agencyId: 'a', updatedAt: null }
	};
	expect(catalog.validateCatalog(registry, files, metadata)).toHaveLength(1);
	expect(() =>
		catalog.validateCatalog({ ...registry, defaultAgencyId: 'missing' }, files, metadata)
	).toThrow();
	expect(() =>
		catalog.validateCatalog(
			{ ...registry, agencies: [...registry.agencies, ...registry.agencies] },
			files,
			metadata
		)
	).toThrow();
	expect(() => catalog.validateCatalog(registry, {}, metadata)).toThrow();
});
