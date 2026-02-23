<script>
	let { table, field, children } = $props();

	const sort = table.createSort(field);
</script>

<th onclick={() => sort.set()} class={{ active: sort.isActive }}>
	<div class="flex">
		<strong>{@render children()}</strong>
		<span class={[{ asc: sort.direction === 'asc' }, { desc: sort.direction === 'desc' }]}> </span>
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
	span {
		padding-left: 8px;
	}
	span:before,
	span:after {
		border: 4px solid transparent;
		content: '';
		display: block;
		height: 0;
		width: 0;
	}
	span:before {
		border-bottom-color: #aaa;
		margin-top: 2px;
	}
	span:after {
		border-top-color: #aaa;
		margin-top: 2px;
	}
	th.active span.asc:before {
		border-bottom-color: #222;
	}
	th.active span.desc:after {
		border-top-color: #222;
	}
</style>
