<script lang="ts">
	export let budgets: any[] = [];

	function formatCurrency(amount: string | number) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(Number(amount));
	}

	function getStatusColor(budget: any) {
		const limit = Number(budget.BudgetLimit?.Amount);
		const actual = Number(budget.CalculatedSpend?.ActualSpend?.Amount);
		if (actual > limit) return 'var(--color-danger)';
		if (actual > limit * 0.8) return 'var(--color-warning)';
		return 'var(--color-success)';
	}
</script>

<div class="budgets-container glass">
	<h3>Alerts & Notifications</h3>
	<table>
		<thead>
			<tr>
				<th>메시지</th>
				<th>상태</th>
				<th>날짜</th>
			</tr>
		</thead>
		<tbody>
			{#if budgets.length === 0}
				<tr>
					<td colspan="3" class="empty">최근 알림이 없습니다.</td>
				</tr>
			{:else}
				{#each budgets as alert}
					<tr>
						<td class="name">{alert.message}</td>
						<td>
							<div
								class="status-pill"
								style="--status-color: {alert.severity === 'error'
									? 'var(--color-danger)'
									: 'var(--color-warning)'}"
							>
								{alert.severity}
							</div>
						</td>
						<td class="date">{alert.date}</td>
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

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}

	.status-pill {
		display: inline-block;
		padding: 0.2rem 0.6rem;
		border-radius: 1rem;
		font-size: 0.7rem;
		font-weight: 700;
		background: var(--status-color);
		color: #fff;
		text-transform: uppercase;
	}
</style>
