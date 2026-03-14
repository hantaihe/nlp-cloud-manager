<script lang="ts">
	interface Summary {
		total_budget?: number;
		currency_code?: string;
		active_accounts?: number;
		account_count?: number;
		start_date?: string;
		end_date?: string;
	}

	let { summary = {} }: { summary: Summary } = $props();

	function formatCurrency(amount: number, code: string) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: code || 'USD'
		}).format(amount);
	}
</script>

<div class="cost-card glass">
	<h3>Current Month Budget Summary</h3>
	<div class="amount">{formatCurrency(summary?.total_budget || 0, summary?.currency_code)}</div>
	<div class="stats">
		<div class="stat">
			<span class="label">Billing Accounts</span>
			<span class="value">{summary?.active_accounts || 0} / {summary?.account_count || 0}</span>
		</div>
		<div class="stat">
			<span class="label">Period</span>
			<span class="value">{summary?.start_date} ~ {summary?.end_date}</span>
		</div>
	</div>
</div>

<style>
	.cost-card {
		padding: 2.5rem;
		border-radius: 2rem;
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		box-shadow: var(--shadow-xl);
		text-align: center;
		transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		position: relative;
		overflow: hidden;
	}

	.cost-card::before {
		content: '';
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: radial-gradient(circle, rgba(66, 133, 244, 0.05) 0%, transparent 70%);
		pointer-events: none;
	}

	.cost-card:hover {
		transform: translateY(-8px) scale(1.02);
		border-color: #4285f4;
		box-shadow: 0 20px 40px rgba(66, 133, 244, 0.15);
	}

	h3 {
		margin: 0;
		font-size: 1rem;
		color: #4285f4;
		text-transform: uppercase;
		letter-spacing: 0.15rem;
		font-weight: 800;
	}

	.amount {
		font-size: 4.5rem;
		font-weight: 900;
		margin: 1.5rem 0;
		background: linear-gradient(135deg, #4285f4, #34a853, #fbbc04);
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
	}

	.stats {
		display: flex;
		justify-content: center;
		gap: 3rem;
		margin-top: 1.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--color-border-subtle);
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.label {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05rem;
	}

	.value {
		font-size: 1rem;
		font-weight: 700;
		color: var(--color-text-primary);
	}
</style>
