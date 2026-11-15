// @ts-nocheck
// Parent-owned session state: drafts must never double as applied filters.
export function createAgencyState(view) {
	const amounts = view.processedData.map((row) => row.total);
	const filters = {
		groups: [...view.gpMap.keys()],
		member: '',
		year: '',
		minFund: Math.floor((amounts.length ? Math.min(...amounts) : 0) / 1000),
		maxFund: Math.ceil(Math.max(0, ...amounts) / 1000)
	};
	return { draft: structuredClone(filters), applied: filters, sort: null, pageSize: 20, page: 1 };
}
const copyFilters = (filters) => ({ ...filters, groups: [...filters.groups] });
export function applyDraft(state) {
	const { minFund, maxFund } = state.draft;
	if (!Number.isFinite(minFund) || !Number.isFinite(maxFund) || minFund > maxFund)
		throw new Error('支援額の最小値は最大値以下にしてください。');
	state.applied = copyFilters(state.draft);
	state.page = 1;
}
export function resetFilters(state, view) {
	const initial = createAgencyState(view);
	state.draft = initial.draft;
	state.applied = initial.applied;
	state.page = 1;
}
export function filterAgencyRows(rows, filters) {
	return rows.filter(
		(row) =>
			row.group.some((group) => filters.groups.includes(group)) &&
			(!filters.member ||
				row.member
					.split(',')
					.map((s) => s.trim())
					.includes(filters.member)) &&
			(filters.year === '' || row.eventYear === Number(filters.year)) &&
			row.total >= filters.minFund * 1000 &&
			row.total <= filters.maxFund * 1000
	);
}
