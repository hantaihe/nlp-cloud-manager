<script lang="ts">
	import { page } from '$app/state';
	import { themeStore } from '$lib/theme.svelte';
	import { SERVICES } from '$lib/services';

	let id = $derived(page.params.id);
	let service = $derived(SERVICES.find((s) => s.id === id));
	let isLoaded = $state(false);

	$effect(() => {
		if (id) isLoaded = false;
	});
</script>

<div class="iframe-container">
	{#if !service}
		<div class="error-overlay">
			<p>Service "{id}" not found.</p>
		</div>
	{:else}
		{#if !isLoaded}
			<div class="loading-overlay">
				<div class="spinner" style="border-top-color: {service.color}"></div>
				<p>Loading {service.name} Service...</p>
			</div>
		{/if}
		<iframe
			src="{service.url}?theme={themeStore.current}"
			title="{service.name} Service"
			frameborder="0"
			class:hidden={!isLoaded}
			onload={() => (isLoaded = true)}
		></iframe>
	{/if}
</div>

<style>
	.iframe-container {
		width: 100%;
		height: calc(100vh - var(--header-height) - var(--spacing-xl) * 2);
		background: var(--color-bg-primary);
		border-radius: var(--radius-lg);
		overflow: hidden;
		border: 1px solid var(--color-border-subtle);
		box-shadow: var(--shadow-sm);
		position: relative;
	}

	.loading-overlay,
	.error-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-md);
		background: var(--color-bg-primary);
		color: var(--color-text-secondary);
		z-index: 10;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-border);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	iframe {
		width: 100%;
		height: 100%;
		opacity: 1;
		transition: opacity 0.5s ease-in-out;
	}

	iframe.hidden {
		opacity: 0;
	}
</style>
