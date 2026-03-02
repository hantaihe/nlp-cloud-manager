<script lang="ts">
	export let costData: any;

	function formatCurrency(amount: string | number) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(Number(amount));
	}

	$: currentCost = costData?.[0]?.Total?.UnblendedCost?.Amount || 0;
	$: startDate = costData?.[0]?.TimePeriod?.Start || '';
	$: endDate = costData?.[0]?.TimePeriod?.End || '';
</script>

<div class="cost-card glass">
	<h3>이번 달의 예상 비용</h3>
	<div class="amount">{formatCurrency(currentCost)}</div>
	<div class="period">
		<span>{startDate}</span> → <span>{endDate}</span>
	</div>
</div>

<style>
	.cost-card {
		padding: 2rem;
		border-radius: 1.5rem;
		background: var(--color-bg-card);
		backdrop-filter: blur(10px);
		border: 1px solid var(--color-border);
		box-shadow: var(--shadow-md);
		text-align: center;
		transition: transform 0.3s ease;
	}

	.cost-card:hover {
		transform: translateY(-5px);
		border-color: rgba(255, 255, 255, 0.2);
	}

	h3 {
		margin: 0;
		font-size: 1.2rem;
		color: var(--color-accent);
		text-transform: uppercase;
		letter-spacing: 0.1rem;
		opacity: 0.8;
	}

	.amount {
		font-size: 4rem;
		font-weight: 800;
		margin: 1.5rem 0;
		background: linear-gradient(135deg, var(--color-accent), var(--color-purple));
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
	}

	.period {
		font-size: 0.9rem;
		color: var(--color-text-muted);
		display: flex;
		justify-content: center;
		gap: 0.5rem;
		align-items: center;
	}

	.period span {
		background: var(--color-bg-tertiary);
		padding: 0.2rem 0.5rem;
		border-radius: 0.3rem;
	}
</style>
