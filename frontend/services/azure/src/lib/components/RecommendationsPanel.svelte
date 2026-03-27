<script lang="ts">
	interface Recommendation {
		id: string;
		name: string;
		category: string;
		impact: string;
		risk: string;
		short_description: { problem: string; solution: string };
		resource_metadata?: Record<string, any>;
	}

	interface Props {
		name?: string;
	}

	let { name = '' }: Props = $props();

	let recommendations = $state<Recommendation[]>([]);
	let activeCategory = $state('All');
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function fetchRecommendations() {
		loading = true;
		error = null;
		try {
			const res = await fetch(`http://localhost:8001/advisor?name=${encodeURIComponent(name)}`);
			if (!res.ok) {
				const errData = await res.json().catch(() => ({}));
				throw new Error(errData.detail || `HTTP ${res.status}`);
			}
			const data = await res.json();
			recommendations = data.recommendations || [];
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		fetchRecommendations();
	});

	const categories = $derived([
		'All',
		...Array.from(new Set(recommendations.map((r) => r.category)))
	]);

	const filtered = $derived(
		activeCategory === 'All'
			? recommendations
			: recommendations.filter((r) => r.category === activeCategory)
	);

	function impactColor(impact: string): string {
		if (impact === 'High') return 'var(--color-danger)';
		if (impact === 'Medium') return 'var(--color-warning)';
		return 'var(--color-success)';
	}
</script>

<div class="panel glass">
	<div class="panel-header">
		<h2>Azure Advisor Recommendations</h2>
		<button onclick={fetchRecommendations} class="refresh-btn" disabled={loading}>
			{loading ? '...' : 'Refresh'}
		</button>
	</div>

	{#if !loading && !error && categories.length > 1}
		<div class="category-tabs">
			{#each categories as cat}
				<button class:active={activeCategory === cat} onclick={() => (activeCategory = cat)}>
					{cat}
				</button>
			{/each}
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<span>로딩 중...</span>
		</div>
	{:else if error}
		<div class="empty-state error">{error}</div>
	{:else if filtered.length === 0}
		<div class="empty-state">
			<span class="empty-icon">✓</span>
			<p>추천 사항이 없습니다.</p>
		</div>
	{:else}
		<ul class="rec-list">
			{#each filtered as rec}
				<li class="rec-item">
					<div class="rec-content">
						<div class="rec-top">
							<span class="rec-title">{rec.short_description?.problem || rec.name}</span>
							<span
								class="impact-badge"
								style="color: {impactColor(rec.impact)}; border-color: {impactColor(rec.impact)}"
							>
								{rec.impact}
							</span>
						</div>
						{#if rec.short_description?.solution}
							<p class="rec-solution">{rec.short_description.solution}</p>
						{/if}
						<div class="rec-footer">
							<span class="rec-category">{rec.category}</span>
							{#if rec.risk}
								<span class="rec-risk">{rec.risk}</span>
							{/if}
						</div>
					</div>
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
		margin-bottom: 1rem;
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
		border-color: #0078d4;
		color: #0078d4;
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.category-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin-bottom: 1rem;
	}

	.category-tabs button {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border-subtle);
		color: var(--color-text-secondary);
		padding: 0.3rem 0.75rem;
		border-radius: 0.5rem;
		cursor: pointer;
		font-size: 0.8rem;
		transition: all 0.2s;
	}

	.category-tabs button:hover {
		background: var(--color-bg-hover);
	}

	.category-tabs button.active {
		background: #0078d4;
		color: #fff;
		border-color: #0078d4;
		font-weight: 600;
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
		border-top-color: #0078d4;
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
		padding: 0.9rem 1rem;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border-subtle);
		border-radius: 0.75rem;
	}

	.rec-content {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.rec-top {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.rec-title {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--color-text-primary);
		line-height: 1.4;
	}

	.impact-badge {
		font-size: 0.75rem;
		font-weight: 700;
		padding: 0.15rem 0.6rem;
		border-radius: 999px;
		border: 1px solid;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.rec-solution {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		margin: 0;
		line-height: 1.5;
	}

	.rec-footer {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.rec-category {
		font-size: 0.72rem;
		color: #0078d4;
		font-weight: 600;
		background: rgba(0, 120, 212, 0.1);
		padding: 0.1rem 0.5rem;
		border-radius: 0.4rem;
	}

	.rec-risk {
		font-size: 0.72rem;
		color: var(--color-text-muted);
	}
</style>
