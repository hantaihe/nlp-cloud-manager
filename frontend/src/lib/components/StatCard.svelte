<script lang="ts">
	import type { Snippet } from 'svelte';
	import MiniChart from './MiniChart.svelte';

	interface DataPoint {
		label: string;
		value: number;
		displayValue?: string;
		color?: string;
	}

	interface Props {
		title: string;
		value?: string | number;
		subtitle?: string;
		unit?: string;
		icon?: string;
		color?:
			| 'default'
			| 'aws'
			| 'azure'
			| 'gcp'
			| 'combined'
			| 'success'
			| 'warning'
			| 'danger'
			| 'info'
			| 'purple';
		trend?: { value: number; direction: 'up' | 'down' | 'neutral' };
		mode?: 'kpi' | 'chart' | 'list' | 'progress';
		chartType?: 'sparkline' | 'minibar';
		chartData?: DataPoint[];
		chartColor?: string;
		progress?: number;
		error?: string;
		imgSrc?: string;
		href?: string;
		children?: Snippet;
		action?: Snippet;
	}

	let {
		title,
		value = '',
		subtitle = '',
		unit = '',
		icon = '',
		imgSrc = '',
		color = 'default',
		trend,
		mode = 'kpi',
		chartType = 'sparkline',
		chartData = [],
		chartColor,
		progress = 0,
		error = '',
		href,
		children,
		action
	}: Props = $props();

	const trendIcon = $derived(
		trend?.direction === 'up' ? '▲' : trend?.direction === 'down' ? '▼' : '▬'
	);

	const trendClass = $derived(
		trend?.direction === 'up'
			? 'trend-up'
			: trend?.direction === 'down'
				? 'trend-down'
				: 'trend-neutral'
	);

	const progressColor = $derived(
		progress > 90
			? 'var(--color-danger)'
			: progress > 70
				? 'var(--color-warning)'
				: 'var(--color-success)'
	);
</script>

