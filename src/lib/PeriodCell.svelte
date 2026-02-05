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
		grid-template-columns: 1fr 40px;
	}

	.container > div {
		align-self: center;
	}
</style>
