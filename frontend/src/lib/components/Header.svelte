<script lang="ts">
	import ThemeSwitcher from './ThemeSwitcher.svelte';
	import { searchStore } from '$lib/search.svelte';
	import { goto } from '$app/navigation';

	interface Props {
		title?: string;
		titleHref?: string;
		onToggleSidebar?: () => void;
	}

	let { title = 'Documents', titleHref, onToggleSidebar }: Props = $props();

	const services = [
		{
			name: 'Dashboard',
			type: 'dashboard',
			href: '/',
			symbol: '❖',
			desc: '메인 대시보드'
		},
		{
			name: 'AWS Service',
			type: 'aws',
			href: '/aws-cost',
			imgSrc: '/icons/aws.svg',
			desc: 'Amazon Web Services 비용 관리'
		},
		{
			name: 'Azure Service',
			type: 'azure',
			href: '/azure-cost',
			imgSrc: '/icons/azure.svg',
			desc: 'Microsoft Azure 비용 관리'
		},
		{
			name: 'GCP Service',
			type: 'gcp',
			href: '/gcp-cost',
			imgSrc: '/icons/gcp.svg',
			desc: 'Google Cloud Platform 비용 관리'
		}
	];

	let matchingServices = $derived(
		searchStore.query.trim() === ''
			? []
			: services.filter(
					(s) =>
						s.name.toLowerCase().includes(searchStore.query.toLowerCase()) ||
						s.type.toLowerCase().includes(searchStore.query.toLowerCase())
				)
	);

	function navigateTo(path: string) {
		goto(path);
		searchStore.clear();
	}
</script>

<header class="header">
	<div class="header-left">
		{#if titleHref}
			<a href={titleHref} class="page-title link">{title}</a>
		{:else}
			<h1 class="page-title">{title}</h1>
		{/if}
	</div>

	<div class="header-center">
		<div class="search-container">
			<span class="search-icon">⌕</span>
			<input
				type="text"
				class="search-input"
				placeholder="Search services..."
				bind:value={searchStore.query}
			/>
			{#if searchStore.query}
				<button class="search-clear" onclick={() => searchStore.clear()}>✕</button>
			{/if}

			{#if matchingServices.length > 0}
				<div class="search-results-dropdown">
					{#each matchingServices as service}
						<button class="result-item" onclick={() => navigateTo(service.href)}>
							<span class="result-icon">
								{#if service.imgSrc}
									<img src={service.imgSrc} alt="" class="search-result-logo" />
								{:else}
									{service.symbol}
								{/if}
							</span>
							<div class="result-info">
								<span class="result-name">{service.name}</span>
								<span class="result-desc">{service.desc}</span>
							</div>
							<span class="result-arrow">→</span>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<div class="header-right">
		<ThemeSwitcher />
	</div>
</header>

<style>
	.header {
		height: var(--header-height);
		background: var(--color-bg-secondary);
		border-bottom: 1px solid var(--color-border-subtle);
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 var(--spacing-xl);
		position: fixed;
		top: 0;
		right: 0;
		left: var(--sidebar-width);
		z-index: 90;
		transition: left var(--transition-normal);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.page-title {
		font-size: 1.125rem;
		font-weight: 500;
		color: var(--color-text-primary);
	}

	.page-title.link {
		text-decoration: none;
		transition: color var(--transition-fast);
	}

	.page-title.link:hover {
		color: var(--color-text-secondary);
	}

	.header-center {
		flex: 1;
		max-width: 400px;
		margin: 0 var(--spacing-xl);
	}

	.search-container {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-icon {
		position: absolute;
		left: var(--spacing-md);
		font-size: 1rem;
		color: var(--color-text-muted);
	}

	.search-input {
		width: 100%;
		padding: var(--spacing-sm) var(--spacing-lg);
		padding-left: 2.5rem;
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		color: var(--color-text-primary);
		font-size: 0.875rem;
		transition: all var(--transition-fast);
	}

	.search-input::placeholder {
		color: var(--color-text-muted);
	}

	.search-input:focus {
		outline: none;
		border-color: var(--color-text-muted);
		background: var(--color-bg-elevated);
	}

	.search-clear {
		position: absolute;
		right: var(--spacing-md);
		color: var(--color-text-muted);
		font-size: 0.75rem;
		padding: 4px;
	}

	.search-clear:hover {
		color: var(--color-text-primary);
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.search-results-dropdown {
		position: absolute;
		top: calc(100% + 8px);
		left: 0;
		right: 0;
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
		z-index: 1000;
		overflow: hidden;
		animation: slideDown 0.2s ease-out;
	}

	.result-item {
		width: 100%;
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
		text-align: left;
		transition: all 0.2s;
		border-bottom: 1px solid var(--color-border-subtle);
	}

	.result-item:last-child {
		border-bottom: none;
	}

	.result-item:hover {
		background: var(--color-bg-hover);
	}

	.result-icon {
		font-size: 1.25rem;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-text-secondary);
	}

	.search-result-logo {
		width: 22px;
		height: 22px;
		object-fit: contain;
	}

	.result-info {
		flex: 1;
		display: flex;
		flex-direction: column;
	}

	.result-name {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.95rem;
	}

	.result-desc {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.result-arrow {
		color: var(--color-text-muted);
		opacity: 0;
		transition: all 0.2s;
	}

	.result-item:hover .result-arrow {
		opacity: 1;
		transform: translateX(4px);
	}
</style>
