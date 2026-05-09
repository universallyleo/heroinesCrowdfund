<script>
	let { table, field, children } = $props();

	const sort = table.createSort(field);
</script>

<th
	onclick={() => sort.set()}
	class={{ active: sort.isActive }}
	aria-sort={sort.direction === 'asc'
		? 'ascending'
		: sort.direction === 'desc'
			? 'descending'
			: 'none'}
>
	<div class="flex">
		<strong>{@render children()}</strong>
		<span
			class="sort-indicator"
			class:asc={sort.direction === 'asc'}
			class:desc={sort.direction === 'desc'}
		></span>
	</div>
</th>

<style>
	th {
		padding: 8px 20px;
		white-space: nowrap;
		user-select: none;
		border-bottom: 1px solid var(--grey, #e0e0e0);
		cursor: pointer;
	}
	th strong {
		white-space: pre-wrap;
		text-align: left;
	}
	div.flex {
		padding: 0;
		display: flex;
		align-items: center;
		justify-content: flex-start;
		height: 100%;
	}
	.sort-indicator {
		padding-left: 8px;
	}
	.sort-indicator:before,
	.sort-indicator:after {
		border: 4px solid transparent;
		content: '';
		display: block;
		height: 0;
		width: 0;
	}
	.sort-indicator:before {
		border-bottom-color: #aaa;
		margin-top: 2px;
	}
	.sort-indicator:after {
		border-top-color: #aaa;
		margin-top: 2px;
	}
	th.active .sort-indicator.asc:before {
		border-bottom-color: #222;
	}
	th.active .sort-indicator.desc:after {
		border-top-color: #222;
	}
</style>
