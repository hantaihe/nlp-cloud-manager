<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDashboardLayout, saveDashboardLayout } from '$lib/api';
	import type { DashboardItem } from '$lib/types';
	import StatCard from '$lib/components/StatCard.svelte';
	import { dashboardSettings } from '$lib/stores/dashboardSettings';
	import { get } from 'svelte/store';
	import { SERVICES, COMBINED_ITEMS } from '$lib/services';
	import {
		fetchServiceStats,
		getCombinedStats,
		formatCurrency,
		type CloudStats
	} from '$lib/dashboardApi';

	let loading = $state(false);
	let isEditing = $state(false);

	let serviceStats = $state<Record<string, CloudStats | null>>({});
	let selectedProviders = $state<Record<string, boolean>>({});

	SERVICES.forEach((s) => {
		selectedProviders[s.id] = true;
	});

	let combinedStats = $derived(
		getCombinedStats(serviceStats as Record<string, CloudStats | undefined>, selectedProviders)
	);

	const DEFAULT_LAYOUT: DashboardItem[] = [
		...SERVICES.flatMap((s) =>
			s.dashboardItems.map((item) => ({
				...item,
				category: s.category as any,
				visible: true
			}))
		),
		...COMBINED_ITEMS.map((item) => ({
			...item,
			visible: true
		}))
	];

	let layout = $state<DashboardItem[]>([]);

	async function loadData() {
		loading = true;
		const results = await Promise.all(SERVICES.map((s) => fetchServiceStats(s.id)));
		const newStats: Record<string, CloudStats | null> = {};
		SERVICES.forEach((s, i) => {
			newStats[s.id] = results[i];
		});
		serviceStats = newStats;
		loading = false;
	}

	async function initLayout() {
		const saved = await fetchDashboardLayout();
		if (saved && saved.length > 0) {
			const existingIds = new Set(saved.map((i: any) => i.id));
			const newItems = DEFAULT_LAYOUT.filter((i) => !existingIds.has(i.id));
			const merged = saved.map((s: any) => {
				const def = DEFAULT_LAYOUT.find((d) => d.id === s.id);
				return { ...s, category: s.category || def?.category };
			});
			layout = [...merged, ...newItems];
		} else {
			layout = [...DEFAULT_LAYOUT];
		}
	}

	async function saveLayout() {
		await saveDashboardLayout(layout);
	}

	onMount(() => {
		initLayout();
		loadData();

		let timer: ReturnType<typeof setInterval>;
		const unsubscribe = dashboardSettings.subscribe((settings) => {
			if (timer) clearInterval(timer);
			if (settings.pollInterval > 0) {
				timer = setInterval(loadData, settings.pollInterval);
			}
		});

		return () => {
			if (timer) clearInterval(timer);
			unsubscribe();
		};
	});

	let filteredLayout = $derived(layout.filter((i) => i.visible));

	let categories = $derived(() => {
		const cats = new Map<string, DashboardItem[]>();
		for (const item of layout) {
			const cat = item.category || 'other';
			if (!cats.has(cat)) cats.set(cat, []);
			cats.get(cat)!.push(item);
		}
		return cats;
	});

	const categoryLabels: Record<string, string> = {
		aws: 'AWS',
		azure: 'Azure',
		gcp: 'GCP',
		combined: '종합 통계'
	};

	function toggleVisibility(id: string) {
		const item = layout.find((i) => i.id === id);
		if (item) {
			item.visible = !item.visible;
			saveLayout();
		}
	}

	let draggingId = $state<string | null>(null);
	let startX = 0;
	let startY = 0;
	let startCols = 1;
	let startRows = 1;
	let cellWidth = 0;
	let cellHeight = 0;
	const GAP = 24;

	function startResize(e: MouseEvent, id: string, direction: 'horizontal' | 'vertical' | 'both') {
		e.preventDefault();
		e.stopPropagation();
		draggingId = id;
		startX = e.clientX;
		startY = e.clientY;

		const item = layout.find((i) => i.id === id);
		if (!item) return;

		startCols = item.cols;
		startRows = item.rows;

		const element = (e.target as HTMLElement).closest('.grid-item');
		if (element) {
			const rect = element.getBoundingClientRect();
			cellWidth = (rect.width - GAP * (item.cols - 1)) / item.cols;
			cellHeight = (rect.height - GAP * (item.rows - 1)) / item.rows;
		} else {
			cellWidth = 280;
			cellHeight = 180;
		}

		window.addEventListener('mousemove', onMouseMove);
		window.addEventListener('mouseup', onMouseUp);
	}

	function onMouseMove(e: MouseEvent) {
		if (!draggingId) return;
		const item = layout.find((i) => i.id === draggingId);
		if (!item) return;

		const dx = e.clientX - startX;
		const dy = e.clientY - startY;
		const colChange = Math.round(dx / (cellWidth + GAP));
		const rowChange = Math.round(dy / (cellHeight + GAP));
		const newCols = Math.max(1, Math.min(4, startCols + colChange));
		const newRows = Math.max(1, Math.min(4, startRows + rowChange));

		if (item.cols !== newCols) item.cols = newCols;
		if (item.rows !== newRows) item.rows = newRows;
	}

	function onMouseUp() {
		if (draggingId) saveLayout();
		draggingId = null;
		window.removeEventListener('mousemove', onMouseMove);
		window.removeEventListener('mouseup', onMouseUp);
	}

	let dragSrcIndex = $state<number | null>(null);
	let dragEnterIndex = $state<number | null>(null);

	function handleDragStart(e: DragEvent, index: number) {
		if (draggingId) {
			e.preventDefault();
			return;
		}
		dragSrcIndex = index;
		if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move';
	}

	function handleDragOver(e: DragEvent, index: number) {
		e.preventDefault();
		if (dragSrcIndex === null) return;
		e.dataTransfer!.dropEffect = 'move';
		dragEnterIndex = index;
	}

	function handleDrop(e: DragEvent, index: number) {
		e.stopPropagation();
		if (dragSrcIndex !== null && dragSrcIndex !== index) {
			const newLayout = [...layout];
			const [movedItem] = newLayout.splice(dragSrcIndex, 1);
			newLayout.splice(index, 0, movedItem);
			layout = newLayout;
			saveLayout();
		}
		dragSrcIndex = null;
		dragEnterIndex = null;
	}

	function handleDragEnd() {
		dragSrcIndex = null;
		dragEnterIndex = null;
	}

	function getProviderStats(category: string): CloudStats | null {
		const service = SERVICES.find((s) => s.category === category);
		return service ? serviceStats[service.id] : null;
	}

	function getProviderColor(category: string): string {
		const service = SERVICES.find((s) => s.category === category);
		return service?.color || 'var(--color-purple)';
	}

	function getProviderIcon(category: string): string {
		if (category === 'combined') return '/icons/total.png';
		const service = SERVICES.find((s) => s.category === category);
		return service?.icon || '';
	}
