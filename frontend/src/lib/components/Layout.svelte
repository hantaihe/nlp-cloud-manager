<script lang="ts">
	import Sidebar from './Sidebar.svelte';
	import Header from './Header.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		title?: string;
		titleHref?: string;
		children: Snippet;
	}

	let { title = 'Dashboard', titleHref, children }: Props = $props();

	let sidebarCollapsed = $state(false);

	function toggleSidebar() {
		sidebarCollapsed = !sidebarCollapsed;
	}
</script>

<div class="layout" class:sidebar-collapsed={sidebarCollapsed}>
	<Sidebar isCollapsed={sidebarCollapsed} onToggle={toggleSidebar} />

	<div class="main-wrapper">
		<Header {title} {titleHref} onToggleSidebar={toggleSidebar} />

		<main class="main-content">
			{@render children()}
		</main>
	</div>
</div>

<style>
	.layout {
		display: flex;
		min-height: 100vh;
	}

	.main-wrapper {
		flex: 1;
		margin-left: var(--sidebar-width);
		transition: margin-left var(--transition-normal);
	}

	.layout.sidebar-collapsed .main-wrapper {
		margin-left: var(--sidebar-collapsed-width);
	}

	.main-content {
		padding: var(--spacing-xl);
		padding-top: calc(var(--header-height) + var(--spacing-xl));
		min-height: 100vh;
		background: var(--color-bg-primary);
	}

	.layout.sidebar-collapsed :global(.header) {
		left: var(--sidebar-collapsed-width);
	}
</style>
