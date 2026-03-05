<script lang="ts">
	import { onMount } from 'svelte';
	import FilterPanel from './FilterPanel.svelte';
	import CostSummary from './CostSummary.svelte';
	import BudgetsTable from './BudgetsTable.svelte';
	import FreeTierStatus from './FreeTierStatus.svelte';
	import CredentialsManager from './CredentialsManager.svelte';

	let summaryData: any = null;
	let loading = true;
	let error: string | null = null;
	let filters = {
		start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
		end: new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate() + 1)
			.toISOString()
			.split('T')[0],
		granularity: 'MONTHLY' as 'DAILY' | 'MONTHLY' | 'HOURLY',
		groupBy: [] as string[]
	};

	async function fetchSummary() {
		loading = true;
		error = null;

		const activeName = localStorage.getItem('azure_active_name') || '';

		try {
			const summaryRes = await fetch(`http://localhost:8001/billing?name=${activeName}`);
			if (!summaryRes.ok) {
				const errData = await summaryRes.json();
				throw new Error(errData.detail || 'Azure 정보를 불러오기 실패');
			}
			const summary = await summaryRes.json();

			const queryParams = new URLSearchParams({
				name: activeName,
				start: filters.start,
				end: filters.end,
				granularity: filters.granularity
			});

			filters.groupBy.forEach((dim) => queryParams.append('group_by_dimension', dim));

			const costRes = await fetch(`http://localhost:8001/consumption?${queryParams.toString()}`);
			if (!costRes.ok) throw new Error('Azure 정보를 가져오기 실패');
			const costData = await costRes.json();

			summaryData = {
				...summary,
				currentMonthCost: costData.ResultsByTime || costData.currentMonthCost || []
			};
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function handleApplyFilters(newFilters: any) {
		filters = { ...newFilters };
		fetchSummary();
	}

	onMount(() => {
		fetchSummary();
	});
</script>

<div class="dashboard">
	<header>
		<h1>Azure Billing</h1>
		<div class="header-actions">
			<CredentialsManager />
			<button on:click={fetchSummary} class="refresh-btn"> Refresh </button>
		</div>
	</header>

	<FilterPanel {filters} onApply={handleApplyFilters} />

	{#if loading}
		<div class="loader">
			<div class="spinner"></div>
			<p>Fetching Azure Data...</p>
		</div>
	{:else if error}
		<div class="error-card glass">
			<p>⚠️ {error}</p>
			<button on:click={fetchSummary}>재시도</button>
		</div>
	{:else}
		<div class="grid">
			<div class="span-all">
				<CostSummary costData={summaryData.currentMonthCost} />
			</div>

			<div class="column">
				<BudgetsTable budgets={summaryData.budgets || []} />
			</div>

			<div class="column">
				<FreeTierStatus freeTierUsage={summaryData.freeTierUsage || []} />
			</div>
		</div>
	{/if}
</div>

<style>
	.dashboard {
		padding: 2rem;
		max-width: 1200px;
		margin: 0 auto;
		color: var(--color-text-primary);
		font-family: 'Inter', sans-serif;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid var(--color-border-subtle);
	}

	.header-actions {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	h1 {
		font-size: 2.5rem;
		font-weight: 900;
		letter-spacing: -1px;
		background: linear-gradient(135deg, var(--color-text-primary) 0%, var(--color-text-muted) 100%);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		margin: 0;
	}

	.refresh-btn {
		background: var(--color-accent);
		border: none;
		color: #fff;
		padding: 0.6rem 1.4rem;
		border-radius: 0.8rem;
		cursor: pointer;
		font-weight: 700;
		font-size: 0.9rem;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: var(--shadow-sm);
	}

	.refresh-btn:hover {
		background: var(--color-accent-hover);
		transform: translateY(-2px);
		box-shadow: var(--shadow-md);
	}

	.grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
	}

	.span-all {
		grid-column: 1 / -1;
	}

	.loader {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 5rem;
		color: var(--color-text-muted);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid var(--color-border-subtle);
		border-top: 4px solid var(--color-accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 1rem;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	.error-card {
		padding: 3rem;
		text-align: center;
		color: #ff4d4d;
		background: rgba(255, 77, 77, 0.05);
	}

	.error-card button {
		margin-top: 1rem;
		background: #ff4d4d;
		color: #fff;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 0.5rem;
		cursor: pointer;
	}

	.column {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	@media (max-width: 900px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
