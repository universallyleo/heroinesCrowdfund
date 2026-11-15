<script>
	let { sort, onSort, children, zindex = 7, frozen = false } = $props();
</script>

<th
	class={{ active: sort.isActive, frozen }}
	style="z-index: {zindex}"
	aria-sort={sort.direction === 'asc'
		? 'ascending'
		: sort.direction === 'desc'
			? 'descending'
			: 'none'}
>
	<button class="flex" onclick={() => onSort(sort)}>
		<strong>{@render children()}</strong>
		<span
			class="sort-indicator"
			class:asc={sort.direction === 'asc'}
			class:desc={sort.direction === 'desc'}
		></span>
	</button>
</th>

<style>
	th {
		white-space: normal;
		word-break: break-word;
		user-select: none;
		border-bottom: 1px solid var(--grey, #e0e0e0);
		cursor: pointer;
		position: sticky;
		top: 0;
		z-index: 10;
	}
	th strong {
		white-space: pre-wrap;
		text-align: left;
	}
	button.flex {
		background: transparent;
		color: inherit;
		border: 0;
		font: inherit;
		cursor: pointer;
		width: 100%;
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
