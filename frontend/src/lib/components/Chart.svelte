<script lang="ts">
	interface DataPoint {
		label: string;
		value: number;
		color?: string;
	}

	interface Props {
		title?: string;
		type?: 'bar' | 'line';
		data: DataPoint[];
		height?: number;
		showLabels?: boolean;
		showValues?: boolean;
	}

	let {
		title = '',
		type = 'bar',
		data,
		height = 200,
		showLabels = true,
		showValues = true
	}: Props = $props();

	const maxValue = $derived(Math.max(...data.map((d) => d.value), 1));
	const chartPadding = 40;
	const barWidth = $derived((100 - chartPadding) / data.length);

	const defaultColors = ['#ff9900', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

	function getBarHeight(value: number): number {
		return (value / maxValue) * (height - 60);
	}

	function getColor(index: number, customColor?: string): string {
		return customColor ?? defaultColors[index % defaultColors.length];
	}

	const linePoints = $derived(() => {
		const padding = 30;
		const usableWidth = 100 - padding * 2;
		const step = data.length > 1 ? usableWidth / (data.length - 1) : 0;

		return data.map((d, i) => ({
			x: padding + i * step,
			y: height - 40 - getBarHeight(d.value),
			value: d.value,
			label: d.label
		}));
	});

	const linePath = $derived(() => {
		const points = linePoints();
		if (points.length === 0) return '';

		return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
	});

	const areaPath = $derived(() => {
		const points = linePoints();
		if (points.length === 0) return '';

		const line = linePath();
		const lastPoint = points[points.length - 1];
		const firstPoint = points[0];

		return `${line} L ${lastPoint.x} ${height - 40} L ${firstPoint.x} ${height - 40} Z`;
	});
</script>

<div class="chart-container">
	{#if title}
		<div class="chart-header">
			<h3 class="chart-title">{title}</h3>
		</div>
	{/if}

	<div class="chart-body">
		<svg viewBox="0 0 100 {height}" class="chart-svg" preserveAspectRatio="xMidYMid meet">
			{#each [0, 0.25, 0.5, 0.75, 1] as tick}
				<line
					x1="5"
					y1={height - 40 - tick * (height - 60)}
					x2="95"
					y2={height - 40 - tick * (height - 60)}
					class="grid-line"
				/>
				{#if showValues}
					<text x="3" y={height - 38 - tick * (height - 60)} class="axis-label">
						{Math.round(maxValue * tick)}
					</text>
				{/if}
			{/each}

			{#if type === 'bar'}
				{#each data as item, index (item.label)}
					{@const barHeight = getBarHeight(item.value)}
					{@const x = 10 + index * barWidth + barWidth * 0.1}
					{@const y = height - 40 - barHeight}
					{@const width = barWidth * 0.8}

					<g class="bar-group">
						<rect
							{x}
							{y}
							{width}
							height={barHeight}
							fill={getColor(index, item.color)}
							rx="1"
							class="bar"
						>
							<title>{item.label}: {item.value}</title>
						</rect>

						{#if showLabels}
							<text x={x + width / 2} y={height - 25} class="bar-label" text-anchor="middle">
								{item.label.slice(0, 3)}
							</text>
						{/if}
					</g>
				{/each}
			{:else}
				<defs>
					<linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
						<stop offset="0%" stop-color="var(--color-accent)" stop-opacity="0.3" />
						<stop offset="100%" stop-color="var(--color-accent)" stop-opacity="0" />
					</linearGradient>
				</defs>

				<path d={areaPath()} fill="url(#lineGradient)" />
				<path d={linePath()} class="line-path" fill="none" />

				{#each linePoints() as point, index (point.label)}
					<circle cx={point.x} cy={point.y} r="1.5" class="line-point">
						<title>{point.label}: {point.value}</title>
					</circle>

					{#if showLabels}
						<text x={point.x} y={height - 25} class="bar-label" text-anchor="middle">
							{point.label.slice(0, 3)}
						</text>
					{/if}
				{/each}
			{/if}
		</svg>
	</div>
</div>

<style>
	.chart-container {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.chart-header {
		padding: var(--spacing-lg);
		border-bottom: 1px solid var(--color-border);
	}

	.chart-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text-primary);
	}

	.chart-body {
		padding: var(--spacing-md);
	}

	.chart-svg {
		width: 100%;
		height: auto;
	}

	.grid-line {
		stroke: var(--color-border);
		stroke-width: 0.2;
		stroke-dasharray: 1, 1;
	}

	.axis-label {
		font-size: 2.5px;
		fill: var(--color-text-muted);
	}

	.bar {
		transition: opacity var(--transition-fast);
	}

	.bar-group:hover .bar {
		opacity: 0.8;
	}

	.bar-label {
		font-size: 2.5px;
		fill: var(--color-text-muted);
	}

	.line-path {
		stroke: var(--color-accent);
		stroke-width: 0.5;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.line-point {
		fill: var(--color-accent);
		transition: r var(--transition-fast);
	}

	.line-point:hover {
		r: 2.5;
	}
</style>
