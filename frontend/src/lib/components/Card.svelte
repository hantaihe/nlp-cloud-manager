<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		value: string | number;
		subtitle?: string;
		icon?: string;
		trend?: {
			value: number;
			direction: 'up' | 'down' | 'neutral';
		};
		color?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
		href?: string;
		children?: Snippet;
		action?: Snippet;
	}

	let {
		title,
		value,
		subtitle = '',
		icon = '📊',
		trend,
		color = 'default',
		href,
		children,
		action
	}: Props = $props();

	const trendIcon = $derived(
		trend?.direction === 'up' ? '↑' : trend?.direction === 'down' ? '↓' : '→'
	);

	const trendClass = $derived(
		trend?.direction === 'up'
			? 'trend-up'
			: trend?.direction === 'down'
				? 'trend-down'
				: 'trend-neutral'
	);
</script>

{#if href}
	<a {href} class="card-link">
		<article class="card {color} clickable">
			<div class="card-header">
				<span class="card-icon">{icon}</span>
				<h3 class="card-title">{title}</h3>
			</div>

			<div class="card-body">
				<div class="card-value">{value}</div>

				{#if subtitle}
					<p class="card-subtitle">{subtitle}</p>
				{/if}

				{#if trend}
					<div class="card-trend {trendClass}">
						<span class="trend-icon">{trendIcon}</span>
						<span class="trend-value">{Math.abs(trend.value)}%</span>
						<span class="trend-label">vs last month</span>
					</div>
				{/if}
			</div>

			{#if children}
				<div class="card-footer">
					{@render children()}
				</div>
			{/if}
		</article>
	</a>
{:else}
	<article class="card {color}">
		<div class="card-header">
			<div class="card-header-main">
				<span class="card-icon">{icon}</span>
				<h3 class="card-title">{title}</h3>
			</div>
			{#if action}
				<div class="card-action">
					{@render action()}
				</div>
			{/if}
		</div>

		<div class="card-body">
			<div class="card-value">{value}</div>

			{#if subtitle}
				<p class="card-subtitle">{subtitle}</p>
			{/if}

			{#if trend}
				<div class="card-trend {trendClass}">
					<span class="trend-icon">{trendIcon}</span>
					<span class="trend-value">{Math.abs(trend.value)}%</span>
					<span class="trend-label">vs last month</span>
				</div>
			{/if}
		</div>

		{#if children}
			<div class="card-footer">
				{@render children()}
			</div>
		{/if}
	</article>
{/if}

<style>
	.card {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
		transition: all var(--transition-fast);
	}

	.card:hover {
		border-color: var(--color-accent);
		box-shadow: var(--shadow-md);
		transform: translateY(-2px);
	}

	.card.success {
		border-left: 4px solid var(--color-success);
	}

	.card.warning {
		border-left: 4px solid var(--color-warning);
	}

	.card.danger {
		border-left: 4px solid var(--color-danger);
	}

	.card.info {
		border-left: 4px solid var(--color-info);
	}

	.card.purple {
		border-left: 4px solid var(--color-purple);
	}

	.card-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-md);
	}

	.card-header-main {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.card-action {
		margin-left: auto;
	}

	.card-icon {
		font-size: 1.25rem;
	}

	.card-title {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.025em;
	}

	.card-body {
		margin-bottom: var(--spacing-sm);
	}

	.card-value {
		font-size: 2rem;
		font-weight: 700;
		color: var(--color-text-primary);
		line-height: 1.2;
		margin-bottom: var(--spacing-xs);
	}

	.card-subtitle {
		font-size: 0.875rem;
		color: var(--color-text-muted);
	}

	.card-trend {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		margin-top: var(--spacing-sm);
		font-size: 0.875rem;
	}

	.trend-up {
		color: var(--color-success);
	}

	.trend-down {
		color: var(--color-danger);
	}

	.trend-neutral {
		color: var(--color-text-muted);
	}

	.trend-icon {
		font-weight: 700;
	}

	.trend-value {
		font-weight: 600;
	}

	.trend-label {
		color: var(--color-text-muted);
	}

	.card-footer {
		margin-top: var(--spacing-md);
		padding-top: var(--spacing-md);
		border-top: 1px solid var(--color-border);
	}

	.card-link {
		text-decoration: none;
		color: inherit;
		display: block;
		height: 100%;
	}

	.card.clickable:hover {
		cursor: pointer;
		border-color: var(--color-accent);
		background: var(--color-bg-hover);
	}
</style>
