<script lang="ts">
	interface Account {
		display_name?: string;
		open?: boolean;
		name?: string;
		master_billing_account?: string;
	}

	let { accounts = [] }: { accounts: Account[] } = $props();
</script>

<div class="accounts-container glass">
	<h3>📋 Billing Accounts</h3>
	<div class="accounts-grid">
		{#if accounts.length === 0}
			<p class="empty">청구 계정이 없습니다.</p>
		{:else}
			{#each accounts as account}
				<div class="account-card">
					<div class="account-header">
						<span class="account-name">{account.display_name || 'Unnamed'}</span>
						<span class="status-badge" class:open={account.open} class:closed={!account.open}>
							{account.open ? 'OPEN' : 'CLOSED'}
						</span>
					</div>
					<div class="account-details">
						<div class="detail-row">
							<span class="label">Name</span>
							<span class="value">{account.name}</span>
						</div>
						{#if account.master_billing_account}
							<div class="detail-row">
								<span class="label">Master</span>
								<span class="value">{account.master_billing_account}</span>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.accounts-container {
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

	.accounts-grid {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.account-card {
		padding: 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.8rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.account-card:hover {
		border-color: var(--color-accent);
		transform: translateY(-2px);
	}

	.account-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.account-name {
		font-weight: 600;
		color: var(--color-text-primary);
		font-size: 1rem;
	}

	.status-badge {
		padding: 0.15rem 0.5rem;
		border-radius: 1rem;
		font-size: 0.65rem;
		font-weight: 700;
		text-transform: uppercase;
	}

	.status-badge.open {
		background: rgba(52, 168, 83, 0.15);
		color: #34a853;
	}

	.status-badge.closed {
		background: rgba(234, 67, 53, 0.15);
		color: #ea4335;
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.3rem 0;
	}

	.label {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.value {
		font-size: 0.8rem;
		color: var(--color-text-secondary);
		font-family: 'SF Mono', 'Fira Code', monospace;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
