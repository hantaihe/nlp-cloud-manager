<script lang="ts">
	import { themeStore } from '$lib/theme.svelte';
	import { untrack } from 'svelte';

	interface Props {
		src: string;
		title: string;
		isFullPage?: boolean;
	}

	let { src, title, isFullPage = false }: Props = $props();

	let iframeElement = $state<HTMLIFrameElement | null>(null);
	let lastLoadedBaseSrc = $state<string | null>(null);

	$effect(() => {
		if (iframeElement && src !== lastLoadedBaseSrc) {
			const separator = src.includes('?') ? '&' : '?';
			const initialTheme = untrack(() => themeStore.current);
			const fullSrc = `${src}${separator}theme=${initialTheme}`;

			if (iframeElement.src !== fullSrc) {
				iframeElement.src = fullSrc;
				lastLoadedBaseSrc = src;
			}
		}
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
		if (iframeElement && iframeElement.contentWindow) {
			iframeElement.contentWindow.postMessage(
				{ type: 'THEME_UPDATE', theme: themeStore.current },
				'*'
			);
		}
	}
</script>

<div class="mfe-container" class:full-page={isFullPage}>
	<iframe bind:this={iframeElement} {title} onload={handleLoad} frameborder="0" class="mfe-iframe"
	></iframe>
</div>

<style>
	.mfe-container {
		width: 100%;
		height: calc(100vh - var(--header-height) - var(--spacing-xl) * 2);
		border-radius: var(--radius-lg);
		overflow: hidden;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
	}

	.mfe-container.full-page {
		height: 100vh;
		border-radius: 0;
		border: none;
	}

	.mfe-iframe {
		width: 100%;
		height: 100%;
	}
</style>
