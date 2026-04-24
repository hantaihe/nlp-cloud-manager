<script lang="ts">
	export let costData: any;

	function formatCurrency(amount: string | number) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(Number(amount));
	}

	function getInclusiveEndDate(exclusiveEnd: string): string {
		if (!exclusiveEnd) return '';
		const d = new Date(exclusiveEnd);
		d.setDate(d.getDate() - 1);
		
		const year = d.getUTCFullYear();
		const month = String(d.getUTCMonth() + 1).padStart(2, '0');
		const day = String(d.getUTCDate()).padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

	$: currentItem = costData?.[0];
	$: startDate = currentItem?.TimePeriod?.Start || '';
	$: endDate = getInclusiveEndDate(currentItem?.TimePeriod?.End || '');

	$: groups = (currentItem?.Groups || [])
		.map((g: any) => ({
			name: g.Keys?.join(' | ') || '그룹 없음',
			amount: parseFloat(g.Metrics?.UnblendedCost?.Amount || '0')
		}))
		.filter((g: any) => g.amount > 0)
		.sort((a: any, b: any) => b.amount - a.amount);

	$: currentCost = (() => {
		const total = parseFloat(currentItem?.Total?.UnblendedCost?.Amount || '0');
		if (total === 0 && groups.length > 0) {
			return groups.reduce((acc: number, g: any) => acc + g.amount, 0);
		}
		return total;
	})();
</script>

<div class="cost-card glass">
	<h3>조회 기간 비용</h3>
	<div class="amount">{formatCurrency(currentCost)}</div>
	<div class="period">
		<span>{startDate}</span> → <span>{endDate}</span>
	</div>

	{#if groups.length > 0}
		<div class="groups-breakdown">
			{#each groups.slice(0, 5) as group}
				<div class="group-item">
					<span class="group-name" title={group.name}>{group.name}</span>
					<span class="group-amount">{formatCurrency(group.amount)}</span>
				</div>
			{/each}
			{#if groups.length > 5}
				<div class="more">...외 {groups.length - 5}개 항목 더보기</div>
			{/if}
		</div>
	{/if}
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
		background-clip: text;
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

	.groups-breakdown {
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		text-align: left;
	}

	.group-item {
		display: flex;
		justify-content: space-between;
		font-size: 0.9rem;
	}

	.group-name {
		color: var(--color-text-secondary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 70%;
	}

	.group-amount {
		font-weight: 600;
		color: var(--color-text-primary);
	}

	.more {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		text-align: center;
		margin-top: 0.5rem;
		font-style: italic;
	}
</style>
