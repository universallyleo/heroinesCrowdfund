<script>
	import favicon from '$lib/assets/hcf.png';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}

<style>
	:root {
		--bg: #f7f7f8;
		--panel: #ffffff;
		--border: #d0d0d5;
		--border-strong: #b0b0b8;
		--text: #222;
		--muted: #666;
		--accent: #3b82f6;
		--font-body:
			Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			'Open Sans', 'Helvetica Neue', sans-serif;
		--font-mono: 'Fira Mono', monospace;
	}

	* {
		box-sizing: border-box;
	}
	body {
		margin: 0;
		font-family: var(--font-body);
		background: var(--bg);
		color: var(--text);
	}
</style>
