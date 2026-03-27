<script lang="ts">
	interface Quota {
		name?: string;
		quota_id?: string;
		metric?: string;
		is_precise?: boolean;
		container_type?: string;
	}

	interface Props {
		quotas: Quota[];
	}

	let { quotas = [] }: Props = $props();
</script>

<div class="quotas-container glass">
	<h3>Quotas</h3>
	<div class="quotas-grid">
		{#if quotas.length === 0}
			<p class="empty">조회된 할당량(Quota) 데이터가 없습니다.</p>
		{:else}
			{#each quotas as quota}
				<div class="quota-card">
					<div class="quota-header">
						<span class="quota-title">{quota.quota_id || quota.name || 'Unknown Quota'}</span>
						<span class="badge">{quota.container_type || 'Unknown Type'}</span>
					</div>
					<div class="quota-details">
						<span class="metric" title={quota.metric}>{quota.metric}</span>
						{#if quota.is_precise !== undefined}
							<span class="precise-badge" class:precise={quota.is_precise}>
								{quota.is_precise ? 'Precise' : 'Imprecise'}
							</span>
						{/if}
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.quotas-container {
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

	.quotas-grid {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		max-height: 500px;
		overflow-y: auto;
	}

	.quota-card {
		padding: 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.8rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.quota-card:hover {
		border-color: var(--color-accent);
	}

	.quota-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.quota-title {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.95rem;
	}

	.badge {
		padding: 0.2rem 0.6rem;
		border-radius: 1rem;
		font-size: 0.65rem;
		font-weight: 700;
		background: rgba(66, 133, 244, 0.15);
		color: #4285f4;
	}

	.quota-details {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 0.5rem;
	}

	.metric {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		font-family: 'SF Mono', 'Fira Code', monospace;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 70%;
	}

	.precise-badge {
		padding: 0.1rem 0.5rem;
		border-radius: 1rem;
		font-size: 0.65rem;
		font-weight: 600;
		background: rgba(251, 188, 4, 0.15);
		color: #fbbc04;
	}
	.precise-badge.precise {
		background: rgba(52, 168, 83, 0.15);
		color: #34a853;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
