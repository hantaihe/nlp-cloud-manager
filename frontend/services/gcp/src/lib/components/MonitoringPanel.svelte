<script lang="ts">
	interface MetricPoint {
		interval_start: string;
		interval_end: string;
		value: number;
	}

	interface TimeSeries {
		metric_kind?: string;
		resource_type?: string;
		resource_labels?: Record<string, string>;
		points?: MetricPoint[];
	}

	let { metrics = [] }: { metrics: TimeSeries[] } = $props();
</script>

<div class="monitoring-container glass">
	<h3>Monitoring Metrics</h3>
	<div class="metrics-grid">
		{#if metrics.length === 0}
			<p class="empty">조회된 모니터링 데이터가 없습니다.</p>
		{:else}
			{#each metrics as metric}
				<div class="metric-card">
					<div class="metric-header">
						<span class="metric-kind">{metric.metric_kind || 'Unknown Kind'}</span>
						<span class="badge">{metric.resource_type || 'Unknown Resource'}</span>
					</div>
					
					{#if metric.resource_labels && Object.keys(metric.resource_labels).length > 0}
						<div class="labels-container">
							{#each Object.entries(metric.resource_labels) as [k, v]}
								<div class="label-chip">
									<span class="label-key">{k}:</span>
									<span class="label-value">{v}</span>
								</div>
							{/each}
						</div>
					{/if}

					{#if metric.points && metric.points.length > 0}
						<div class="points-summary">
							Latest Value: <strong>{metric.points[0].value}</strong>
							<span class="time-hint">
								({new Date(metric.points[0].interval_end).toLocaleString()})
							</span>
						</div>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.monitoring-container {
		padding: 1.5rem;
		border-radius: 1rem;
		background: var(--color-bg-card);
		backdrop-filter: blur(10px);
		border: 1px solid var(--color-border);
		box-shadow: var(--shadow-md);
	}

	h3 {
		margin: 0 0 1.5rem 0;
		color: var(--color-accent);
	}

	.metrics-grid {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		max-height: 500px;
		overflow-y: auto;
	}

	.metric-card {
		padding: 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.8rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.metric-card:hover {
		border-color: var(--color-accent);
	}

	.metric-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.metric-kind {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.95rem;
	}

	.badge {
		padding: 0.2rem 0.6rem;
		border-radius: 1rem;
		font-size: 0.65rem;
		font-weight: 700;
		background: rgba(52, 168, 83, 0.15);
		color: #34a853;
	}

	.labels-container {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin-bottom: 0.8rem;
	}

	.label-chip {
		background: var(--color-bg-tertiary);
		padding: 0.2rem 0.5rem;
		border-radius: 0.4rem;
		font-size: 0.7rem;
		border: 1px solid var(--color-border-subtle);
		display: flex;
		align-items: center;
	}

	.label-key {
		color: var(--color-text-muted);
		margin-right: 0.3rem;
	}

	.label-value {
		color: var(--color-text-primary);
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.points-summary {
		font-size: 0.85rem;
		color: var(--color-text-primary);
		background: rgba(66, 133, 244, 0.05);
		padding: 0.6rem;
		border-radius: 0.5rem;
		border-left: 3px solid #4285f4;
	}

	.points-summary strong {
		color: #4285f4;
		font-size: 1rem;
	}

	.time-hint {
		color: var(--color-text-muted);
		font-size: 0.75rem;
		margin-left: 0.5rem;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
