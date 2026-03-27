<script lang="ts">
	import { onMount } from 'svelte';
	import FilterPanel from './FilterPanel.svelte';
	import BillingAccounts from './BillingAccounts.svelte';
	import BudgetsTable from './BudgetsTable.svelte';
	import AssetsPanel from './AssetsPanel.svelte';
	import ServicesPanel from './ServicesPanel.svelte';
	import CredentialsManager from './CredentialsManager.svelte';
	import CostSummary from './CostSummary.svelte';
	import QuotasPanel from './QuotasPanel.svelte';
	import GovernancePanel from './GovernancePanel.svelte';
	import MonitoringPanel from './MonitoringPanel.svelte';
	import LoggingPanel from './LoggingPanel.svelte';
	import RecommendationsPanel from './RecommendationsPanel.svelte';

	const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8002';

	let loading = $state(true);
	let error: string | null = $state(null);

	let billingAccounts: any[] = $state([]);
	let budgets: any[] = $state([]);
	let assets: any[] = $state([]);
	let services: any[] = $state([]);
	let summary: any = $state({});
	let recommendations: any[] = $state([]);

	let filters = $state({
		billingAccountId: '' as string,
		start: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
			.toISOString()
			.split('T')[0] as string,
		end: new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate() + 1)
			.toISOString()
			.split('T')[0] as string,
		activeTab: 'billing' as string,
		zone: 'us-central1-a' as string,
		insightType: 'google.compute.instance.IdleResourceInsight' as string
	});

	function getActiveName() {
		return localStorage.getItem('gcp_active_name') || '';
	}

	async function fetchData() {
		loading = true;
		error = null;
		const name = getActiveName();

		try {
			switch (filters.activeTab) {
				case 'billing':
					await fetchBillingData(name);
					break;
				case 'assets':
					await fetchAssetsData(name);
					break;
				case 'quotas':
					await fetchQuotasData(name);
					break;
				case 'governance':
					await fetchGovernanceData(name);
					break;
				case 'monitoring':
					await fetchMonitoringData(name);
					break;
				case 'logging':
					await fetchLoggingData(name);
					break;
			case 'recommendations':
					await fetchRecommendationsData(name);
					break;
			}
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function fetchBillingData(name: string) {
		const [accountsRes, budgetsRes, summaryRes] = await Promise.allSettled([
			fetch(`${API_BASE}/billing/accounts?name=${name}`),
			filters.billingAccountId
				? fetch(
						`${API_BASE}/billing/budgets?billing_account_id=${filters.billingAccountId}&name=${name}`
					)
				: Promise.resolve(null),
			fetch(
				`${API_BASE}/billing/summary?billing_account_id=${filters.billingAccountId}&name=${name}`
			)
		]);

		if (accountsRes.status === 'fulfilled') {
			if (!accountsRes.value.ok) {
				const errorData = await accountsRes.value.json();
				throw new Error(errorData.detail || 'Failed to fetch billing accounts');
			}
			const data = await accountsRes.value.json();
			billingAccounts = data.billing_accounts || [];
		}

		if (budgetsRes.status === 'fulfilled' && budgetsRes.value instanceof Response) {
			if (!budgetsRes.value.ok) {
				const errorData = await budgetsRes.value.json();
				throw new Error(errorData.detail || 'Failed to fetch budgets');
			}
			const data = await budgetsRes.value.json();
			budgets = data.budgets || [];
		}

		if (summaryRes.status === 'fulfilled') {
			if (!summaryRes.value.ok) {
				const errorData = await summaryRes.value.json();
				throw new Error(errorData.detail || 'Failed to fetch billing summary');
			}
			const data = await summaryRes.value.json();
			summary = data.summary || {};
		}
	}

	async function fetchAssetsData(name: string) {
		const res = await fetch(`${API_BASE}/assets?name=${name}`);
		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.detail || 'Failed to fetch assets');
		}
		const data = await res.json();
		assets = data.assets || [];
	}

	async function fetchGovernanceData(name: string) {
		const res = await fetch(`${API_BASE}/org-policy/constraints?name=${name}`);
		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.detail || 'Failed to fetch governance constraints');
		}
		const data = await res.json();
		services = data.constraints || [];
	}

	async function fetchQuotasData(name: string) {
		const res = await fetch(`${API_BASE}/quotas?name=${name}`);
		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.detail || 'Failed to fetch quotas');
		}
		const data = await res.json();
		services = data.quota_infos || [];
	}

	async function fetchMonitoringData(name: string) {
		const res = await fetch(`${API_BASE}/monitoring/metrics?name=${name}`);
		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.detail || 'Failed to fetch monitoring');
		}
		const data = await res.json();
		services = data.time_series || [];
	}

	async function fetchLoggingData(name: string) {
		const res = await fetch(`${API_BASE}/logging/entries?name=${name}`);
		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.detail || 'Failed to fetch logging entries');
		}
		const data = await res.json();
		services = data.entries || [];
	}

	async function fetchRecommendationsData(name: string) {
		const res = await fetch(`${API_BASE}/recommendations?name=${name}`);
		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.detail || 'Failed to fetch recommendations');
		}
		const data = await res.json();
		recommendations = data.recommendations || [];
	}

	function handleApplyFilters(newFilters: any) {
		filters = { ...newFilters };
		fetchData();
	}

	onMount(() => {
		fetchData();
	});
</script>

<div class="dashboard">
	<header>
		<h1>GCP Billing</h1>
		<div class="header-actions">
			<CredentialsManager />
			<button onclick={fetchData} class="refresh-btn">Refresh</button>
		</div>
	</header>

	<FilterPanel {filters} onApply={handleApplyFilters} />

	{#if loading}
		<div class="loader">
			<div class="spinner"></div>
			<p>Fetching GCP Data...</p>
		</div>
	{:else if error}
		<div class="error-card glass">
			<p>Error: {error}</p>
			<button onclick={fetchData}>재시도</button>
		</div>
	{:else}
		<div class="grid">
			{#if filters.activeTab === 'billing'}
				<div class="span-all">
					<CostSummary {summary} />
				</div>
				<div class="span-all">
					<BillingAccounts accounts={billingAccounts} />
				</div>
				<div class="span-all">
					<BudgetsTable {budgets} />
				</div>
			{:else if filters.activeTab === 'assets'}
				<div class="span-all">
					<AssetsPanel {assets} />
				</div>
			{:else if filters.activeTab === 'governance'}
				<div class="span-all">
					<GovernancePanel constraints={services} />
				</div>
			{:else if filters.activeTab === 'quotas'}
				<div class="span-all">
					<QuotasPanel quotas={services} />
				</div>
			{:else if filters.activeTab === 'monitoring'}
				<div class="span-all">
					<MonitoringPanel metrics={services} />
				</div>
			{:else if filters.activeTab === 'logging'}
				<div class="span-all">
					<LoggingPanel logs={services} />
				</div>
			{:else if filters.activeTab === 'recommendations'}
				<div class="span-all">
					<RecommendationsPanel {recommendations} />
				</div>
			{/if}
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
		background: linear-gradient(135deg, #4285f4 0%, #34a853 50%, #fbbc04 100%);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		margin: 0;
	}

	.refresh-btn {
		background: #4285f4;
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
		background: #3367d6;
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
		border-top: 4px solid #4285f4;
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
		color: #ea4335;
		background: rgba(234, 67, 53, 0.05);
		border-radius: 1rem;
	}

	.error-card button {
		margin-top: 1rem;
		background: #ea4335;
		color: #fff;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 0.5rem;
		cursor: pointer;
	}

	@media (max-width: 900px) {
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
