<script lang="ts">
	interface Filters {
		billingAccountId: string;
		start: string;
		end: string;
		activeTab: string;
	}

	interface Props {
		filters?: Filters;
		onApply: (filters: Filters) => void;
	}

	let {
		filters = $bindable({
			billingAccountId: '',
			start: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
				.toISOString()
				.split('T')[0],
			end: new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate() + 1)
				.toISOString()
				.split('T')[0],
			activeTab: 'billing'
		}),
		onApply
	}: Props = $props();

	const tabs = [
		{ id: 'billing', label: '💰 Billing', icon: '💰' },
		{ id: 'bigquery', label: '📊 BigQuery', icon: '📊' },
		{ id: 'recommender', label: '🎯 Recommender', icon: '🎯' },
		{ id: 'monitoring', label: '📈 Monitoring', icon: '📈' },
		{ id: 'assets', label: '🗂️ Assets', icon: '🗂️' },
		{ id: 'governance', label: '🏛️ Governance', icon: '🏛️' }
	];

	function handleApply() {
		onApply(filters);
	}
</script>

<div class="filter-panel glass">
	<div class="filter-section">
		<span class="label-text">Category</span>
		<div class="tabs">
			{#each tabs as tab}
				<button
					type="button"
					class:active={filters.activeTab === tab.id}
					onclick={() => (filters.activeTab = tab.id)}
				>
					{tab.label}
				</button>
			{/each}
		</div>
	</div>

	{#if filters.activeTab === 'billing'}
		<div class="filter-section">
			<label for="billing-account">Billing Account ID</label>
			<input
				id="billing-account"
				type="text"
				bind:value={filters.billingAccountId}
				placeholder="e.g. 01ABCD-EFGH12-345678"
			/>
		</div>
	{/if}

	<div class="filter-section">
		<label for="start-date">Time Period</label>
		<div class="date-inputs">
			<input id="start-date" type="date" bind:value={filters.start} aria-label="Start Date" />
			<span>to</span>
			<input id="end-date" type="date" bind:value={filters.end} aria-label="End Date" />
		</div>
	</div>

	<div class="actions">
		<button type="button" class="apply-btn" onclick={handleApply}>필터 적용</button>
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

	label,
	.label-text {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: block;
	}

	.date-inputs {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	input[type='date'],
	input[type='text'] {
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		color: var(--color-text-primary);
		padding: 0.4rem 0.8rem;
		border-radius: 0.6rem;
		font-size: 0.9rem;
		outline: none;
	}

	input:focus {
		border-color: var(--color-accent);
	}

	.tabs {
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
		background: #4285f4;
		color: #fff;
		border-color: #4285f4;
		font-weight: 600;
	}

	.actions {
		display: flex;
		justify-content: flex-end;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.apply-btn {
		background: #34a853;
		color: #fff;
		font-weight: 700;
		padding: 0.6rem 1.5rem;
		border-radius: 0.8rem;
	}

	.apply-btn:hover {
		background: #2d9249;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(52, 168, 83, 0.3);
	}
</style>
