<script lang="ts">
	interface Asset {
		asset_type?: string;
		name?: string;
		update_time?: string;
	}

	let { assets = [] }: { assets: Asset[] } = $props();

	function getAssetIcon(type: string) {
		if (type?.includes('compute')) return '🖥️';
		if (type?.includes('storage')) return '💾';
		if (type?.includes('sql') || type?.includes('database')) return '🗄️';
		if (type?.includes('network') || type?.includes('firewall')) return '🌐';
		if (type?.includes('iam') || type?.includes('serviceAccount')) return '🔐';
		if (type?.includes('pubsub')) return '📨';
		if (type?.includes('function')) return '⚡';
		if (type?.includes('cluster') || type?.includes('container')) return '🐳';
		return '📦';
	}

	function getShortType(type: string) {
		const parts = type?.split('/') || [];
		return parts[parts.length - 1] || type;
	}

	function getShortName(name: string) {
		const parts = name?.split('/') || [];
		return parts[parts.length - 1] || name;
	}
</script>

<div class="assets-container glass">
	<h3>🗂️ Asset Inventory</h3>
	<div class="asset-count">
		<span class="count">{assets.length}</span> resources found
	</div>

	<div class="assets-grid">
		{#if assets.length === 0}
			<p class="empty">리소스를 찾을 수 없습니다.</p>
		{:else}
			{#each assets as asset}
				<div class="asset-card">
					<div class="asset-icon">{getAssetIcon(asset.asset_type)}</div>
					<div class="asset-info">
						<span class="asset-name">{getShortName(asset.name)}</span>
						<span class="asset-type">{getShortType(asset.asset_type)}</span>
					</div>
					<span class="update-time">
						{asset.update_time ? new Date(asset.update_time).toLocaleDateString() : ''}
					</span>
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.assets-container {
		padding: 1.5rem;
		border-radius: 1rem;
		background: var(--color-bg-card);
		backdrop-filter: blur(10px);
		border: 1px solid var(--color-border);
		box-shadow: var(--shadow-md);
	}

	h3 {
		margin: 0 0 0.5rem 0;
		color: var(--color-accent);
	}

	.asset-count {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		margin-bottom: 1.5rem;
	}

	.count {
		font-weight: 700;
		color: #4285f4;
		font-size: 1rem;
	}

	.assets-grid {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-height: 400px;
		overflow-y: auto;
	}

	.asset-card {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.7rem 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.6rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.asset-card:hover {
		border-color: var(--color-accent);
		transform: translateX(4px);
	}

	.asset-icon {
		font-size: 1.4rem;
		flex-shrink: 0;
	}

	.asset-info {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 0;
	}

	.asset-name {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 0.85rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.asset-type {
		font-size: 0.7rem;
		color: var(--color-text-muted);
	}

	.update-time {
		font-size: 0.7rem;
		color: var(--color-text-subtle);
		flex-shrink: 0;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
