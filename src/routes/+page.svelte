<script>
	// @ts-nocheck
	import ghlogo from '$lib/assets/github.svg';
	import xicon from '$lib/assets/X_icon.svg';
	import AgencyProjects from '$lib/AgencyProjects.svelte';
	import { agencies, defaultAgencyId, loadAgency, configurationError } from '$lib/agencies.js';
	import { createSelectionLoader, formatUpdateDate } from '$lib/agencyCatalog.js';
	import { processAgencyData } from '$lib/procData.js';
	import { createAgencyState } from '$lib/agencyState.js';
	let selectedId = $state(defaultAgencyId);
	let selected = $derived(agencies.find((agency) => agency.id === selectedId));
	let result = $state({ status: 'loading' });
	let sessions = $state({});
	const select = createSelectionLoader(async (id) => processAgencyData(await loadAgency(id)));
	function load(id) {
		result = { status: 'loading' };
		select(id, (value) => {
			if (value.status === 'ready' && !sessions[id]) sessions[id] = createAgencyState(value.data);
			result = { ...value, agencyId: id };
		});
	}
	$effect(() => {
		if (!configurationError) load(selectedId);
	});
	let title = $derived(selected ? `${selected.label} クラファ記録` : 'クラファ記録');
	const structuredData = JSON.stringify({
		'@context': 'https://schema.org',
		'@type': 'WebSite',
		name: 'アイドル クラファ記録',
		url: 'https://universallyleo.github.io/heroinesCrowdfund/'
	});
</script>

<svelte:head>
	<title>{title}</title>
	<meta
		name="description"
		content="アイドルのクラウドファンディング記録を事務所別に閲覧できます。"
	/>
	<meta property="og:site_name" content="アイドル クラファ記録" />
	<meta property="og:title" content={title} />
	{@html '<script type="application/ld+json">' + structuredData + '</script>'}
</svelte:head>
<main>
	{#if configurationError}<p role="alert">データ設定を読み込めませんでした。</p>
		<button onclick={() => window.location.reload()}>ページを再読み込み</button>{:else}
		<header>
			<h1>{title}</h1>
			<div class="agency-details">
				<label class="agency-select"
					>事務所<select bind:value={selectedId}
						>{#each agencies as agency}<option value={agency.id}>{agency.label}</option
							>{/each}</select
					></label
				>
				<div class="agency-meta">
					<div>
						データソース：{#each selected.sources as source, i}{#if i > 0}・{/if}<a
								href={source.url}>{source.label}</a
							>{/each}
					</div>
					<div>データ最終更新：{formatUpdateDate(selected.metadata.updatedAt)}</div>
				</div>
			</div>
		</header>
		<div aria-live="polite" class="load-status">
			{#if result.status === 'loading' || result.agencyId !== selectedId}<p>
					データを読み込んでいます…
				</p>
			{:else if result.status === 'error'}
				<p>データを読み込めませんでした。</p>
				<button onclick={() => load(selectedId)}>再試行</button><button
					onclick={() => window.location.reload()}>ページを再読み込み</button
				>
			{:else if result.data.processedData.length === 0}<p>
					この事務所の終了済みプロジェクトはまだありません。
				</p>
			{:else}<p class="sr-only">{selected.label} のデータを読み込みました。</p>
			{/if}
		</div>
		{#if result.status === 'ready' && result.agencyId === selectedId && result.data.processedData.length > 0}
			{#key result.agencyId}<AgencyProjects
					view={result.data}
					bind:settings={sessions[result.agencyId]}
				/>{/key}
		{/if}
		<footer>
			<div>サイト更新：{formatUpdateDate(__BUILD_DATE__)}</div>
			<div class="footer-links">
				<a href="https://github.com/universallyleo/heroinesCrowdfund"
					><img width="32" src={ghlogo} alt="ソースコード" /></a
				>
				<a href="https://x.com/55gohan06"><img width="32" src={xicon} alt="X" /></a>
				<a href="https://universallyleo.github.io/heroinesLeague/">ヒロインズリーグ記録</a>
			</div>
		</footer>
	{/if}
</main>

<style>
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip-path: inset(50%);
		white-space: nowrap;
	}
	main {
		padding: 12px;
		font-family: var(--font-body);
		display: flex;
		flex-direction: column;
		gap: 12px;
		min-width: 0;
	}
	header {
		padding: 1.2em;
		background: var(--panel);
		border-top: 4px solid var(--border-strong);
	}
	h1 {
		margin: 0 0 0.7em;
		font-size: clamp(1.3rem, 3vw, 1.8rem);
		overflow-wrap: anywhere;
	}
	.agency-details {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 1em 2em;
	}
	.agency-select {
		display: flex;
		align-items: center;
		gap: 0.6em;
		font-weight: bold;
		max-width: 100%;
	}
	select {
		padding: 0.5em;
		font: inherit;
		max-width: 100%;
		min-width: 0;
		border: 1px solid var(--border);
		border-radius: 6px;
		background: var(--bg);
		color: var(--text);
	}
	.agency-meta {
		color: var(--muted);
		font-size: 0.9rem;
		line-height: 1.8;
		overflow-wrap: anywhere;
	}
	.load-status:empty {
		display: none;
	}
	footer {
		padding: 1em;
		border-top: 1px solid var(--muted);
		color: var(--muted);
		text-align: center;
		font-size: 0.9rem;
	}
	.footer-links {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: center;
		gap: 1em;
		margin-top: 0.5em;
	}
	@media (max-width: 499px) {
		main {
			padding: 8px;
		}
		header {
			padding: 0.8em;
		}
		.agency-select {
			width: 100%;
		}
		select {
			flex: 1;
		}
	}
</style>
