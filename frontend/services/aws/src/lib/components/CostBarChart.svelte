<script lang="ts">
	export let costData: any[] = [];
	export let loading = false;

	function formatCurrency(amount: string | number) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 2
		}).format(Number(amount));
	}

	interface GroupData {
		name: string;
		amount: number;
	}

	interface ChartDataItem {
		date: string;
		total: number;
		groups: GroupData[];
		estimated: boolean;
	}

	$: chartData = (costData as any[]).map((d): ChartDataItem => {
		const groups = (d.Groups || [])
			.map(
				(g: any): GroupData => ({
					name: g.Keys?.join(' | ') || 'No Group',
					amount: parseFloat(g.Metrics?.UnblendedCost?.Amount || '0')
				})
			)
			.filter((g: GroupData) => g.amount > 0);

		let total = parseFloat(d.Total?.UnblendedCost?.Amount || '0');
		if (total === 0 && groups.length > 0) {
			total = groups.reduce((acc: number, g: GroupData) => acc + g.amount, 0);
		}

		return {
			date: d.TimePeriod.Start,
			total,
			groups: groups.length > 0 ? groups : [{ name: 'Total', amount: total }],
			estimated: d.Estimated
		};
	});

	$: allGroupNames = Array.from(
		new Set(chartData.flatMap((d: ChartDataItem) => d.groups.map((g: GroupData) => g.name)))
	);

	const colors = [
		'var(--color-accent)',
		'#ff4d4d',
		'#4d94ff',
		'#4dff88',
		'#ff4dff',
		'#ff944d',
		'#944dff',
		'#4dffff',
		'#ffd700',
		'#ff6b6b'
	];

	function getGroupColor(name: string) {
		const index = allGroupNames.indexOf(name);
		return colors[index % colors.length];
	}

	$: maxAmount = Math.max(...chartData.map((d) => d.total), 0.1);
</script>

<div class="chart-container glass">
	<div class="chart-header">
		<h3>Daily Cost Trend</h3>
		<div class="legend">
			<div class="legend-item">
				<span class="dot actual"></span> 실제
			</div>
			<div class="legend-item">
				<span class="dot estimated"></span> 예상
			</div>
		</div>
	</div>

	{#if loading}
		<div class="chart-loading">
			<div class="skeleton-bar"></div>
			<div class="skeleton-bar"></div>
			<div class="skeleton-bar"></div>
			<div class="skeleton-bar"></div>
		</div>
	{:else if chartData.length === 0}
		<div class="no-data">비용 데이터를 사용할 수 없습니다.</div>
	{:else}
		<div class="bars-wrapper">
			<div class="y-axis">
				<span>{formatCurrency(maxAmount)}</span>
				<span>{formatCurrency(maxAmount / 2)}</span>
				<span>$0.00</span>
			</div>
			<div class="bars">
				{#each chartData as data}
					<div class="bar-group">
						<div class="bar" style="height: {(data.total / maxAmount) * 100}%">
							{#each data.groups as group}
								<div
									class="bar-segment"
									class:estimated={data.estimated}
									style="height: {(group.amount / data.total) *
										100}%; background-color: {getGroupColor(group.name)}"
								>
									<div class="tooltip">
										<div class="tooltip-date">{data.date}</div>
										<div class="tooltip-group">{group.name}</div>
										<div class="tooltip-amount">{formatCurrency(group.amount)}</div>
										{#if data.estimated}
											<div class="tooltip-tag">예상</div>
										{/if}
									</div>
								</div>
							{/each}
						</div>
						<div class="label">{data.date.split('-').slice(1).join('/')}</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.chart-container {
		padding: 2rem;
		border-radius: 1.5rem;
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		margin-bottom: 2rem;
		min-height: 350px;
		display: flex;
		flex-direction: column;
	}

	.chart-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	h3 {
		margin: 0;
		font-size: 1.1rem;
		color: var(--color-text-primary);
		font-weight: 700;
	}

	.legend {
		display: flex;
		gap: 1.5rem;
		font-size: 0.85rem;
		color: var(--color-text-muted);
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.dot.actual {
		background: var(--color-accent);
	}

	.dot.estimated {
		background: var(--color-purple);
		opacity: 0.6;
	}

	.bars-wrapper {
		display: flex;
		flex: 1;
		gap: 1rem;
		position: relative;
		padding-top: 1rem;
	}

	.y-axis {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding-bottom: 25px;
		font-size: 0.75rem;
		color: var(--color-text-muted);
		text-align: right;
		width: 60px;
	}

	.bars {
		display: flex;
		flex: 1;
		align-items: flex-end;
		gap: 0.5rem;
		overflow-x: auto;
		padding-bottom: 1rem;
	}

	.bar-group {
		flex: 1;
		min-width: 30px;
		max-width: 60px;
		height: 100%;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		align-items: center;
		gap: 0.8rem;
	}

	.bar {
		width: 100%;
		border-radius: 4px 4px 0 0;
		position: relative;
		cursor: pointer;
		display: flex;
		flex-direction: column-reverse;
		overflow: hidden;
	}

	.bar-segment {
		width: 100%;
		position: relative;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.bar-segment:hover {
		filter: brightness(1.2);
		z-index: 2;
	}

	.bar-segment.estimated {
		opacity: 0.7;
		border-top: 1px dashed rgba(255, 255, 255, 0.3);
	}

	.label {
		font-size: 0.7rem;
		color: var(--color-text-muted);
		white-space: nowrap;
		transform: rotate(-45deg);
		margin-top: 0.5rem;
		width: 0;
		display: flex;
		justify-content: center;
	}

	.tooltip {
		position: absolute;
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%) translateY(-10px);
		background: var(--color-bg-secondary);
		padding: 0.6rem 1rem;
		border-radius: 0.5rem;
		border: 1px solid var(--color-border);
		box-shadow: var(--shadow-lg);
		pointer-events: none;
		opacity: 0;
		transition: all 0.2s ease;
		z-index: 10;
		white-space: nowrap;
		text-align: center;
	}

	.bar-segment:hover .tooltip {
		opacity: 1;
		transform: translateX(-50%) translateY(-15px);
	}

	.tooltip-date {
		font-size: 0.75rem;
		margin-bottom: 0.2rem;
		color: var(--color-text-muted);
	}

	.tooltip-group {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--color-text-primary);
		margin-bottom: 0.1rem;
	}

	.tooltip-amount {
		font-size: 1rem;
		font-weight: 800;
		color: var(--color-accent);
	}

	.tooltip-tag {
		font-size: 0.65rem;
		margin-top: 0.2rem;
		color: var(--color-purple);
		text-transform: uppercase;
		font-weight: 700;
	}

	.no-data {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-text-muted);
		font-style: italic;
	}

	.chart-loading {
		flex: 1;
		display: flex;
		align-items: flex-end;
		gap: 1rem;
		padding-bottom: 2rem;
	}

	.skeleton-bar {
		flex: 1;
		background: var(--color-border-subtle);
		border-radius: 4px;
		animation: pulse 1.5s infinite ease-in-out;
	}

	.skeleton-bar:nth-child(1) {
		height: 40%;
	}
	.skeleton-bar:nth-child(2) {
		height: 70%;
		animation-delay: 0.2s;
	}
	.skeleton-bar:nth-child(3) {
		height: 50%;
		animation-delay: 0.4s;
	}
	.skeleton-bar:nth-child(4) {
		height: 30%;
		animation-delay: 0.6s;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 0.5;
		}
		50% {
			opacity: 1;
		}
	}
</style>
