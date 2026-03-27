<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchGcpCredentials, updateGcpBillingAccount, type GcpCredential } from '$lib/api';

	let credentials = $state<GcpCredential[]>([]);
	let loading = $state(true);
	let saving = $state<string | null>(null);
	let saved = $state<string | null>(null);
	let error = $state<string | null>(null);

	let editValues = $state<Record<string, string>>({});

	onMount(async () => {
		credentials = await fetchGcpCredentials();
		credentials.forEach((c) => {
			editValues[c.name] = c.billing_account_id ?? '';
		});
		loading = false;
	});

	async function save(name: string) {
		saving = name;
		error = null;
		const ok = await updateGcpBillingAccount(name, editValues[name]);
		saving = null;
		if (ok) {
			saved = name;
			const cred = credentials.find((c) => c.name === name);
			if (cred) cred.billing_account_id = editValues[name] || null;
			setTimeout(() => (saved = null), 2000);
		} else {
			error = name;
		}
	}
</script>

<div class="settings-page">
	<div class="page-header">
		<h1>Settings</h1>
	</div>

	<section class="section">
		<div class="section-header">
			<img src="/icons/gcp.svg" alt="GCP" class="section-icon" />
			<div>
				<h2>GCP Credentials</h2>
				<p class="section-desc">
					Billing Account ID는 예산 조회에 사용됩니다. 서비스 계정에
					<code>billing.accounts.list</code> 권한이 없을 경우 직접 입력하세요.
				</p>
			</div>
		</div>

		{#if loading}
			<div class="placeholder animate-shimmer"></div>
		{:else if credentials.length === 0}
			<div class="empty">등록된 GCP 자격증명이 없습니다.</div>
		{:else}
			<div class="card-list">
				{#each credentials as cred (cred.name)}
					<div class="cred-card">
						<div class="cred-info">
							<span class="cred-name">{cred.name}</span>
							<span class="cred-project">{cred.project_id}</span>
						</div>

						<div class="field-row">
							<label for="billing-{cred.name}">Billing Account ID</label>
							<div class="input-group">
								<input
									id="billing-{cred.name}"
									type="text"
									placeholder="e.g. 01234A-56789B-CDEF01"
									bind:value={editValues[cred.name]}
									onkeydown={(e) => e.key === 'Enter' && save(cred.name)}
								/>
								<button
									class="btn-save"
									class:saving={saving === cred.name}
									disabled={saving === cred.name}
									onclick={() => save(cred.name)}
								>
									{#if saving === cred.name}
										저장 중…
									{:else if saved === cred.name}
										✓ 저장됨
									{:else}
										저장
									{/if}
								</button>
							</div>
							{#if error === cred.name}
								<span class="field-error">저장 실패. 다시 시도해주세요.</span>
							{/if}
							{#if cred.billing_account_id}
								<span class="field-hint">현재: {cred.billing_account_id}</span>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</section>
</div>

<style>
	.settings-page {
		max-width: 720px;
		padding: var(--spacing-xl);
	}

	.page-header {
		margin-bottom: var(--spacing-xl);
	}

	.page-header h1 {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--color-text-primary);
	}

	.section {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
	}

	.section-header {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-md);
		margin-bottom: var(--spacing-lg);
		padding-bottom: var(--spacing-md);
		border-bottom: 1px solid var(--color-border-subtle);
	}

	.section-icon {
		width: 28px;
		height: 28px;
		margin-top: 2px;
		flex-shrink: 0;
	}

	.section-header h2 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text-primary);
		margin-bottom: 4px;
	}

	.section-desc {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		line-height: 1.5;
	}

	.section-desc code {
		background: var(--color-bg-tertiary);
		padding: 1px 5px;
		border-radius: 4px;
		font-size: 0.75rem;
	}

	.placeholder {
		height: 80px;
		border-radius: var(--radius-md);
	}

	.empty {
		color: var(--color-text-muted);
		font-size: 0.875rem;
		text-align: center;
		padding: var(--spacing-lg);
	}

	.card-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.cred-card {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border-subtle);
		border-radius: var(--radius-md);
		padding: var(--spacing-md);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.cred-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.cred-name {
		font-weight: 600;
		font-size: 0.9rem;
		color: var(--color-text-primary);
	}

	.cred-project {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		background: var(--color-bg-tertiary);
		padding: 2px 8px;
		border-radius: var(--radius-full);
	}

	.field-row {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	label {
		font-size: 0.8rem;
		font-weight: 500;
		color: var(--color-text-secondary);
	}

	.input-group {
		display: flex;
		gap: var(--spacing-sm);
	}

	input {
		flex: 1;
		padding: 0.5rem 0.75rem;
		background: var(--color-bg-primary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		color: var(--color-text-primary);
		font-size: 0.875rem;
		font-family: inherit;
		transition: border-color 0.2s;
	}

	input:focus {
		outline: none;
		border-color: var(--color-accent);
	}

	input::placeholder {
		color: var(--color-text-subtle);
	}

	.btn-save {
		padding: 0.5rem 1rem;
		border-radius: var(--radius-sm);
		background: var(--color-accent);
		color: #fff;
		font-size: 0.85rem;
		font-weight: 500;
		transition: all 0.2s;
		white-space: nowrap;
		cursor: pointer;
	}

	.btn-save:hover:not(:disabled) {
		background: var(--color-accent-hover);
	}

	.btn-save:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-save.saving {
		background: var(--color-text-muted);
	}

	.field-hint {
		font-size: 0.75rem;
		color: var(--color-text-muted);
	}

	.field-error {
		font-size: 0.75rem;
		color: var(--color-danger);
	}
</style>
