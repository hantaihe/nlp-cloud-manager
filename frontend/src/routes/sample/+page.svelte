<script lang="ts">
	import { themeStore } from '$lib/theme.svelte';
	let isLoaded = $state(false);
</script>

<div class="iframe-container">
	{#if !isLoaded}
		<div class="loading-overlay">
			<div class="spinner"></div>
			<p>Loading Service...</p>
		</div>
	{/if}
	<iframe
		src="http://127.0.0.1:5174?theme={themeStore.current}"
		title="Sample Service"
		frameborder="0"
		class:hidden={!isLoaded}
		onload={() => (isLoaded = true)}
	></iframe>
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

	.loading-overlay {
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
		border-top-color: var(--color-accent);
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
