<script>
	// @ts-nocheck

	import { MoneyString, gpMap, mbSet, yrSelection } from '$lib/procData';
	// import { SvelteSet } from 'svelte/reactivity';
	let { grid } = $props();

	const gps = [...gpMap.keys()];
	let gpFilt = $state(gps);
	let gpResetBtnClass = $state('reset-gp');
	let mbFilt = $state('');
	let yrFilt = $state('');
	let minFundFilt = $state(100);
	let maxFundFilt = $state(200000);
	let members = $state([...mbSet]);

	const when = (cond, obj) => (cond ? obj : {});

	let filtObj = $derived({
		...when(gpFilt !== '', { group: gpFilt }),
		...when(mbFilt !== '', { member: mbFilt }),
		...when(yrFilt !== '', { eventYear: Number(yrFilt) }),
		minFund: minFundFilt * 1000,
		maxFund: maxFundFilt * 1000
	});

	function handleFilter() {
		const filters = Object.keys(filtObj).map((key) => {
			const value = filtObj[key];
			console.log(filtObj);
			switch (key) {
				case 'minFund': {
					return (v) => v.total >= value;
				}
				case 'maxFund': {
					return (v) => v.total <= value;
				}
				case 'group': {
					return (v) => value.reduce((res, cur) => res || v[key].indexOf(cur) > -1, false);
				}
				default: {
					return (v) => v[key] === value;
				}
			}
		});
		// console.log('Created filter: ', filters);

		const filter = (obj) => {
			for (let i = 0; i < filters.length; i++) {
				if (!filters[i](obj)) {
					return false;
				}
			}
			return true;
		};
		grid.exec('filter-rows', { filter });
	}

	function clear() {
		gpFilt = [...gpMap.keys()];
		mbFilt = '';
		yrFilt = '';
		minFundFilt = 400;
		maxFundFilt = 20000;
		members = [...mbSet];
		grid.exec('filter-rows', {});
	}

	function repopulateMbList() {
		[members, gpResetBtnClass] =
			gpFilt.length === gps.length
				? [[...mbSet], 'reset-gp']
				: [
						[...gpFilt.reduce((res, gp) => res.union(gpMap.get(gp)), new Set())],
						'reset-gp-inactive'
					];
	}
</script>

<aside>
	<h3>絞り込む</h3>

	<div class="filter-group">
		<label>
			<div class="label-inline">
				<span>グループ</span>
				<button
					type="button"
					class={gpResetBtnClass}
					onclick={() => {
						gpFilt = gps;
						repopulateMbList();
					}}
					title="全部"
				>
					全部
				</button>
			</div>
			<select id="gpFilter" bind:value={gpFilt} onchange={repopulateMbList} multiple size="6">
				<!-- <option value=""> 全部 </option> -->
				{#each gpMap.keys() as gp (gp)}
					<option value={gp}> {gp} </option>
				{/each}
			</select>
		</label>
	</div>

	<div class="filter-group">
		<label>
			メンバー
			<select bind:value={mbFilt}>
				<option value=""> 全員 </option>
				{#each members as mb (mb)}
					<option value={mb}> {mb} </option>
				{/each}
			</select>
		</label>
	</div>

	<div class="filter-group">
		<label>
			実施年
			<select bind:value={yrFilt}>
				<option value="">全部</option>
				{#each yrSelection as yr (yr)}
					<option value={yr}> {yr} </option>
				{/each}
			</select>
		</label>
	</div>

	<div class="filter-group">
		<span> 支援額範囲 (~千円) : </span><br />
		<label class="range-label">
			<div class="label-text">
				最小: {MoneyString(minFundFilt)}k
			</div>
			<input
				type="range"
				id="minFund"
				name="minFund"
				bind:value={minFundFilt}
				min="10"
				max="18000"
			/>
		</label>
		<label class="range-label">
			<div class="label-text">
				最大: {MoneyString(maxFundFilt)}k
			</div>
			<input
				type="range"
				id="maxFund"
				name="maxFund"
				bind:value={maxFundFilt}
				min="500"
				max="20000"
			/>
		</label>
	</div>
	<div class="filter-btns">
		<button onclick={() => handleFilter()}>条件を適用</button>
		<button onclick={() => clear()}>リセット</button>
	</div>
</aside>

<style>
	aside {
		font-family: var(--font-body);
		background: var(--panel);
		border: 1px solid var(--border);
		border-radius: 10px;
		padding: 12px;
	}

	aside > h3 {
		margin: 0 0 0.4em 0;
		font-weight: normal;
		text-align: center;
	}

	.filter-btns {
		margin: 2px auto;
	}

	.filter-group {
		margin-bottom: 1.3em;
		min-width: 0;
	}

	.filter-group label:not(.range-label) {
		display: block;
		margin-bottom: 0.5em;
	}

	.label-inline {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}

	.reset-gp {
		font-size: 0.85rem;
		padding: 0.18rem 0.45rem;
		border: 1px solid var(--border);
		border-radius: 0px;
		background: transparent;
		color: var(--text);
		cursor: pointer;
	}

	.reset-gp-inactive {
		border: 1px solid var(--border);
		background: transparent;
		color: var(--border);
	}

	.filter-group input,
	.filter-group select {
		width: 100%;
		padding: 6px;
		border: 1px solid var(--border);
		border-radius: 6px;
	}

	.range-label {
		display: grid;
		grid-template-rows: auto 1fr;
		row-gap: 0.25rem;
		/* margin: 0.2em 0.5em; */
		margin-right: 1em;
		min-width: 0;
	}

	.range-label > .label-text {
		white-space: nowrap;
	}

	.range-label > input[type='range'] {
		margin: 0 auto;
		width: 95%;
		min-width: 0;
	}

	#gpFilter {
		size: 6;
	}

	@media screen and (max-width: 999px) {
		#gpFilter {
			size: 3;
		}

		.filter-group {
			margin-bottom: 0.2em;
		}

		/* Make label + select appear inline on small screens */
		.filter-group > label:not(.range-label) {
			display: flex;
			flex-direction: row;
			align-items: center;
			justify-content: space-between;
			gap: 0.5rem;
			margin-bottom: 0;
		}

		.filter-group > label:not(.range-label) > select {
			width: auto;
			min-width: 60%;
			flex: 0 0 auto;
		}

		/* Make range-label a single row on small screens */
		.range-label {
			display: grid;
			grid-template-columns: 1fr 60%; /* left flexible, right fixed 60% */
			align-items: center; /* vertical center */
			column-gap: 0.5rem;
			width: 100%;
		}

		.range-label .label-text {
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
			min-width: 0; /* important so the label can shrink */
		}

		.range-label input[type='range'] {
			justify-self: end; /* ensures it sits at the right edge of that column */
			box-sizing: border-box;
		}
	}
</style>
