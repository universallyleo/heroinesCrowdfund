<script>
	import { gpMap } from '$lib/procData';
	let { gps, selected = $bindable() } = $props();

	function toggle(val) {
		if (selected.includes(val)) {
			selected = selected.filter((v) => v !== val);
		} else {
			selected = [...selected, val];
		}
	}
</script>

<div class="label-inline">
	<span>グループ</span>
	<button
		type="button"
		class="reset-gp"
		class:reset-gp-inactive={selected.length === gps.length}
		onclick={() => (selected = [...gps])}
		title="全部"
	>
		全部
	</button>
	<button
		type="button"
		class="reset-gp"
		class:reset-gp-inactive={selected.length === 0}
		onclick={() => (selected = [])}
		title="解除"
	>
		解除
	</button>
</div>

<div class="group-filter">
	{#each gps as gp}
		<label class="group-item" class:active={selected.includes(gp)}>
			<input type="checkbox" checked={selected.includes(gp)} onchange={() => toggle(gp)} />
			<span class="name">{gp}</span>
			<span class="count">{gpMap.get(gp)?.count ?? 0}</span>
		</label>
	{/each}
</div>

<style>
	.group-filter {
		display: flex;
		flex-direction: column;
		gap: 2px;
		max-height: 20em;
		overflow-y: auto;
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 4px;
		background: var(--bg);
	}

	.group-item {
		display: flex;
		align-items: center;
		padding: 4px 4px;
		cursor: pointer;
		border-radius: 4px;
		font-size: 0.9rem;
		transition: background 0.1s;
		user-select: none;
	}

	.group-item:hover {
		background: var(--bg-emph);
	}

	.group-item.active {
		background: var(--bg-emph2);
		font-weight: bold;
	}

	.group-item input {
		width: auto !important;
		margin-right: 6px;
		cursor: pointer;
	}

	.name {
		flex: 1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.count {
		font-size: 0.75rem;
		color: var(--muted);
		margin-left: 8px;
		background: var(--panel);
		padding: 1px 3px;
		border-radius: 1px;
		min-width: 1.2em;
		text-align: center;
	}
</style>
