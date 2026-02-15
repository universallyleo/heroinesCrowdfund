<script>
	let { row } = $props();
</script>

<div class="container">
	{row.eventYear} <br />
	{row.type}
</div>

<style>
	.container {
		min-width: 70px;
	}
</style>
