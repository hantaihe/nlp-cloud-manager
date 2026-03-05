<script lang="ts">
	import { onMount } from 'svelte';

	let credentials: any[] = $state([]);
	let activeName = $state('');
	let newCred = $state({
		name: '',
		tenant_id: '',
		client_id: '',
		client_secret: '',
		subscription_id: ''
	});
	let isVisible = $state(false);
	let loading = $state(false);

	onMount(async () => {
		activeName = localStorage.getItem('azure_active_name') || '';
		await fetchCredentials();
	});

	async function fetchCredentials() {
		loading = true;
		try {
			const res = await fetch('http://localhost:8001/credentials');
			if (res.ok) {
				credentials = await res.json();
				if (!activeName || !credentials.find((c) => c.name === activeName)) {
					if (credentials.length > 0) {
						selectCredential(credentials[0].name);
					}
				}
			}
		} catch (e) {
			console.error('Error fetchCredentials:', e);
		} finally {
			loading = false;
		}
	}

	async function saveCredential() {
		if (
			!newCred.name ||
			!newCred.tenant_id ||
			!newCred.client_id ||
			!newCred.client_secret ||
			!newCred.subscription_id
		) {
			alert('모든 필드를 입력해주세요.');
			return;
		}

		try {
			const res = await fetch('http://localhost:8001/credentials', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newCred)
			});
			if (res.ok) {
				await fetchCredentials();
				selectCredential(newCred.name);
				newCred = {
					name: '',
					tenant_id: '',
					client_id: '',
					client_secret: '',
					subscription_id: ''
				};
			} else {
				alert('저장 실패');
			}
		} catch (e) {
			alert('저장 실패');
		}
	}

	async function deleteCredential(name: string) {
		if (!confirm(`Delete credential "${name}"?`)) return;

		try {
			const res = await fetch(`http://localhost:8001/credentials/${name}`, {
				method: 'DELETE'
			});
			if (res.ok) {
				await fetchCredentials();
				if (activeName === name) {
					activeName = credentials.length > 0 ? credentials[0].name : '';
					localStorage.setItem('azure_active_name', activeName);
					window.location.reload();
				}
			}
		} catch (e) {
			alert('삭제 실패');
		}
	}

	function selectCredential(name: string) {
		activeName = name;
		localStorage.setItem('azure_active_name', name);
		window.location.reload();
	}
</script>

