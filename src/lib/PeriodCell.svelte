<script>
	let { row } = $props();
</script>

<div class="container">
	<div>
		{row.start} <br />
		{row.end}
	</div>
	<div>({row.period}日)</div>
</div>

<style>
	.container {
		display: grid;
		gap: 0.5em;
		grid-template-columns: 1fr 3em;
		min-width: 9em;
	}

	.container > div {
		align-self: center;
	}
</style>
