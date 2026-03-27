<script lang="ts">
	interface LogEntry {
		log_name?: string;
		severity?: string;
		timestamp?: string;
		resource_type?: string;
		payload?: string;
	}

	interface Props {
		logs: LogEntry[];
	}

	let { logs = [] }: Props = $props();

	function formatPayload(payload?: string) {
		if (!payload) return '';
		try {
			if (payload.startsWith('{')) {
				return payload;
			}
			return payload;
		} catch {
			return payload;
		}
	}
</script>

<div class="logging-container glass">
	<h3>Recent Logs</h3>
	<div class="logs-grid">
		{#if logs.length === 0}
			<p class="empty">조회된 로그 데이터가 없습니다.</p>
		{:else}
			{#each logs as log}
				<div class="log-card">
					<div class="log-header">
						<span
							class="severity"
							class:error={log.severity === 'ERROR'}
							class:warning={log.severity === 'WARNING'}
							class:info={log.severity === 'INFO'}
						>
							{log.severity || 'DEFAULT'}
						</span>
						<span class="timestamp">{new Date(log.timestamp || '').toLocaleString()}</span>
					</div>
					<div class="log-meta">
						<span class="log-name" title={log.log_name}
							>{log.log_name?.split('/').pop() || 'Unknown'}</span
						>
						<span class="resource-type">{log.resource_type}</span>
					</div>
					<div class="log-payload">
						{formatPayload(log.payload)}
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>

<style>
	.logging-container {
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

	.logs-grid {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		max-height: 600px;
		overflow-y: auto;
	}

	.log-card {
		padding: 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.8rem;
		border: 1px solid var(--color-border-subtle);
		transition: all 0.2s;
	}

	.log-card:hover {
		border-color: var(--color-accent);
	}

	.log-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.6rem;
	}

	.severity {
		padding: 0.2rem 0.5rem;
		border-radius: 0.4rem;
		font-size: 0.65rem;
		font-weight: 800;
		background: rgba(158, 158, 158, 0.15);
		color: #9e9e9e;
	}
	.severity.info {
		background: rgba(66, 133, 244, 0.15);
		color: #4285f4;
	}
	.severity.warning {
		background: rgba(251, 188, 4, 0.15);
		color: #fbbc04;
	}
	.severity.error {
		background: rgba(234, 67, 53, 0.15);
		color: #ea4335;
	}

	.timestamp {
		font-size: 0.75rem;
		color: var(--color-text-muted);
	}

	.log-meta {
		display: flex;
		gap: 0.8rem;
		margin-bottom: 0.8rem;
		font-size: 0.8rem;
		align-items: center;
	}
	.log-name {
		color: #34a853;
		font-weight: 600;
	}
	.resource-type {
		color: var(--color-text-subtle);
		background: var(--color-bg-tertiary);
		padding: 0.1rem 0.4rem;
		border-radius: 0.3rem;
		font-size: 0.7rem;
	}

	.log-payload {
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 0.75rem;
		color: var(--color-text-primary);
		background: rgba(0, 0, 0, 0.2);
		padding: 0.8rem;
		border-radius: 0.4rem;
		overflow-x: auto;
		white-space: pre-wrap;
		word-break: break-all;
	}

	.empty {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-subtle);
	}
</style>