<div class="credentials-manager">
	<button class="toggle-btn" onclick={() => (isVisible = !isVisible)}>
		{activeName ? `⚙️ Azure: ${activeName}` : '⚠️ Azure Setup Required'}
	</button>

	{#if isVisible}
		<div
			class="modal-overlay"
			onclick={() => (isVisible = false)}
			onkeydown={(e) => e.key === 'Escape' && (isVisible = false)}
			role="button"
			tabindex="0"
		>
			<div class="modal glass" onclick={(e) => e.stopPropagation()} role="dialog" tabindex="0">
				<h3>Azure Credentials</h3>
				<p class="hint">Azure 자격 증명 정보를 관리합니다.</p>

				<div class="cred-list">
					{#each credentials as cred}
						<div class="cred-item {activeName === cred.name ? 'active' : ''}">
							<span class="cred-name">{cred.name}</span>
							<div class="item-actions">
								<button class="select-btn" onclick={() => selectCredential(cred.name)}
									>Select</button
								>
								<button class="del-btn" onclick={() => deleteCredential(cred.name)}>×</button>
							</div>
						</div>
					{/each}
				</div>

				<div class="divider"></div>

				<h4>Add New Credential</h4>
				<div class="input-group">
					<label for="name">Label (e.g. MyAccount)</label>
					<input id="name" type="text" bind:value={newCred.name} placeholder="Account name" />
				</div>

				<div class="input-row">
					<div class="input-group">
						<label for="tenantId">Tenant ID</label>
						<input
							id="tenantId"
							type="text"
							bind:value={newCred.tenant_id}
							placeholder="Azure Tenant ID"
						/>
					</div>
					<div class="input-group">
						<label for="clientId">Client ID</label>
						<input
							id="clientId"
							type="text"
							bind:value={newCred.client_id}
							placeholder="Azure Client ID"
						/>
					</div>
				</div>

				<div class="input-row">
					<div class="input-group">
						<label for="clientSecret">Client Secret</label>
						<input
							id="clientSecret"
							type="password"
							bind:value={newCred.client_secret}
							placeholder="Azure Client Secret"
						/>
					</div>
					<div class="input-group">
						<label for="subscriptionId">Subscription ID</label>
						<input
							id="subscriptionId"
							type="text"
							bind:value={newCred.subscription_id}
							placeholder="Azure Subscription ID"
						/>
					</div>
				</div>

				<button class="save-btn" onclick={saveCredential}>Save Credential</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.credentials-manager {
		display: inline-block;
		z-index: 100;
	}

	.toggle-btn {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		color: var(--color-text-primary);
		padding: 0.6rem 1.2rem;
		border-radius: 0.8rem;
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.toggle-btn:hover {
		background: var(--color-bg-hover);
		border-color: var(--color-accent);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}

	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.4);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal {
		width: 90%;
		max-width: 450px;
		max-height: 90vh;
		overflow-y: auto;
		padding: 2rem;
		border-radius: 1.5rem;
		border: 1px solid var(--color-border);
	}

	.glass {
		background: var(--color-bg-elevated);
		backdrop-filter: blur(20px);
		-webkit-backdrop-filter: blur(20px);
		box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
	}

	h3,
	h4 {
		margin: 0 0 0.5rem 0;
		color: var(--color-text-primary);
	}

	h4 {
		font-size: 0.9rem;
		margin-top: 1rem;
		color: var(--color-text-secondary);
	}

	.hint {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		margin-bottom: 1rem;
	}

	.cred-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-height: 200px;
		overflow-y: auto;
		margin-bottom: 1rem;
	}

	.cred-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.6rem 1rem;
		background: var(--color-bg-secondary);
		border-radius: 0.8rem;
		border: 1px solid transparent;
	}

	.cred-item.active {
		border-color: var(--color-accent);
		background: var(--color-accent-subtle);
	}

	.cred-name {
		font-size: 0.9rem;
		font-weight: 500;
		color: var(--color-text-primary);
	}

	.item-actions {
		display: flex;
		gap: 0.5rem;
	}

	.select-btn {
		background: var(--color-accent);
		color: #fff;
		border: none;
		padding: 0.2rem 0.6rem;
		font-size: 0.7rem;
		border-radius: 0.4rem;
	}

	.del-btn {
		background: var(--color-danger-bg);
		color: var(--color-danger);
		border: none;
		padding: 0.2rem 0.5rem;
		font-size: 0.8rem;
		border-radius: 0.4rem;
	}

	.divider {
		height: 1px;
		background: var(--color-border);
		margin: 1.5rem 0;
	}

	.input-row {
		display: flex;
		gap: 1rem;
	}

	.input-group {
		margin-bottom: 1rem;
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: 0.4rem;
	}

	label {
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
	}

	input {
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		color: var(--color-text-primary);
		padding: 0.5rem 0.8rem;
		border-radius: 0.6rem;
		outline: none;
		font-size: 0.85rem;
	}

	input:focus {
		border-color: var(--color-accent);
	}

	.save-btn {
		background: #ffd700;
		border: none;
		color: #000;
		width: 100%;
		padding: 0.7rem;
		border-radius: 0.8rem;
		cursor: pointer;
		font-weight: 700;
		margin-top: 1rem;
		transition: all 0.2s;
	}

	.save-btn:hover {
		background: #fff;
		transform: translateY(-2px);
	}
</style>