</script>

<div class="dashboard container">
	<header class="header">
		<div class="header-left">
			<h1>Dashboard</h1>
			{#if loading}
				<span class="loading-badge">Updating...</span>
			{/if}
		</div>
		<button class="btn-edit" onclick={() => (isEditing = !isEditing)}>
			{isEditing ? 'Done' : 'Customize Board'}
		</button>
	</header>

	{#if isEditing}
		<div class="controls-panel">
			<div class="controls-grid">
				{#each [...categories().entries()] as [cat, items]}
					<div class="settings-group">
						<div class="settings-group-header">
							{#if getProviderIcon(cat)}
								<img src={getProviderIcon(cat)} alt="" class="header-logo" />
							{/if}
							<h3>{categoryLabels[cat] || cat}</h3>
						</div>
						<div class="toggles">
							{#each items as item}
								<label class="toggle">
									<input
										type="checkbox"
										checked={item.visible}
										onchange={() => toggleVisibility(item.id)}
									/>
									<span class="toggle-icon">
										{#if getProviderIcon(item.category)}
											<img src={getProviderIcon(item.category)} alt="" class="small-logo" />
										{/if}
									</span>
									<span class="toggle-label">{item.label}</span>
								</label>
							{/each}
						</div>
					</div>
				{/each}
			</div>

			<div class="settings-row">
				<div class="settings-group">
					<h3>업데이트 주기</h3>
					<select bind:value={$dashboardSettings.pollInterval} class="select-interval">
						<option value={10000}>10초</option>
						<option value={30000}>30초</option>
						<option value={60000}>1분</option>
						<option value={300000}>5분</option>
						<option value={0}>수동</option>
					</select>
				</div>
			</div>
		</div>
	{/if}

	<div class="provider-selector">
		<span class="selector-label">종합 통계 포함:</span>
		{#each SERVICES as service}
			<label class="provider-toggle {service.id}-toggle">
				<input type="checkbox" bind:checked={selectedProviders[service.id]} />
				<span
					class="provider-chip"
					style="--provider-color: {service.color}; color: {selectedProviders[service.id]
						? service.color
						: 'var(--color-text-muted)'}; background: {selectedProviders[service.id]
						? `${service.color}26`
						: 'var(--color-bg-secondary)'}; border-color: {selectedProviders[service.id]
						? service.color
						: 'var(--color-border)'}"
				>
					{service.name}
				</span>
			</label>
		{/each}
	</div>

	<div class="grid-layout">
		{#each filteredLayout as item, index (item.id)}
			{@const stats = getProviderStats(item.category)}
			<div
				class="grid-item"
				style="grid-column: span {item.cols}; grid-row: span {item.rows}; opacity: {dragSrcIndex ===
				index
					? 0.4
					: 1};"
				draggable={true}
				ondragstart={(e) => handleDragStart(e, index)}
				ondragover={(e) => handleDragOver(e, index)}
				ondrop={(e) => handleDrop(e, index)}
				ondragend={handleDragEnd}
				role="listitem"
			>
				<div class="card-wrapper">
					{#if item.id.includes('total-cost') && stats}
						<StatCard
							title="Total Cost"
							value={formatCurrency(stats.totalCost)}
							subtitle="Current month"
							imgSrc={getProviderIcon(item.category)}
							color={item.category}
							mode="kpi"
							error={stats.error}
							trend={{
								value: Math.abs(stats.costTrend),
								direction: stats.costTrend > 0 ? 'up' : 'down'
							}}
							chartData={stats.monthlyData.map((m) => ({ label: m.month, value: m.cost }))}
							chartColor={getProviderColor(item.category)}
							href="/service/{item.category}"
						/>
					{:else if item.id.includes('trend') && stats && item.category !== 'combined'}
						<StatCard
							title="Monthly Trend"
							value={formatCurrency(stats.totalCost)}
							imgSrc={getProviderIcon(item.category)}
							color={item.category}
							mode="chart"
							chartType="sparkline"
							error={stats.error}
							chartData={stats.monthlyData.map((m) => ({ label: m.month, value: m.cost }))}
							chartColor={getProviderColor(item.category)}
							trend={{
								value: Math.abs(stats.costTrend),
								direction: stats.costTrend > 0 ? 'up' : 'down'
							}}
							href="/service/{item.category}"
						/>
					{:else if item.id.includes('top-services') && stats}
						<StatCard
							title="Top Services"
							imgSrc={getProviderIcon(item.category)}
							color={item.category}
							mode="list"
							error={stats.error}
							chartData={stats.topServices.map((s) => ({
								label: s.name,
								value: s.cost,
								color: getProviderColor(item.category)
							}))}
							chartColor={getProviderColor(item.category)}
							href="/service/{item.category}"
						/>
					{:else if item.id.includes('recommendations') && stats}
						<StatCard
							title="Recommendations"
							imgSrc={getProviderIcon(item.category)}
							color={item.category}
							mode="list"
							error={stats.error}
							chartData={(stats.recommendations || []).map((r) => ({
								label: r.title,
								value: 100,
								displayValue: r.impact || r.info,
								color: getProviderColor(item.category)
							}))}
							href="/service/{item.category}"
						/>
					{:else if item.id.includes('resources') && stats && item.category !== 'combined'}
						<StatCard
							title="Active Resources"
							value={stats.activeResources}
							subtitle="Detailed view"
							imgSrc={getProviderIcon(item.category)}
							color={item.category}
							mode="list"
							error={stats.error}
							chartData={(stats.resourcesSummary || []).slice(0, 3).map((r) => ({
								label: r.name,
								value: 100,
								displayValue: r.type,
								color: getProviderColor(item.category)
							}))}
						/>
					{:else if item.id.includes('budget') && stats}
						<StatCard
							title="Budget Usage"
							value={stats.budgetUsed + '%'}
							subtitle={stats.alerts > 0 ? `${stats.alerts} Alerts active` : 'Monthly budget'}
							imgSrc={getProviderIcon(item.category)}
							color={stats.alerts > 0 ? 'warning' : item.category}
							mode="progress"
							error={stats.error}
							progress={stats.budgetUsed}
						/>
					{:else if item.type === 'combined-total'}
						<StatCard
							title="Total Cloud Spend"
							value={formatCurrency(combinedStats.totalCost)}
							subtitle="Selected providers"
							imgSrc="/icons/total.png"
							color="combined"
							mode="kpi"
							trend={{
								value: Math.abs(combinedStats.costTrend),
								direction: combinedStats.costTrend > 0 ? 'up' : 'down'
							}}
							chartData={combinedStats.monthlyData.map((m) => ({ label: m.month, value: m.cost }))}
							chartColor="var(--color-purple)"
						/>
					{:else if item.type === 'combined-trend'}
						<StatCard
							title="Cloud Spend Trend"
							value={formatCurrency(combinedStats.totalCost)}
							imgSrc="/icons/total.png"
							color="combined"
							mode="chart"
							chartType="sparkline"
							chartData={combinedStats.monthlyData.map((m) => ({ label: m.month, value: m.cost }))}
							chartColor="var(--color-purple)"
							trend={{
								value: Math.abs(combinedStats.costTrend),
								direction: combinedStats.costTrend > 0 ? 'up' : 'down'
							}}
						/>
					{:else if item.type === 'combined-compare'}
						<StatCard
							title="Provider Comparison"
							imgSrc="/icons/total.png"
							color="combined"
							mode="list"
							chartData={SERVICES.filter((s) => selectedProviders[s.id] && serviceStats[s.id]).map(
								(s) => ({
									label: s.name,
									value: serviceStats[s.id]!.totalCost,
									color: s.color
								})
							)}
						/>
					{:else if item.type === 'combined-top'}
						<StatCard
							title="Top Services (All Providers)"
							imgSrc="/icons/total.png"
							color="combined"
							mode="list"
							chartData={combinedStats.topServices.map((s) => ({
								label: s.name,
								value: s.cost,
								color: s.color
							}))}
						/>
					{:else if item.type === 'combined-recommendations'}
						<StatCard
							title="Cloud Recommendations"
							imgSrc="/icons/total.png"
							color="combined"
							mode="list"
							chartData={(combinedStats.recommendations || []).slice(0, 5).map((r) => ({
								label: r.title,
								value: 100,
								displayValue: r.impact || r.info,
								color: 'var(--color-purple)'
							}))}
						/>
					{:else if item.type === 'combined-resources'}
						<StatCard
							title="Total Resources"
							value={combinedStats.activeResources}
							subtitle="Across all clouds"
							imgSrc="/icons/total.png"
							color="combined"
							mode="list"
							chartData={(combinedStats.resourcesSummary || []).slice(0, 5).map((r) => ({
								label: r.name,
								value: 100,
								displayValue: r.type,
								color: 'var(--color-purple)'
							}))}
						/>
					{:else if item.type === 'combined-alerts'}
						<StatCard
							title="Active Alerts"
							value={combinedStats.alerts}
							subtitle={combinedStats.alerts === 0
								? 'All clear!'
								: `${combinedStats.alerts} issues found`}
							imgSrc="/icons/total.png"
							color={combinedStats.alerts > 0 ? 'warning' : 'combined'}
							mode="list"
							chartData={(combinedStats.recentAlerts || []).map((a) => ({
								label: a.message,
								value: a.severity === 'error' ? 100 : 50,
								displayValue: a.severity.toUpperCase(),
								color: a.severity === 'error' ? 'var(--color-danger)' : 'var(--color-warning)'
							}))}
						/>
					{:else}
						<div class="placeholder-card">
							<div class="placeholder-icon">
								{#if getProviderIcon(item.category)}
									<img src={getProviderIcon(item.category)} alt="" class="small-logo" />
								{/if}
							</div>
							<div class="placeholder-text">{item.label}</div>
							<div class="placeholder-loading">Loading data...</div>
						</div>
					{/if}
				</div>

				<div
					class="resize-handle right"
					onmousedown={(e) => startResize(e, item.id, 'horizontal')}
					role="button"
					aria-label="Resize width"
					tabindex="0"
				></div>
				<div
					class="resize-handle bottom"
					onmousedown={(e) => startResize(e, item.id, 'vertical')}
					role="button"
					aria-label="Resize height"
					tabindex="0"
				></div>
				<div
					class="resize-handle corner"
					onmousedown={(e) => startResize(e, item.id, 'both')}
					role="button"
					aria-label="Resize both"
					tabindex="0"
				></div>
			</div>
		{/each}
	</div>
</div>

<style>
	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		padding: 2rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.header h1 {
		font-size: 1.5rem;
		font-weight: 700;
	}

	.loading-badge {
		padding: 0.2rem 0.6rem;
		background: var(--color-accent-muted);
		border-radius: var(--radius-full);
		font-size: 0.75rem;
		color: var(--color-accent);
		font-weight: 500;
		animation: pulse 1.5s infinite;
	}

	.btn-edit {
		padding: 0.5rem 1rem;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.9rem;
		transition: all 0.2s;
		color: var(--color-text-primary);
		font-weight: 500;
	}

	.btn-edit:hover {
		background: var(--color-bg-tertiary);
		border-color: var(--color-accent);
	}

	.controls-panel {
		background: var(--color-bg-secondary);
		padding: 1.25rem;
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-border);
		animation: slideDown 0.2s ease-out;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.controls-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 1rem;
	}

	.settings-row {
		display: flex;
		gap: 1rem;
	}

	.settings-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.settings-group-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid var(--color-border-subtle);
	}

	.header-logo {
		width: 24px;
		height: 24px;
		object-fit: contain;
	}

	.header-symbol {
		font-size: 1.3rem;
		width: 24px;
		text-align: center;
		color: var(--color-text-muted);
	}

	.settings-group h3 {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.toggles {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		cursor: pointer;
		color: var(--color-text-secondary);
	}

	.toggle-icon {
		width: 16px;
		height: 16px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.9rem;
		font-weight: bold;
	}

	.small-logo {
		width: 14px;
		height: 14px;
		object-fit: contain;
	}

	.toggle-label {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.select-interval {
		padding: 0.4rem 0.8rem;
		border-radius: 6px;
		border: 1px solid var(--color-border);
		background: var(--color-bg-card);
		font-size: 0.85rem;
		color: var(--color-text-primary);
		outline: none;
	}

	.provider-selector {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 0;
	}

	.selector-label {
		font-size: 0.85rem;
		color: var(--color-text-secondary);
		font-weight: 500;
	}

	.provider-toggle {
		cursor: pointer;
	}

	.provider-toggle input {
		display: none;
	}

	.provider-chip {
		display: inline-flex;
		align-items: center;
		padding: 0.3rem 0.8rem;
		border-radius: var(--radius-full);
		font-size: 0.8rem;
		font-weight: 600;
		border: 1.5px solid var(--color-border);
		background: var(--color-bg-secondary);
		color: var(--color-text-muted);
		transition: all 0.2s;
	}

	.grid-layout {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		grid-auto-rows: 200px;
		gap: 1.5rem;
	}

	.grid-item {
		position: relative;
		display: flex;
		flex-direction: column;
		cursor: grab;
		transition:
			transform 0.2s,
			box-shadow 0.2s;
	}

	.grid-item:active {
		cursor: grabbing;
	}

	.card-wrapper {
		height: 100%;
		width: 100%;
		user-select: none;
	}

	:global(.card-wrapper > .stat-card) {
		height: 100%;
	}

	.placeholder-card {
		height: 100%;
		width: 100%;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 1rem;
	}

	.placeholder-icon {
		font-size: 2rem;
		opacity: 0.5;
	}

	.placeholder-text {
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--color-text-secondary);
	}

	.placeholder-loading {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		animation: pulse 2s infinite;
	}

	.resize-handle {
		position: absolute;
		z-index: 20;
		background: rgba(0, 0, 0, 0);
		transition: background 0.2s;
	}

	.resize-handle:hover {
		background: rgba(0, 123, 255, 0.3);
	}

	.resize-handle.right {
		top: 0;
		right: -8px;
		width: 16px;
		height: 100%;
		cursor: col-resize;
	}

	.resize-handle.bottom {
		bottom: -8px;
		left: 0;
		width: 100%;
		height: 16px;
		cursor: row-resize;
	}

	.resize-handle.corner {
		bottom: -8px;
		right: -8px;
		width: 16px;
		height: 16px;
		cursor: nwse-resize;
		z-index: 21;
	}

	:global(.grid-item:has(.resize-handle:hover)) {
		outline: 2px dashed var(--color-accent);
		outline-offset: 4px;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.6;
		}
	}
</style>
