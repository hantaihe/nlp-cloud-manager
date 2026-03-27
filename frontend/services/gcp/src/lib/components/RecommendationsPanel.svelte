<script lang="ts">
	interface Recommendation {
		name: string;
		description: string;
		impact: number;
		category: string;
		last_refresh_time?: string;
	}

	interface Props {
		recommendations?: Recommendation[];
	}

	let { recommendations = [] }: Props = $props();

	function impactColor(impact: number): string {
		if (impact >= 50) return 'var(--color-danger)';
		if (impact >= 10) return 'var(--color-warning)';
		return 'var(--color-success)';
	}

	function formatDate(ts?: string): string {
		if (!ts) return '';
		const d = new Date(ts);
		return d.toLocaleDateString();
	}
</script>

<div class="panel glass">
	<div class="panel-header">
		<h2>Cost Recommendations</h2>
		<span class="count-badge">{recommendations.length}</span>
	</div>

	{#if recommendations.length === 0}
		<div class="empty-state">
			<span class="empty-icon">✓</span>
			<p>No recommendations at this time.</p>
		</div>
	{:else}
		<ul class="rec-list">
			{#each recommendations as rec}
				<li class="rec-item">
					<div class="rec-main">
						<span class="rec-desc">{rec.description}</span>
						<div class="rec-meta">
							<span class="rec-category">{rec.category}</span>
							{#if rec.last_refresh_time}
								<span class="rec-date">{formatDate(rec.last_refresh_time)}</span>
							{/if}
						</div>
					</div>
					{#if rec.impact}
						<span class="rec-impact" style="color: {impactColor(rec.impact)}">
							~${rec.impact}/mo
						</span>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.panel {
		background: var(--color-bg-card, rgba(255, 255, 255, 0.04));
		border: 1px solid var(--color-border-subtle);
		border-radius: 1.2rem;
		padding: 1.5rem;
	}

	.panel-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.2rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 700;
		color: var(--color-text-primary);
		margin: 0;
	}

	.count-badge {
		background: rgba(66, 133, 244, 0.15);
		color: #4285f4;
		font-size: 0.75rem;
		font-weight: 700;
		padding: 0.15rem 0.6rem;
		border-radius: 999px;
	}

	.empty-state {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-muted);
		font-size: 0.9rem;
	}

	.empty-icon {
		font-size: 2rem;
		display: block;
		margin-bottom: 0.5rem;
		color: var(--color-success);
	}

	.empty-state p { margin: 0; }

	.rec-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.rec-item {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		padding: 0.9rem 1rem;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border-subtle);
		border-radius: 0.75rem;
	}

	.rec-main {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		min-width: 0;
	}

	.rec-desc {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--color-text-primary);
		line-height: 1.4;
	}

	.rec-meta {
		display: flex;
		gap: 0.6rem;
		align-items: center;
	}

	.rec-category {
		font-size: 0.72rem;
		font-weight: 600;
		color: #4285f4;
		background: rgba(66, 133, 244, 0.1);
		padding: 0.1rem 0.5rem;
		border-radius: 0.4rem;
	}

	.rec-date {
		font-size: 0.72rem;
		color: var(--color-text-muted);
	}

	.rec-impact {
		font-size: 0.85rem;
		font-weight: 700;
		white-space: nowrap;
		flex-shrink: 0;
	}
</style>
