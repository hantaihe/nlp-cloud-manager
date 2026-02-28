<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Chatbot from '$lib/components/Chatbot.svelte';
	import Layout from '$lib/components/Layout.svelte';
	import { page } from '$app/stores';
	import { themeStore } from '$lib/theme.svelte';

	let { children } = $props();
	let isTerminal = $derived($page.url.pathname.includes('/terminal'));

	$effect(() => {
		const handleMessage = (event: MessageEvent) => {
			if (event.data.type === 'GET_THEME') {
				(event.source as Window)?.postMessage(
					{ type: 'THEME_UPDATE', theme: themeStore.current },
					{ targetOrigin: '*' }
				);
			}
		};
		window.addEventListener('message', handleMessage);

		const theme = themeStore.current;
		const iframes = document.querySelectorAll('iframe');
		iframes.forEach((iframe) => {
			iframe.contentWindow?.postMessage({ type: 'THEME_UPDATE', theme }, '*');
		});

		return () => window.removeEventListener('message', handleMessage);
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>NLP Cloud Manager</title>
	<meta name="description" content="NLP Cloud Manager" />
</svelte:head>

{#if isTerminal}
	{@render children()}
{:else}
	<Layout title="Dashboard" titleHref="/">
		{@render children()}
	</Layout>
	<Chatbot />
{/if}
