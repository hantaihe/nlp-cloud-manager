<script lang="ts">
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
		return `${baseUrl}?theme=${themeStore.current}`;
	});

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
		aria-label="Close chat">×</button
	>

	<button class="fab" onclick={toggleChat} aria-label="Open chat">
		<span>{isOpen ? '×' : '💬'}</span>
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
		width: 380px;
		height: 600px;
		max-height: 80vh;
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
		max-width: 90vw;
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
