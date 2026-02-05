<script>
	import { MoneyString } from './procData';
	let { row } = $props();

	let bgc =
		row.total < 1_000_000
			? '#fff7ee'
			: row.total < 4_000_000
				? '#ffcccf'
				: row.total < 8_000_000
					? '#ffb995'
					: '#ff7200';
</script>

<div class="container" style="--bgc:{bgc}">
	{MoneyString(row.total)}
</div>

<style>
	.container {
		background-color: var(--bgc);
		display: flex;
		align-items: center; /* vertical center */
		justify-content: flex-end; /* keep right alignment */
		font-size: large;
		font-weight: bold;
		padding: 0.4em;
		height: 100%;
	}
</style>
