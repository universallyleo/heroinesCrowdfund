<script>
	let { row } = $props();
</script>

<div class="container">
	<div>
		<a href={row.url} target="_blank">
			<!-- <img src="https://api.iconify.design/line-md:external-link.svg" alt="Go to page" /> -->
		</a>
	</div>
	<div>
		<div class="gpcell">{row.group}</div>
		<div class="mbcell">{row.member}</div>
	</div>
</div>

<style>
	.container {
		display: grid;
		grid-template-columns: 40px 1fr;
	}

	.container > div {
		align-self: center;
	}

	/* .gpcell{

    } */

	.mbcell {
		margin-left: 1em;
		margin-top: 0.2em;
		font-weight: bold;
	}

	a::after {
		content: '';
		display: inline-block;
		background-repeat: no-repeat;
		background-size: contain;
		background-position: center;
		width: 16px;
		height: 16px;
		background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='%238d8d8d' d='M18 19H6c-.55 0-1-.45-1-1V6c0-.55.45-1 1-1h5c.55 0 1-.45 1-1s-.45-1-1-1H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-6c0-.55-.45-1-1-1s-1 .45-1 1v5c0 .55-.45 1-1 1M14 4c0 .55.45 1 1 1h2.59l-9.13 9.13a.996.996 0 1 0 1.41 1.41L19 6.41V9c0 .55.45 1 1 1s1-.45 1-1V4c0-.55-.45-1-1-1h-5c-.55 0-1 .45-1 1'/></svg>");
	}
</style>
