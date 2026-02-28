<script lang="ts">
	import { onMount } from 'svelte';
	import { initThemeSync } from '../../../shared/theme/theme-sync';
	import '../../../shared/theme/theme.css';

	let serviceInfo = $state<{
		name: string;
		version: string;
		status: string;
		port: number;
		timestamp: string;
	} | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function fetchInfo() {
		loading = true;
		error = null;
		try {
			const response = await fetch('http://localhost:3001/info');
			if (!response.ok) throw new Error('fetch failed');
			serviceInfo = await response.json();
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchInfo();
		const cleanup = initThemeSync();
		return cleanup;
	});
</script>

<main class="container">
	<div class="card">
		<header class="card-header">
			<div class="status-indicator" class:active={serviceInfo?.status === 'healthy'}></div>
			<h1>Sample Service</h1>
		</header>

		{#if loading}
			<div class="loading">
				<div class="spinner"></div>
				<p>Connecting to backend...</p>
			</div>
		{:else if error}
			<div class="error-state">
				<span class="error-icon">⚠️</span>
				<p>{error}</p>
				<button onclick={fetchInfo} class="retry-btn">Retry Connection</button>
			</div>
		{:else if serviceInfo}
			<div class="info-grid">
				<div class="info-item">
					<div class="field-label">Service Name</div>
					<span>{serviceInfo.name}</span>
				</div>
				<div class="info-item">
					<div class="field-label">Status</div>
					<span class="status-tag success">{serviceInfo.status}</span>
				</div>
				<div class="info-item">
					<div class="field-label">Version</div>
					<span>v{serviceInfo.version}</span>
				</div>
				<div class="info-item">
					<div class="field-label">Port</div>
					<span>{serviceInfo.port}</span>
				</div>
				<div class="info-item full">
					<div class="field-label">Last Updated</div>
					<span>{new Date(serviceInfo.timestamp).toLocaleString()}</span>
				</div>
			</div>

			<div class="actions">
				<button onclick={fetchInfo} class="refresh-btn">
					<span>↻</span> Refresh Data
				</button>
			</div>
		{/if}
	</div>

	<footer class="footer">
		<p>Standalone Microservice Node • Internal Network</p>
	</footer>
</main>

<style>
	:global(:root) {
		--primary: var(--color-accent, #6366f1);
		--primary-hover: var(--color-accent-hover, #4f46e5);
		--bg-main: var(--color-bg-primary, #f8fafc);
		--bg-card: var(--color-bg-secondary, #ffffff);
		--text-main: var(--color-text-primary, #1e293b);
		--text-muted: var(--color-text-muted, #64748b);
		--border: var(--color-border, #e2e8f0);
		--success: var(--color-success, #10b981);
		--danger: var(--color-danger, #ef4444);
	}

	:global(body) {
		margin: 0;
		font-family:
			'Inter',
			system-ui,
			-apple-system,
			sans-serif;
		background-color: var(--bg-main);
		color: var(--text-main);
		transition:
			background-color 0.3s ease,
			color 0.3s ease;
	}

	.container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		padding: 2rem;
	}

	.card {
		background: var(--bg-card);
		border-radius: 12px;
		box-shadow:
			0 4px 6px -1px rgb(0 0 0 / 0.1),
			0 2px 4px -2px rgb(0 0 0 / 0.1);
		border: 1px solid var(--border);
		width: 100%;
		max-width: 480px;
		padding: 2rem;
	}

	.card-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 2rem;
		border-bottom: 1px solid var(--border);
		padding-bottom: 1rem;
	}

	.card-header h1 {
		font-size: 1.25rem;
		margin: 0;
		font-weight: 600;
	}

	.status-indicator {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background-color: var(--text-muted);
	}

	.status-indicator.active {
		background-color: var(--success);
		box-shadow: 0 0 8px var(--success);
	}

	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.info-item.full {
		grid-column: span 2;
	}

	.field-label {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--text-muted);
		font-weight: 600;
	}

	.info-item span {
		font-size: 0.9375rem;
		font-weight: 500;
	}

	.status-tag {
		display: inline-flex;
		padding: 0.125rem 0.625rem;
		border-radius: 99px;
		font-size: 0.75rem;
		font-weight: 600;
		width: fit-content;
	}

	.status-tag.success {
		background-color: #ecfdf5;
		color: var(--success);
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 2rem 0;
		color: var(--text-muted);
	}

	.spinner {
		width: 24px;
		height: 24px;
		border: 2px solid var(--border);
		border-top-color: var(--primary);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin-bottom: 1rem;
	}

	.error-state {
		text-align: center;
		padding: 1rem 0;
		color: var(--danger);
	}

	.error-icon {
		font-size: 2rem;
		display: block;
		margin-bottom: 0.5rem;
	}

	.retry-btn,
	.refresh-btn {
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		border: 1px solid var(--border);
	}

	.retry-btn {
		background-color: var(--danger);
		color: white;
		border: none;
		margin-top: 1rem;
	}

	.refresh-btn {
		background-color: var(--bg-main);
		color: var(--text-main);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.refresh-btn:hover {
		background-color: var(--border);
	}

	.footer {
		margin-top: 2rem;
		color: var(--text-muted);
		font-size: 0.75rem;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
