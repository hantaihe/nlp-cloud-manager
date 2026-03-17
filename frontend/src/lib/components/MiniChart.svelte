<script lang="ts">
	interface DataPoint {
		label: string;
		value: number;
		displayValue?: string;
		color?: string;
	}

	interface Props {
		type?: 'sparkline' | 'minibar';
		data: DataPoint[];
		height?: number;
		color?: string;
		showLabels?: boolean;
	}

	let {
		type = 'sparkline',
		data,
		height = 60,
		color = 'var(--color-accent)',
		showLabels = false
	}: Props = $props();

	const maxValue = $derived(Math.max(...data.map((d) => d.value), 1));

	const sparkPoints = $derived(() => {
		if (data.length === 0) return [];
		const w = 100;
		const h = height;
		const pad = 4;
		const step = data.length > 1 ? (w - pad * 2) / (data.length - 1) : 0;
		return data.map((d, i) => ({
			x: pad + i * step,
			y: pad + (h - pad * 2) * (1 - d.value / maxValue),
			value: d.value,
			label: d.label
		}));
	});

	const sparkPath = $derived(() => {
		const pts = sparkPoints();
		if (pts.length === 0) return '';
		return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
	});

	const sparkArea = $derived(() => {
		const pts = sparkPoints();
		if (pts.length === 0) return '';
		const line = sparkPath();
		const last = pts[pts.length - 1];
		const first = pts[0];
		return `${line} L ${last.x} ${height - 2} L ${first.x} ${height - 2} Z`;
	});
</script>

<div class="mini-chart" style="height: {height}px;">
	{#if type === 'sparkline'}
		<svg viewBox="0 0 100 {height}" preserveAspectRatio="none" class="sparkline-svg">
			<defs>
				<linearGradient
					id="sparkGrad-{color.replace(/[^a-zA-Z0-9]/g, '')}"
					x1="0"
					y1="0"
					x2="0"
					y2="1"
				>
					<stop offset="0%" stop-color={color} stop-opacity="0.3" />
					<stop offset="100%" stop-color={color} stop-opacity="0.02" />
				</linearGradient>
			</defs>
			<path d={sparkArea()} fill="url(#sparkGrad-{color.replace(/[^a-zA-Z0-9]/g, '')})" />
			<path
				d={sparkPath()}
				fill="none"
				stroke={color}
				stroke-width="1.5"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
			{#each sparkPoints() as pt}
				<circle cx={pt.x} cy={pt.y} r="1.5" fill={color} opacity="0">
					<title>{pt.label}: ${pt.value.toLocaleString()}</title>
				</circle>
			{/each}
			{#if sparkPoints().length > 0}
				{@const last = sparkPoints()[sparkPoints().length - 1]}
				<circle cx={last.x} cy={last.y} r="2" fill={color} />
			{/if}
		</svg>
	{:else if type === 'minibar'}
		<div class="minibar-list">
			{#each data.slice(0, 5) as item, i}
				<div class="minibar-row">
					<span class="minibar-label">{item.label}</span>
					<div class="minibar-track">
						<div
							class="minibar-fill"
							style="width: {(item.value / maxValue) * 100}%; background: {item.color || color};"
						></div>
					</div>
					<span class="minibar-value">
						{#if item.displayValue}
							{item.displayValue}
						{:else}
							${item.value.toLocaleString()}
						{/if}
					</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.mini-chart {
		width: 100%;
		overflow: hidden;
	}

	.sparkline-svg {
		width: 100%;
		height: 100%;
		display: block;
	}

	.sparkline-svg circle:not([opacity='0']) {
		filter: drop-shadow(0 0 3px currentColor);
	}

	.minibar-list {
		display: flex;
		flex-direction: column;
		gap: 6px;
		height: 100%;
		justify-content: center;
	}

	.minibar-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.minibar-label {
		font-size: 0.7rem;
		color: var(--color-text-secondary);
		min-width: 60px;
		text-align: right;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.minibar-track {
		flex: 1;
		height: 8px;
		background: var(--color-bg-tertiary);
		border-radius: 4px;
		overflow: hidden;
	}

	.minibar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.minibar-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--color-text-primary);
		min-width: 50px;
		text-align: right;
	}
</style>