<article class="stat-card {color}">
	<div class="stat-header">
		<div class="stat-header-main">
			{#if imgSrc}
				<img src={imgSrc} alt="" class="stat-logo" />
			{:else if icon}
				<span class="stat-icon">{icon}</span>
			{/if}
			<h3 class="stat-title">{title}</h3>
		</div>
		{#if action}
			<div class="stat-action">
				{@render action()}
			</div>
		{/if}
	</div>

	<div class="stat-body">
		{#if error}
			<div class="error-container">
				<p class="error-message">{error}</p>
			</div>
		{:else if mode === 'kpi'}
			<div class="kpi-content">
				<div class="kpi-value-row">
					<span class="kpi-value">{value}</span>
					{#if unit}
						<span class="kpi-unit">{unit}</span>
					{/if}
				</div>
				{#if trend}
					<div class="stat-trend {trendClass}">
						<span class="trend-icon">{trendIcon}</span>
						<span class="trend-value">{Math.abs(trend.value)}%</span>
						<span class="trend-label">전월 대비</span>
					</div>
				{/if}
				{#if subtitle}
					<p class="stat-subtitle">{subtitle}</p>
				{/if}
				{#if chartData.length > 0}
					<div class="kpi-sparkline">
						<MiniChart
							type="sparkline"
							data={chartData}
							height={40}
							color={chartColor || 'var(--color-accent)'}
						/>
					</div>
				{/if}
			</div>
		{:else if mode === 'chart'}
			<div class="chart-content">
				{#if value}
					<div class="chart-value-row">
						<span class="chart-main-value">{value}</span>
						{#if unit}<span class="kpi-unit">{unit}</span>{/if}
						{#if trend}
							<span class="inline-trend {trendClass}">
								{trendIcon}
								{Math.abs(trend.value)}%
							</span>
						{/if}
					</div>
				{/if}
				<div class="chart-area">
					<MiniChart
						type={chartType}
						data={chartData}
						height={100}
						color={chartColor || 'var(--color-accent)'}
					/>
				</div>
			</div>
		{:else if mode === 'list'}
			<div class="list-content">
				<MiniChart
					type="minibar"
					data={chartData}
					height={140}
					color={chartColor || 'var(--color-accent)'}
				/>
			</div>
		{:else if mode === 'progress'}
			<div class="progress-content">
				<div class="kpi-value-row">
					<span class="kpi-value">{value}</span>
					{#if unit}<span class="kpi-unit">{unit}</span>{/if}
				</div>
				{#if subtitle}
					<p class="stat-subtitle">{subtitle}</p>
				{/if}
				<div class="progress-bar-container">
					<div class="progress-bar-track">
						<div
							class="progress-bar-fill"
							style="width: {Math.min(progress, 100)}%; background: {progressColor};"
						></div>
					</div>
					<span class="progress-label" style="color: {progressColor};">{progress}%</span>
				</div>
			</div>
		{/if}
	</div>

	{#if children}
		<div class="stat-footer">
			{@render children()}
		</div>
	{/if}

	{#if href}
		<a {href} class="stat-link" aria-label="Go to {title}">
			<span class="link-arrow">→</span>
		</a>
	{/if}
</article>

<style>
	.stat-card {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: 1rem;
		transition: all var(--transition-fast);
		position: relative;
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
	}

	.stat-card:hover {
		border-color: var(--color-accent);
		box-shadow: var(--shadow-md);
		transform: translateY(-1px);
	}

	.stat-card.aws {
		border-left: 4px solid #ff9900;
	}
	.stat-card.azure {
		border-left: 4px solid #0078d4;
	}
	.stat-card.gcp {
		border-left: 4px solid #4285f4;
	}
	.stat-card.combined {
		border-left: 4px solid var(--color-purple);
	}
	.stat-card.success {
		border-left: 4px solid var(--color-success);
	}
	.stat-card.warning {
		border-left: 4px solid var(--color-warning);
	}
	.stat-card.danger {
		border-left: 4px solid var(--color-danger);
	}
	.stat-card.info {
		border-left: 4px solid var(--color-info);
	}
	.stat-card.purple {
		border-left: 4px solid var(--color-purple);
	}

	.stat-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
		flex-shrink: 0;
	}

	.stat-header-main {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		min-width: 0;
	}

	.stat-logo {
		width: 1.25rem;
		height: 1.25rem;
		object-fit: contain;
		flex-shrink: 0;
	}

	.stat-icon {
		font-size: 1rem;
		flex-shrink: 0;
	}

	.stat-title {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.stat-action {
		margin-left: auto;
		flex-shrink: 0;
	}

	.stat-body {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
	}

	.kpi-content {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.kpi-value-row {
		display: flex;
		align-items: baseline;
		gap: 0.3rem;
	}

	.kpi-value {
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--color-text-primary);
		line-height: 1.1;
	}

	.kpi-unit {
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--color-text-muted);
	}

	.kpi-sparkline {
		margin-top: auto;
		padding-top: 0.25rem;
	}

	.chart-content {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		flex: 1;
	}

	.chart-value-row {
		display: flex;
		align-items: baseline;
		gap: 0.4rem;
	}

	.chart-main-value {
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--color-text-primary);
	}

	.inline-trend {
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.1rem 0.35rem;
		border-radius: 4px;
	}

	.inline-trend.trend-up {
		color: var(--color-success);
		background: var(--color-success-bg);
	}

	.inline-trend.trend-down {
		color: var(--color-danger);
		background: var(--color-danger-bg);
	}

	.inline-trend.trend-neutral {
		color: var(--color-text-muted);
		background: var(--color-bg-tertiary);
	}

	.chart-area {
		flex: 1;
		min-height: 0;
	}

	.list-content {
		flex: 1;
	}

	.progress-content {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.progress-bar-container {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}

	.progress-bar-track {
		flex: 1;
		height: 8px;
		background: var(--color-bg-tertiary);
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.progress-label {
		font-size: 0.8rem;
		font-weight: 700;
		min-width: 36px;
		text-align: right;
	}

	.stat-trend {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.8rem;
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
		font-size: 0.7rem;
	}

	.stat-subtitle {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		margin-top: 0.15rem;
	}

	.stat-footer {
		margin-top: auto;
		padding-top: 0.5rem;
		border-top: 1px solid var(--color-border);
		flex-shrink: 0;
	}

	.stat-link {
		position: absolute;
		top: 0.75rem;
		right: 0.75rem;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		background: var(--color-bg-tertiary);
		color: var(--color-text-muted);
		text-decoration: none;
		font-size: 0.8rem;
		transition: all var(--transition-fast);
		opacity: 0;
	}

	.stat-card:hover .stat-link {
		opacity: 1;
	}

	.stat-link:hover {
		background: var(--color-accent);
		color: white;
	}

	.error-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		gap: 0.5rem;
		padding: 1rem 0;
		height: 100%;
		opacity: 0.8;
	}

	.error-icon {
		font-size: 1.5rem;
	}

	.error-message {
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--color-text-muted);
		line-height: 1.4;
	}
</style>
