<script lang="ts">
	interface Service {
		config?: {
			title?: string;
		};
		state?: string;
		name?: string;
	}

	let { services = [] }: { services: Service[] } = $props();
</script>

<div class="services-container glass">
	<h3>Active Services</h3>
	<div class="services-grid">
		{#if services.length === 0}
			<p class="empty">활성화된 서비스가 없습니다.</p>
		{:else}
			{#each services as svc}
				<div class="service-card">
					<div class="service-header">
						<span class="service-title">{svc.config?.title || svc.config?.name || 'Unknown'}</span>
						<span class="state-badge" class:enabled={svc.state === 'ENABLED'}>
							{svc.state}
						</span>
					</div>
					<span class="service-name">{svc.config?.name || ''}</span>
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.services-container {
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

	.services-grid {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-height: 400px;
		overflow-y: auto;
	}

	.service-card {
		padding: 0.8rem 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.6rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.service-card:hover {
		border-color: var(--color-accent);
	}

	.service-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.3rem;
	}

	.service-title {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.85rem;
	}

	.state-badge {
		padding: 0.1rem 0.5rem;
		border-radius: 1rem;
		font-size: 0.6rem;
		font-weight: 700;
		background: rgba(234, 67, 53, 0.15);
		color: #ea4335;
	}

	.state-badge.enabled {
		background: rgba(52, 168, 83, 0.15);
		color: #34a853;
	}

	.service-name {
		font-size: 0.7rem;
		color: var(--color-text-muted);
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
