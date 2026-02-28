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

	let showNotifications = $state(false);
	let showProfile = $state(false);

	const notifications = [
		{ id: 1, type: 'warning', message: '테스트 알림', time: '5m ago' },
		{ id: 2, type: 'info', message: '테스트 알림 2', time: '1h ago' },
		{ id: 3, type: 'success', message: '테스트 알림 3', time: '2h ago' }
	];

	const services = [
		{
			name: 'Sample Service',
			type: 'sample',
			href: '/sample',
			icon: '⚡',
			desc: '샘플 서비스'
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
							<span class="result-icon">{service.icon}</span>
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

		<button class="create-btn">
			<span class="btn-icon">⊕</span>
			<span>Quick Create</span>
		</button>

		<div class="notification-wrapper">
			<button class="icon-btn" onclick={() => (showNotifications = !showNotifications)}>
				<span class="notification-icon">🔔</span>
				<span class="notification-badge">3</span>
			</button>

			{#if showNotifications}
				<div class="dropdown notification-dropdown">
					<div class="dropdown-header">
						<span>Notifications</span>
						<button class="mark-read">모두 읽음</button>
					</div>
					<ul class="notification-list">
						{#each notifications as notif (notif.id)}
							<li class="notification-item {notif.type}">
								<span class="notif-icon">
									{#if notif.type === 'warning'}⚠️{:else if notif.type === 'success'}✅{:else}ℹ️{/if}
								</span>
								<div class="notif-content">
									<p class="notif-message">{notif.message}</p>
									<span class="notif-time">{notif.time}</span>
								</div>
							</li>
						{/each}
					</ul>
				</div>
			{/if}
		</div>

		<div class="profile-wrapper">
			<button class="profile-btn" onclick={() => (showProfile = !showProfile)}>
				<div class="profile-avatar">
					<img src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin" alt="User" />
				</div>
				<span class="profile-name">Admin</span>
				<span class="dropdown-arrow">▾</span>
			</button>

			{#if showProfile}
				<div class="dropdown profile-dropdown">
					<a href="/account" class="dropdown-item">내 계정</a>
					<a href="/security" class="dropdown-item">보안</a>
					<a href="/preferences" class="dropdown-item">설정</a>
					<hr class="dropdown-divider" />
					<button class="dropdown-item logout">로그아웃</button>
				</div>
			{/if}
		</div>
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

	.create-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		color: var(--color-text-primary);
		font-size: 0.875rem;
		font-weight: 500;
		transition: all var(--transition-fast);
	}

	.create-btn:hover {
		background: var(--color-bg-hover);
		border-color: var(--color-text-muted);
	}

	.btn-icon {
		font-size: 1rem;
	}

	.icon-btn {
		position: relative;
		padding: var(--spacing-sm);
		color: var(--color-text-secondary);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
	}

	.icon-btn:hover {
		background: var(--color-bg-hover);
		color: var(--color-text-primary);
	}

	.notification-badge {
		position: absolute;
		top: 2px;
		right: 2px;
		background: var(--color-danger);
		color: white;
		font-size: 0.625rem;
		font-weight: 600;
		width: 16px;
		height: 16px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.notification-wrapper,
	.profile-wrapper {
		position: relative;
	}

	.profile-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-xs) var(--spacing-sm);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
	}

	.profile-btn:hover {
		background: var(--color-bg-hover);
	}

	.profile-avatar {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-md);
		overflow: hidden;
		background: var(--color-bg-tertiary);
	}

	.profile-avatar img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.profile-name {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-text-primary);
	}

	.dropdown-arrow {
		font-size: 0.625rem;
		color: var(--color-text-muted);
	}

	.dropdown {
		position: absolute;
		top: 100%;
		right: 0;
		margin-top: var(--spacing-sm);
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
		animation: fadeIn 0.15s ease-out;
		overflow: hidden;
	}

	.notification-dropdown {
		min-width: 320px;
	}

	.profile-dropdown {
		min-width: 200px;
	}

	.dropdown-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-md);
		border-bottom: 1px solid var(--color-border);
		font-weight: 600;
		font-size: 0.875rem;
	}

	.mark-read {
		color: var(--color-text-muted);
		font-size: 0.75rem;
		font-weight: 500;
	}

	.mark-read:hover {
		color: var(--color-text-primary);
	}

	.notification-list {
		list-style: none;
		max-height: 300px;
		overflow-y: auto;
	}

	.notification-item {
		display: flex;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		border-bottom: 1px solid var(--color-border-subtle);
		transition: background var(--transition-fast);
	}

	.notification-item:hover {
		background: var(--color-bg-hover);
	}

	.notification-item:last-child {
		border-bottom: none;
	}

	.notif-content {
		flex: 1;
	}

	.notif-message {
		font-size: 0.875rem;
		color: var(--color-text-primary);
		margin-bottom: 2px;
	}

	.notif-time {
		font-size: 0.75rem;
		color: var(--color-text-muted);
	}

	.dropdown-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		transition: all var(--transition-fast);
		width: 100%;
		text-align: left;
	}

	.dropdown-item:hover {
		background: var(--color-bg-hover);
		color: var(--color-text-primary);
	}

	.dropdown-divider {
		border: none;
		border-top: 1px solid var(--color-border);
		margin: var(--spacing-xs) 0;
	}

	.logout {
		color: var(--color-danger);
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
		font-size: 1.5rem;
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
