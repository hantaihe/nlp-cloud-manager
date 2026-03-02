<script lang="ts">
	export let freeTierUsage: any[] = [];

	function formatUsage(usage: any) {
		const actual = Number(usage.actualUsageAmount || 0);
		const limit = Number(usage.freeTierUsageLimit || 0);
		const unit = usage.unit || '';
		return `${actual.toFixed(2)} / ${limit.toFixed(2)} ${unit}`;
	}

	function getProgress(usage: any) {
		const actual = Number(usage.actualUsageAmount || 0);
		const limit = Number(usage.freeTierUsageLimit || 0);
		return Math.min((actual / limit) * 100, 100);
	}

	function getProgressColor(usage: any) {
		const progress = getProgress(usage);
		if (progress > 90) return 'var(--color-danger)';
		if (progress > 70) return 'var(--color-warning)';
		return 'var(--color-success)';
	}
</script>

<div class="freetier-container glass">
	<h3>Free Tier Usage</h3>
	<div class="usage-grid">
		{#if freeTierUsage.length === 0}
			<p class="empty">Free Tier 사용 데이터가 없습니다.</p>
		{:else}
			{#each freeTierUsage as usage}
				<div class="usage-item">
					<div class="service-name">{usage.service || 'Unknown'}</div>
					<div class="usage-info">
						<span class="usage-text">{formatUsage(usage)}</span>
						<span class="operation">{usage.operation || ''}</span>
					</div>
					<div class="progress-bar">
						<div
							class="progress-fill"
							style="width: {getProgress(usage)}%; background: {getProgressColor(usage)}"
						></div>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.freetier-container {
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

	.usage-grid {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.service-name {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.usage-info {
		display: flex;
		justify-content: space-between;
		font-size: 0.8rem;
		color: var(--color-text-secondary);
		margin-bottom: 0.3rem;
	}

	.progress-bar {
		height: 0.5rem;
		background: var(--color-bg-tertiary);
		border-radius: 0.25rem;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		border-radius: 0.25rem;
		transition: width 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
