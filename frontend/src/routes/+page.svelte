<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDashboardLayout, saveDashboardLayout } from '$lib/api';
	import type { DashboardItem } from '$lib/types';
	import Card from '$lib/components/Card.svelte';
	import { searchStore } from '$lib/search.svelte';
	import { dashboardSettings } from '$lib/stores/dashboardSettings';
	import { get } from 'svelte/store';

	let loading = $state(false);
	let isEditing = $state(false);

	const DEFAULT_LAYOUT: DashboardItem[] = [
		{ id: 'sample', type: 'sample', label: 'Sample Service', visible: true, cols: 1, rows: 1 },
		{ id: 'aws', type: 'aws', label: 'AWS Billing', visible: true, cols: 2, rows: 1 }
	];

	let layout = $state<DashboardItem[]>([]);

	async function loadData() {
		loading = false;
	}

	async function initLayout() {
		const saved = await fetchDashboardLayout();
		if (saved && saved.length > 0) {
			const savedMap = new Map(saved.map((i: any) => [i.id, i]));
			const existingIds = new Set(saved.map((i: any) => i.id));
			const newItems = DEFAULT_LAYOUT.filter((i) => !existingIds.has(i.id));

			layout = [...saved, ...newItems];
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
			timer = setInterval(loadData, settings.pollInterval);
		});

		return () => {
			if (timer) clearInterval(timer);
			unsubscribe();
		};
	});

	let filteredLayout = $derived(layout.filter((i) => i.visible));

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

		if (item.cols !== newCols || item.rows !== newRows) {
			if (item.cols !== newCols) item.cols = newCols;
			if (item.rows !== newRows) item.rows = newRows;
		}
	}

	function onMouseUp() {
		if (draggingId) {
			saveLayout();
		}
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
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
		}
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
</script>

<div class="dashboard container">
	<header class="header">
		<h1>Dashboard</h1>
		<button class="btn-edit" onclick={() => (isEditing = !isEditing)}>
			{isEditing ? 'Done' : 'Customize Board'}
		</button>
	</header>

	{#if isEditing}
		<div class="controls-panel">
			<div class="settings-group">
				<h3>서비스 보여주기/숨기기</h3>
				<div class="toggles">
					{#each layout as item}
						<label class="toggle">
							<input
								type="checkbox"
								checked={item.visible}
								onchange={() => toggleVisibility(item.id)}
							/>
							{item.label}
						</label>
					{/each}
				</div>
			</div>

			<div class="settings-group">
				<h3>업데이트 주기</h3>
				<div class="interval-selector">
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

	<div class="grid-layout">
		{#each filteredLayout as item, index (item.id)}
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
					{#if item.type === 'sample'}
						<Card
							title={item.label}
							value="Active"
							subtitle="Running smoothly"
							icon="⚡"
							color="success"
						>
							{#snippet action()}
								<a class="shortcut-link" href="/sample">Go</a>
							{/snippet}
						</Card>
					{:else if item.type === 'aws'}
						<Card title={item.label} value="AWS" subtitle="Cost & Usage" icon="☁️" color="warning">
							{#snippet action()}
								<a class="shortcut-link" href="/aws-cost">Go</a>
							{/snippet}
						</Card>
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

	.header h1 {
		font-size: 1.5rem;
		font-weight: 700;
	}

	.btn-edit {
		padding: 0.5rem 1rem;
		background: #ffffff;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.9rem;
		transition: all 0.2s;
		color: #333;
		font-weight: 500;
	}

	.btn-edit:hover {
		background: #f0f0f0;
	}

	.controls-panel {
		background: var(--color-bg-secondary);
		padding: 1rem;
		border-radius: 8px;
		border: 1px solid var(--color-border);
		animation: slideDown 0.2s ease-out;
	}

	.settings-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.toggles {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
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

	.toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		cursor: pointer;
	}

	.grid-layout {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		grid-auto-rows: 180px;
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

	.stat-value {
		font-weight: 700;
		color: var(--color-text-primary);
	}

	.shortcut-link {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0.25rem 0.75rem;
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		border-radius: 99px;
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--color-text-secondary);
		text-decoration: none;
		transition: all 0.2s;
		white-space: nowrap;
	}

	.shortcut-link:hover {
		background: var(--color-primary);
		color: white;
		border-color: var(--color-primary);
		transform: translateY(-1px);
	}

	:global(.card-wrapper > .card) {
		height: 100%;
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
</style>
