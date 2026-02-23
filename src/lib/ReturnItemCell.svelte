<script>
	import { MoneyString } from './procData';

	let { row } = $props();
	// $inspect(row.pricePatrons);
</script>

<div class="container">
	{#each row.pricePatrons as pp}
		<div class="col">
			<div>{MoneyString(pp.price, true)}k</div>
			<div>{pp.patrons}人</div>
		</div>
	{/each}
	{#if row.pricePatrons.length < 7}
		{#each { length: 7 - row.pricePatrons.length }, row}
			<div class="col"></div>
		{/each}
	{/if}
	<div class="final">
		<span style="font-size:small;"> 合計金額 </span><br />
		{MoneyString(row.ppTotal)}
	</div>
</div>

<style>
	.container {
		display: grid;
		grid-template-columns: repeat(7, 4.2em) 5.5em;
		grid-column-gap: 0.2em;
		/* border: 1px red solid; */
	}

	.container > .col {
		/* border: 1px blue solid; */
		align-self: center;
		display: grid;
		grid-template-rows: repeat(2, 1fr);
		grid-row-gap: 0.1em;
	}

	.container > .col > div {
		text-align: end;
	}

	.container > .final {
		/* border: 1px black solid; */
		border-left: 1px #aaa solid;
		/* margin-left: 0.1em; */
		/* padding-left: 0.3em; */
		/* justify-self: end; */
		/* align-self: end; */
		text-align: end;
	}
</style>
