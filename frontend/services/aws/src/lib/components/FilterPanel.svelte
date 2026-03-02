<script lang="ts">
	let {
		filters = $bindable({
			start: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
				.toISOString()
				.split('T')[0],
			end: new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate() + 1)
				.toISOString()
				.split('T')[0],
			granularity: 'MONTHLY' as 'DAILY' | 'MONTHLY' | 'HOURLY',
			groupBy: [] as string[]
		}),
		onApply
	}: { filters?: any; onApply: (filters: any) => void } = $props();

	const dimensions = [
		{ id: 'SERVICE', label: 'Service' },
		{ id: 'REGION', label: 'Region' },
		{ id: 'AZ', label: 'Availability Zone' },
		{ id: 'INSTANCE_TYPE', label: 'Instance Type' },
		{ id: 'LINKED_ACCOUNT', label: 'Linked Account' },
		{ id: 'OPERATION', label: 'Operation' },
		{ id: 'USAGE_TYPE', label: 'Usage Type' }
	];

	const granularities = ['DAILY', 'MONTHLY', 'HOURLY'];

	function toggleGroupBy(dimId: string) {
		if (filters.groupBy.includes(dimId)) {
			filters.groupBy = filters.groupBy.filter((id: string) => id !== dimId);
		} else {
			filters.groupBy = [...filters.groupBy, dimId];
		}
	}

	function handleApply() {
		onApply(filters);
	}
</script>

<div class="filter-panel glass">
	<div class="filter-section">
		<label>Time Period</label>
		<div class="date-inputs">
			<input type="date" bind:value={filters.start} />
			<span>to</span>
			<input type="date" bind:value={filters.end} />
		</div>
	</div>

	<div class="filter-section">
		<label>Granularity</label>
		<div class="options">
			{#each granularities as g}
				<button
					class:active={filters.granularity === g}
					on:click={() => (filters.granularity = g as any)}
				>
					{g}
				</button>
			{/each}
		</div>
	</div>

	<div class="filter-section">
		<label>Group By</label>
		<div class="tags">
			{#each dimensions as dim}
				<button
					class="tag"
					class:active={filters.groupBy.includes(dim.id)}
					on:click={() => toggleGroupBy(dim.id)}
				>
					{dim.label}
				</button>
			{/each}
		</div>
	</div>

	<div class="actions">
		<button class="apply-btn" on:click={handleApply}>필터 적용</button>
	</div>
</div>

<style>
	.filter-panel {
		padding: 1.5rem;
		border-radius: 1.2rem;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		margin-bottom: 2rem;
		border: 1px solid var(--color-border-subtle);
	}

	.glass {
		background: rgba(255, 255, 255, 0.05);
		backdrop-filter: blur(10px);
	}

	.filter-section {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	label {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.date-inputs {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	input[type='date'] {
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		color: var(--color-text-primary);
		padding: 0.4rem 0.8rem;
		border-radius: 0.6rem;
		font-size: 0.9rem;
		outline: none;
	}

	.options,
	.tags {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	button {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border-subtle);
		color: var(--color-text-secondary);
		padding: 0.4rem 0.8rem;
		border-radius: 0.6rem;
		cursor: pointer;
		font-size: 0.85rem;
		transition: all 0.2s;
	}

	button:hover {
		background: var(--color-bg-hover);
	}

	button.active {
		background: var(--color-accent);
		color: #fff;
		border-color: var(--color-accent);
		font-weight: 600;
	}

	.tag.active {
		background: var(--color-accent-subtle);
		color: var(--color-accent);
		border-color: var(--color-accent);
	}

	.actions {
		display: flex;
		justify-content: flex-end;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.apply-btn {
		background: #ffd700;
		color: #000;
		font-weight: 700;
		padding: 0.6rem 1.5rem;
		border-radius: 0.8rem;
	}

	.apply-btn:hover {
		background: #fff;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
	}
</style>
