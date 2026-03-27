<script lang="ts">
	import { browser } from '$app/environment';
	import { themeStore } from '$lib/theme.svelte';
	import { untrack, onMount } from 'svelte';

	let isOpen = $state(false);
	let isWide = $state(false);
	let iframeElement = $state<HTMLIFrameElement | null>(null);
	let isLoaded = $state(false);

	function toggleChat() {
		isOpen = !isOpen;
	}

	let themeSrc = $derived(() => {
		const baseUrl = 'http://localhost:3106';
		const aws = browser ? localStorage.getItem('aws_active_name') || '' : '';
		const azure = browser ? localStorage.getItem('azure_active_name') || '' : '';
		const gcp = browser ? localStorage.getItem('gcp_active_name') || '' : '';
		return `${baseUrl}?theme=${themeStore.current}&aws=${aws}&azure=${azure}&gcp=${gcp}`;
	});

	async function fetchDefaultCredentials() {
		if (!browser) return;

		const services = [
			{ key: 'aws_active_name', url: 'http://localhost:3002/credentials' },
			{ key: 'azure_active_name', url: 'http://localhost:8001/credentials' },
			{ key: 'gcp_active_name', url: 'http://localhost:8002/credentials' }
		];

		for (const service of services) {
			if (!localStorage.getItem(service.key)) {
				try {
					const res = await fetch(service.url);
					if (res.ok) {
						const creds = await res.json();
						if (creds && creds.length > 0) {
							localStorage.setItem(service.key, creds[0].name);
						}
					}
				} catch (e) {
					console.error(`Error fetching credentials for ${service.key}:`, e);
				}
			}
		}
	}

	$effect(() => {
		const theme = themeStore.current;
		if (iframeElement && iframeElement.contentWindow) {
			untrack(() => {
				iframeElement?.contentWindow?.postMessage({ type: 'THEME_UPDATE', theme }, '*');
			});
		}
	});

	function handleLoad() {
		isLoaded = true;
		if (iframeElement && iframeElement.contentWindow) {
			iframeElement.contentWindow.postMessage(
				{ type: 'THEME_UPDATE', theme: themeStore.current },
				'*'
			);
		}
	}

	onMount(() => {
		fetchDefaultCredentials();

		const handleMessage = (event: MessageEvent) => {
			if (event.data.type === 'RESIZE_CHAT') {
				isWide = event.data.isWide;
			}
		};
		window.addEventListener('message', handleMessage);
		return () => window.removeEventListener('message', handleMessage);
	});
</script>

<div class="chatbot-wrapper">
	<div class="chat-window" class:hidden={!isOpen} class:wide={isWide}>
		<div class="chat-header">
			<h3>AI Assistant</h3>
			<button class="resize-btn" onclick={() => (isWide = !isWide)} aria-label="Resize chat">
				{#if isWide}
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="10" y1="14" x2="3" y2="21"/><line x1="21" y1="3" x2="14" y2="10"/></svg>
				{:else}
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
				{/if}
			</button>
		</div>

		{#if !isLoaded}
			<div class="loading-overlay">
				<div class="spinner"></div>
				<p>Initializing AI...</p>
			</div>
		{/if}

		<iframe
			bind:this={iframeElement}
			src={themeSrc()}
			title="Chatbot"
			onload={handleLoad}
			frameborder="0"
			class:hidden-iframe={!isLoaded}
		></iframe>
	</div>

	<button
		class="inner-close-btn"
		class:hidden={!isOpen}
		onclick={toggleChat}
		aria-label="Close chat">&times;</button
	>

	<button class="fab" onclick={toggleChat} aria-label="Open chat">
		<span>
			{#if isOpen}
				&times;
			{:else}
				<svg
					width="24"
					height="24"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"><path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z" /></svg
				>
			{/if}
		</span>
	</button>
</div>

<style>
	.chatbot-wrapper {
		position: fixed;
		bottom: 30px;
		right: 30px;
		z-index: 1000;
		pointer-events: none;
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}

	.chatbot-wrapper > * {
		pointer-events: auto;
	}

	.chat-window {
		width: 440px;
		height: 680px;
		max-height: 85vh;
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: 20px;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		margin-bottom: 20px;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		transform-origin: bottom right;
	}

	.chat-window.hidden {
		opacity: 0;
		visibility: hidden;
		transform: scale(0.9) translateY(20px);
		pointer-events: none;
	}

	.chat-window.wide {
		width: 800px;
		height: 85vh;
		max-width: 90vw;
		max-height: 85vh;
	}

	.chat-header {
		padding: 12px 20px;
		background: var(--color-bg-tertiary);
		border-bottom: 1px solid var(--color-border);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.chat-header h3 {
		font-size: 0.9rem;
		margin: 0;
	}

	.chat-header button {
		background: none;
		border: none;
		font-size: 1.5rem;
		cursor: pointer;
		color: var(--color-text-muted);
	}

	.resize-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 4px;
		border-radius: 6px;
		transition: background 0.15s, color 0.15s;
	}

	.resize-btn:hover {
		background: var(--color-border);
		color: var(--color-purple);
	}

	iframe {
		flex: 1;
		width: 100%;
		height: 100%;
		transition: opacity 0.3s;
	}

	.hidden-iframe {
		opacity: 0;
		pointer-events: none;
	}

	.loading-overlay {
		position: absolute;
		top: 50px;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: var(--color-bg-card);
		color: var(--color-text-muted);
		z-index: 10;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-border);
		border-top-color: var(--color-purple);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 15px;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.inner-close-btn {
		position: absolute;
		bottom: 20px;
		right: 20px;
		width: 60px;
		height: 60px;
		border-radius: 50%;
		background: var(--color-purple);
		color: white;
		border: none;
		font-size: 1.5rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4);
		transition: all 0.2s;
		z-index: 20;

		position: absolute;
		bottom: 0;
		right: 0;
	}

	.inner-close-btn.hidden {
		opacity: 0;
		visibility: hidden;
		pointer-events: none;
		transform: scale(0.8);
	}

	.inner-close-btn:hover {
		transform: scale(1.1);
		background: #9333ea;
	}

	.fab {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		background: var(--color-purple);
		color: white;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4);
		transition:
			transform 0.2s,
			opacity 0.2s;
	}

	.fab:hover {
		transform: scale(1.1);
	}

	:global(.chat-window:not(.hidden)) ~ .fab {
		opacity: 0;
		pointer-events: none;
	}
</style>
