<script lang="ts">
	interface Recommendation {
		actionType: string;
		recommendationLookbackPeriodInDays?: number;
		estimatedMonthlySavings?: string;
	}

	interface Props {
		name?: string;
	}

	let { name = '' }: Props = $props();

	let recommendations = $state<Recommendation[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function fetchRecommendations() {
		loading = true;
		error = null;
		try {
			const res = await fetch(
				`http://localhost:3002/billing/recommendations?name=${encodeURIComponent(name)}`
			);
			if (!res.ok) {
				const errData = await res.json().catch(() => ({}));
				throw new Error(errData.message || errData.detail || `HTTP ${res.status}`);
			}
			const data = await res.json();
			recommendations = data.items || [];
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		fetchRecommendations();
	});

	function impactColor(savings?: string): string {
		if (!savings) return 'var(--color-text-muted)';
		const val = parseFloat(savings.replace(/[^0-9.]/g, ''));
		if (val >= 100) return 'var(--color-danger)';
		if (val >= 20) return 'var(--color-warning)';
		return 'var(--color-success)';
	}
</script>

<div class="panel glass">
	<div class="panel-header">
		<h2>Cost Optimization Recommendations</h2>
		<button onclick={fetchRecommendations} class="refresh-btn" disabled={loading}>
			{loading ? '...' : 'Refresh'}
		</button>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<span>로딩 중...</span>
		</div>
	{:else if error}
		<div class="empty-state error">{error}</div>
	{:else if recommendations.length === 0}
		<div class="empty-state">
			<span class="empty-icon">✓</span>
			<p>추천 사항이 없습니다.</p>
		</div>
	{:else}
		<ul class="rec-list">
			{#each recommendations as rec}
				<li class="rec-item">
					<div class="rec-main">
						<span class="rec-action">{rec.actionType}</span>
						{#if rec.recommendationLookbackPeriodInDays}
							<span class="rec-meta">{rec.recommendationLookbackPeriodInDays}일 기준</span>
						{/if}
					</div>
					{#if rec.estimatedMonthlySavings}
						<span class="rec-savings" style="color: {impactColor(rec.estimatedMonthlySavings)}">
							~{rec.estimatedMonthlySavings}/월
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
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.2rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 700;
		color: var(--color-text-primary);
		margin: 0;
	}

	.refresh-btn {
		background: transparent;
		border: 1px solid var(--color-border);
		color: var(--color-text-muted);
		padding: 0.3rem 0.8rem;
		border-radius: 0.5rem;
		cursor: pointer;
		font-size: 0.8rem;
		transition: all 0.2s;
	}

	.refresh-btn:hover:not(:disabled) {
		border-color: #ff9900;
		color: #ff9900;
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.loading {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 1.5rem 0;
		color: var(--color-text-muted);
		font-size: 0.9rem;
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid var(--color-border);
		border-top-color: #ff9900;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		flex-shrink: 0;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
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

	.empty-state p {
		margin: 0;
	}

	.empty-state.error {
		color: var(--color-danger);
	}

	.rec-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.rec-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border-subtle);
		border-radius: 0.75rem;
		gap: 1rem;
	}

	.rec-main {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		min-width: 0;
	}

	.rec-action {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--color-text-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.rec-meta {
		font-size: 0.75rem;
		color: var(--color-text-muted);
	}

	.rec-savings {
		font-size: 0.85rem;
		font-weight: 700;
		white-space: nowrap;
		flex-shrink: 0;
	}
</style>
