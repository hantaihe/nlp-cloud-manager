<script lang="ts">
	import { themeStore, type Theme } from '$lib/theme.svelte';

	const themes: { id: Theme; label: string; icon: string }[] = [
		{ id: 'dark', label: 'Dark', icon: '🌙' },
		{ id: 'light', label: 'Light', icon: '☀️' },
		{ id: 'ocean', label: 'Ocean', icon: '🌊' },
		{ id: 'forest', label: 'Forest', icon: '🌲' }
	];

	let isOpen = $state(false);

	function toggle() {
		isOpen = !isOpen;
	}
	function select(id: Theme) {
		themeStore.setTheme(id);
		isOpen = false;
	}
</script>

<div class="theme-switcher">
	<button class="current-toggle" onclick={toggle} aria-label="Switch theme">
		<span class="icon">{themes.find((t) => t.id === themeStore.current)?.icon}</span>
	</button>

	{#if isOpen}
		<div class="dropdown-overlay" onclick={toggle} role="presentation"></div>
		<div class="dropdown">
			{#each themes as theme}
				<button
					class="theme-opt"
					class:active={themeStore.current === theme.id}
					onclick={() => select(theme.id)}
				>
					<span class="opt-icon">{theme.icon}</span>
					<span class="opt-label">{theme.label}</span>
					{#if themeStore.current === theme.id}
						<span class="check">✓</span>
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.theme-switcher {
		position: relative;
	}

	.current-toggle {
		width: 36px;
		height: 36px;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		transition: all 0.2s;
		font-size: 1.2rem;
	}
	.current-toggle:hover {
		background: var(--color-bg-hover);
		border-color: var(--color-accent);
	}

	.dropdown-overlay {
		position: fixed;
		inset: 0;
		z-index: 1000;
	}

	.dropdown {
		position: absolute;
		top: calc(100% + 8px);
		right: 0;
		width: 160px;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		padding: 0.5rem;
		z-index: 1001;
		box-shadow: var(--shadow-lg);
		animation: slideDown 0.2s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.theme-opt {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.6rem 0.8rem;
		border-radius: 8px;
		color: var(--color-text-secondary);
		transition: all 0.2s;
		font-size: 0.9rem;
		text-align: left;
	}

	.theme-opt:hover {
		background: var(--color-bg-hover);
		color: var(--color-text-primary);
	}
	.theme-opt.active {
		background: var(--color-accent-subtle);
		color: var(--color-accent);
		font-weight: 600;
	}

	.opt-icon {
		font-size: 1.1rem;
	}
	.opt-label {
		flex: 1;
	}
	.check {
		font-size: 0.8rem;
	}
</style>
