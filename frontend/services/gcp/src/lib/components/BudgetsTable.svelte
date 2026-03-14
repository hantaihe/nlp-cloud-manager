<script lang="ts">
	interface Budget {
		display_name?: string;
		name?: string;
		amount?: {
			specified_amount?: {
				units: number;
				currency_code: string;
			};
		};
		threshold_rules?: Array<{
			threshold_percent: number;
		}>;
	}

	let { budgets = [] }: { budgets: Budget[] } = $props();

	function formatCurrency(amount: any) {
		const units = Number(amount?.units || 0);
		const code = amount?.currency_code || 'USD';
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: code
		}).format(units);
	}
</script>

<div class="budgets-container glass">
	<h3>📊 Budgets</h3>
	<table>
		<thead>
			<tr>
				<th>Name</th>
				<th>Amount</th>
				<th>Thresholds</th>
			</tr>
		</thead>
		<tbody>
			{#if budgets.length === 0}
				<tr>
					<td colspan="3" class="empty">Budget을 찾을 수 없습니다.</td>
				</tr>
			{:else}
				{#each budgets as budget}
					<tr>
						<td class="name">{budget.display_name}</td>
						<td class="amount">
							{#if budget.amount?.specified_amount}
								{formatCurrency(budget.amount.specified_amount)}
							{:else if budget.amount?.last_period_amount}
								<span class="badge">Last Period</span>
							{:else}
								-
							{/if}
						</td>
						<td>
							<div class="thresholds">
								{#each budget.threshold_rules || [] as rule}
									<span class="threshold-pill">
										{(rule.threshold_percent * 100).toFixed(0)}%
										<span class="basis">{rule.spend_basis}</span>
									</span>
								{/each}
							</div>
						</td>
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>

<style>
	.budgets-container {
		padding: 1.5rem;
		border-radius: 1rem;
		background: var(--color-bg-card);
		backdrop-filter: blur(10px);
		border: 1px solid var(--color-border);
		box-shadow: var(--shadow-md);
	}

	h3 {
		margin: 0 0 1rem 0;
		color: var(--color-accent);
	}

	table {
		width: 100%;
		border-collapse: collapse;
		color: var(--color-text-secondary);
	}

	th {
		text-align: left;
		padding: 0.8rem;
		border-bottom: 1px solid var(--color-border);
		font-size: 0.8rem;
		text-transform: uppercase;
		color: var(--color-text-muted);
	}

	td {
		padding: 1rem 0.8rem;
		border-bottom: 1px solid var(--color-border-subtle);
	}

	.name {
		font-weight: 600;
		color: var(--color-text-primary);
	}

	.amount {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-weight: 600;
		color: #34a853;
	}

	.badge {
		background: rgba(66, 133, 244, 0.15);
		color: #4285f4;
		padding: 0.15rem 0.5rem;
		border-radius: 0.4rem;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.thresholds {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.threshold-pill {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.15rem 0.5rem;
		border-radius: 1rem;
		font-size: 0.7rem;
		font-weight: 600;
		background: rgba(251, 188, 4, 0.15);
		color: #fbbc04;
	}

	.basis {
		font-size: 0.6rem;
		opacity: 0.7;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
