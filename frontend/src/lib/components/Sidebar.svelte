<script lang="ts">
	import { page } from '$app/stores';
	import logo from '$lib/assets/logo.png';
	import { SERVICES } from '$lib/services';

	interface Props {
		isCollapsed?: boolean;
		onToggle?: () => void;
	}

	let { isCollapsed = false, onToggle }: Props = $props();

	const servicesMenu = $derived([
		{ icon: 'Dashboard', href: '/', symbol: '❖' },
		...SERVICES.map((s) => ({
			icon: s.name,
			href: `/service/${s.id}`,
			imgSrc: s.icon,
			symbol: s.icon ? undefined : '◈'
		}))
	]);
</script>

<aside class="sidebar" class:collapsed={isCollapsed}>
	<div class="sidebar-header">
		<div class="logo">
			<img src={logo} alt="Logo" class="logo-img" />
		</div>
		<button class="toggle-btn" onclick={onToggle} aria-label="Toggle sidebar">
			{isCollapsed ? '▸' : '◂'}
		</button>
	</div>

	<nav class="sidebar-nav">
		<div class="menu-section">
			{#if !isCollapsed}
				<div class="section-header">
					<span class="section-title">Services</span>
				</div>
			{/if}

			<ul class="menu-items">
				{#each servicesMenu as item (item.icon)}
					<li>
						<a
							href={item.href}
							class="menu-item"
							class:active={item.href === '/'
								? $page.url.pathname === '/'
								: $page.url.pathname.startsWith(item.href)}
						>
							<span class="menu-icon">
								{#if item.imgSrc}
									<img src={item.imgSrc} alt="" class="sidebar-logo" />
								{:else if item.symbol}
									{item.symbol}
								{/if}
							</span>
							{#if !isCollapsed}
								<span class="menu-label">{item.icon} Service</span>
							{/if}
						</a>
					</li>
				{/each}
			</ul>
		</div>
	</nav>

	<div class="sidebar-footer"></div>
</aside>

<style>
	.sidebar {
		width: var(--sidebar-width);
		height: 100vh;
		background: var(--color-bg-secondary);
		border-right: 1px solid var(--color-border-subtle);
		display: flex;
		flex-direction: column;
		transition: width var(--transition-normal);
		overflow: hidden;
		position: fixed;
		left: 0;
		top: 0;
		z-index: 100;
	}

	.sidebar.collapsed {
		width: var(--sidebar-collapsed-width);
	}

	.sidebar-header {
		padding: var(--spacing-md);
		border-bottom: 1px solid var(--color-border-subtle);
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 80px;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		overflow: hidden;
	}

	.logo-img {
		width: 64px;
		height: 64px;
		object-fit: contain;
		flex-shrink: 0;
	}

	.toggle-btn {
		padding: var(--spacing-sm) var(--spacing-md);
		color: var(--color-text-muted);
		border-radius: var(--radius-sm);
		font-size: 1rem;
		transition: all var(--transition-fast);
		flex-shrink: 0;
	}

	.toggle-btn:hover {
		background: var(--color-bg-hover);
		color: var(--color-text-primary);
	}

	.sidebar.collapsed .toggle-btn {
		margin: 0 auto;
	}

	.sidebar-nav {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-md) 0;
	}

	.menu-section {
		margin-bottom: var(--spacing-md);
	}

	.section-header {
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.section-title {
		font-size: 0.7rem;
		font-weight: 500;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.menu-items {
		list-style: none;
	}

	.menu-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm) var(--spacing-md);
		margin: 2px var(--spacing-sm);
		color: var(--color-text-secondary);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		font-size: 0.875rem;
	}

	.sidebar.collapsed .menu-item {
		justify-content: center;
		padding: var(--spacing-md);
		margin: 2px var(--spacing-xs);
	}

	.menu-item:hover {
		background: var(--color-bg-hover);
		color: var(--color-text-primary);
	}

	.menu-item.active {
		background: var(--color-bg-elevated);
		color: var(--color-text-primary);
	}

	.menu-icon {
		font-size: 1.1rem;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0.7;
	}

	.sidebar-logo {
		width: 18px;
		height: 18px;
		object-fit: contain;
	}

	.menu-item:hover .menu-icon,
	.menu-item.active .menu-icon {
		opacity: 1;
	}

	.menu-label {
		flex: 1;
		white-space: nowrap;
	}

	.sidebar-footer {
		padding: var(--spacing-md);
		border-top: 1px solid var(--color-border-subtle);
	}
</style>
