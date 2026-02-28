<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Column<T> {
		key: keyof T | string;
		label: string;
		width?: string;
		align?: 'left' | 'center' | 'right';
	}

	interface Props<T> {
		columns: Column<T>[];
		data: T[];
		title?: string;
		emptyMessage?: string;
		row?: Snippet<[T, number]>;
	}

	let {
		columns,
		data,
		title = '',
		emptyMessage = 'No data available',
		row
	}: Props<Record<string, any>> = $props();

	let sortColumn = $state<string | null>(null);
	let sortDirection = $state<'asc' | 'desc'>('asc');

	function handleSort(column: string) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'asc';
		}
	}

	const sortedData = $derived(() => {
		if (!sortColumn) return data;
		return [...data].sort((a, b) => {
			const aVal = a[sortColumn as string];
			const bVal = b[sortColumn as string];
			const modifier = sortDirection === 'asc' ? 1 : -1;

			if (typeof aVal === 'string') {
				return aVal.localeCompare(bVal) * modifier;
			}
			return (aVal - bVal) * modifier;
		});
	});
</script>

<div class="table-container">
	{#if title}
		<div class="table-header">
			<h3 class="table-title">{title}</h3>
		</div>
	{/if}

	<div class="table-wrapper">
		<table class="table">
			<thead>
				<tr>
					{#each columns as column (column.key)}
						<th
							class="table-th"
							style:width={column.width}
							style:text-align={column.align ?? 'left'}
						>
							<button class="sort-btn" onclick={() => handleSort(column.key as string)}>
								{column.label}
								{#if sortColumn === column.key}
									<span class="sort-indicator">
										{sortDirection === 'asc' ? '↑' : '↓'}
									</span>
								{/if}
							</button>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#if data.length === 0}
					<tr>
						<td colspan={columns.length} class="empty-cell">
							{emptyMessage}
						</td>
					</tr>
				{:else}
					{#each sortedData() as item, index (index)}
						{#if row}
							{@render row(item, index)}
						{:else}
							<tr class="table-row">
								{#each columns as column (column.key)}
									<td class="table-td" style:text-align={column.align ?? 'left'}>
										{item[column.key as string] ?? '-'}
									</td>
								{/each}
							</tr>
						{/if}
					{/each}
				{/if}
			</tbody>
		</table>
	</div>
</div>

<style>
	.table-container {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.table-header {
		padding: var(--spacing-lg);
		border-bottom: 1px solid var(--color-border);
	}

	.table-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text-primary);
	}

	.table-wrapper {
		overflow-x: auto;
	}

	.table {
		width: 100%;
		border-collapse: collapse;
	}

	.table-th {
		padding: var(--spacing-md) var(--spacing-lg);
		background: var(--color-bg-tertiary);
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid var(--color-border);
	}

	.sort-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-xs);
		color: inherit;
		font-size: inherit;
		font-weight: inherit;
		text-transform: inherit;
		letter-spacing: inherit;
	}

	.sort-btn:hover {
		color: var(--color-text-primary);
	}

	.sort-indicator {
		color: var(--color-accent);
	}

	.table-row {
		transition: background var(--transition-fast);
	}

	.table-row:hover {
		background: var(--color-bg-hover);
	}

	.table-td {
		padding: var(--spacing-md) var(--spacing-lg);
		font-size: 0.875rem;
		color: var(--color-text-secondary);
		border-bottom: 1px solid var(--color-border);
	}

	.table-row:last-child .table-td {
		border-bottom: none;
	}

	.empty-cell {
		padding: var(--spacing-xl);
		text-align: center;
		color: var(--color-text-muted);
		font-style: italic;
	}
</style>
