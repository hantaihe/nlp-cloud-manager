<script lang="ts">
	interface Constraint {
		name?: string;
		display_name?: string;
		description?: string;
		constraint_default?: string;
	}

	let { constraints = [] }: { constraints: Constraint[] } = $props();
</script>

<div class="gov-container glass">
	<h3>Governance Constraints</h3>
	<div class="gov-grid">
		{#if constraints.length === 0}
			<p class="empty">조회된 조직 정책 제약 조건(Governance)이 없습니다.</p>
		{:else}
			{#each constraints as constraint}
				<div class="gov-card">
					<div class="gov-header">
						<span class="gov-title" title={constraint.display_name}>{constraint.display_name || constraint.name || 'Unknown Constraint'}</span>
						{#if constraint.constraint_default}
							<span class="badge" class:allow={constraint.constraint_default === 'ALLOW'} class:deny={constraint.constraint_default === 'DENY'}>
								{constraint.constraint_default}
							</span>
						{/if}
					</div>
					<div class="gov-name" title={constraint.name}>{constraint.name}</div>
					{#if constraint.description}
						<div class="gov-desc">{constraint.description}</div>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.gov-container {
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

	.gov-grid {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		max-height: 500px;
		overflow-y: auto;
	}

	.gov-card {
		padding: 1.2rem;
		background: var(--color-bg-secondary);
		border-radius: 0.8rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.gov-card:hover {
		border-color: var(--color-accent);
	}

	.gov-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.5rem;
	}

	.gov-title {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.95rem;
		flex-grow: 1;
		margin-right: 1rem;
		line-height: 1.3;
	}

	.badge {
		padding: 0.2rem 0.6rem;
		border-radius: 1rem;
		font-size: 0.65rem;
		font-weight: 700;
		white-space: nowrap;
		background: rgba(158, 158, 158, 0.15);
		color: #9e9e9e;
	}

	.badge.allow {
		background: rgba(52, 168, 83, 0.15);
		color: #34a853;
	}

	.badge.deny {
		background: rgba(234, 67, 53, 0.15);
		color: #ea4335;
	}

	.gov-name {
		font-size: 0.75rem;
		color: #4285f4;
		font-family: 'SF Mono', 'Fira Code', monospace;
		margin-bottom: 0.8rem;
		word-break: break-all;
	}

	.gov-desc {
		font-size: 0.85rem;
		color: var(--color-text-subtle);
		line-height: 1.5;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
