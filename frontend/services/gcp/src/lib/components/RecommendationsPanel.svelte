<script lang="ts">
	interface Recommendation {
		recommender_subtype?: string;
		priority?: string;
		description?: string;
		primary_impact?: {
			cost_projection?: {
				cost?: {
					units?: number;
					nanos?: number;
					currency_code?: string;
				};
			};
		};
	}

	interface Insight {
		category?: string;
		severity?: string;
		description?: string;
	}

	let {
		recommendations = [],
		insights = []
	}: { recommendations: Recommendation[]; insights: Insight[] } = $props();
</script>

<div class="rec-container glass">
	<h3>🎯 Cost Recommendations</h3>

	{#if recommendations.length === 0 && insights.length === 0}
		<p class="empty">추천 사항이 없습니다.</p>
	{:else}
		{#if recommendations.length > 0}
			<div class="section">
				<h4>Recommendations</h4>
				{#each recommendations as rec}
					<div class="rec-card">
						<div class="rec-header">
							<span class="rec-subtype">{rec.recommender_subtype || 'Unknown'}</span>
							<span class="priority-badge priority-{rec.priority?.toLowerCase() || 'low'}">
								{rec.priority || 'LOW'}
							</span>
						</div>
						<p class="rec-desc">{rec.description || 'No description'}</p>
						{#if rec.primary_impact?.cost_projection?.cost}
							<div class="cost-impact">
								<span class="cost-label">예상 절감</span>
								<span class="cost-value">
									{new Intl.NumberFormat('en-US', {
										style: 'currency',
										currency: rec.primary_impact.cost_projection.cost.currency_code || 'USD'
									}).format(
										Math.abs(
											Number(rec.primary_impact.cost_projection.cost.units || 0) +
												Number(rec.primary_impact.cost_projection.cost.nanos || 0) / 1e9
										)
									)}
								</span>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}

		{#if insights.length > 0}
			<div class="section">
				<h4>Insights</h4>
				{#each insights as insight}
					<div class="rec-card">
						<div class="rec-header">
							<span class="rec-subtype">{insight.category || 'Unknown'}</span>
							<span class="severity-badge severity-{insight.severity?.toLowerCase() || 'low'}">
								{insight.severity || 'LOW'}
							</span>
						</div>
						<p class="rec-desc">{insight.description || 'No description'}</p>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.rec-container {
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

	h4 {
		margin: 0 0 1rem 0;
		color: var(--color-text-secondary);
		font-size: 0.9rem;
	}

	.section {
		margin-bottom: 1.5rem;
	}

	.section:last-child {
		margin-bottom: 0;
	}

	.rec-card {
		padding: 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.8rem;
		margin-bottom: 0.8rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.rec-card:hover {
		border-color: var(--color-accent);
		transform: translateX(4px);
	}

	.rec-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.rec-subtype {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.85rem;
	}

	.priority-badge,
	.severity-badge {
		padding: 0.1rem 0.5rem;
		border-radius: 1rem;
		font-size: 0.65rem;
		font-weight: 700;
		text-transform: uppercase;
	}

	.priority-high,
	.severity-critical {
		background: rgba(234, 67, 53, 0.15);
		color: #ea4335;
	}

	.priority-medium,
	.severity-high {
		background: rgba(251, 188, 4, 0.15);
		color: #fbbc04;
	}

	.priority-low,
	.severity-low {
		background: rgba(52, 168, 83, 0.15);
		color: #34a853;
	}

	.rec-desc {
		margin: 0;
		font-size: 0.85rem;
		color: var(--color-text-secondary);
		line-height: 1.5;
	}

	.cost-impact {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 0.8rem;
		padding-top: 0.6rem;
		border-top: 1px solid var(--color-border-subtle);
	}

	.cost-label {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		text-transform: uppercase;
	}

	.cost-value {
		font-weight: 700;
		color: #34a853;
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
