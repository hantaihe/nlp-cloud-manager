<script lang="ts">
	import { onMount } from 'svelte';

	let credentials: any[] = $state([]);
	let activeName = $state('');
	let newCred = $state({
		name: '',
		project_id: '',
		service_account_json: ''
	});
	let isVisible = $state(false);
	let loading = $state(false);

	onMount(async () => {
		activeName = localStorage.getItem('gcp_active_name') || '';
		await fetchCredentials();
	});

	async function fetchCredentials() {
		loading = true;
		try {
			const res = await fetch('http://localhost:8002/credentials');
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
		if (!newCred.name || !newCred.project_id || !newCred.service_account_json) {
			alert('모든 필드를 입력해주세요.');
			return;
		}

		try {
			JSON.parse(newCred.service_account_json);
		} catch {
			alert('Service Account JSON이 올바른 JSON 형식이 아닙니다.');
			return;
		}

		try {
			const res = await fetch('http://localhost:8002/credentials', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newCred)
			});
			if (res.ok) {
				await fetchCredentials();
				selectCredential(newCred.name);
				newCred = { name: '', project_id: '', service_account_json: '' };
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
			const res = await fetch(`http://localhost:8002/credentials/${name}`, {
				method: 'DELETE'
			});
			if (res.ok) {
				await fetchCredentials();
				if (activeName === name) {
					activeName = credentials.length > 0 ? credentials[0].name : '';
					localStorage.setItem('gcp_active_name', activeName);
					window.location.reload();
				}
			}
		} catch (e) {
			alert('삭제 실패');
		}
	}

	function selectCredential(name: string) {
		activeName = name;
		localStorage.setItem('gcp_active_name', name);
		window.location.reload();
	}
</script>

<div class="credentials-manager">
	<button class="toggle-btn" onclick={() => (isVisible = !isVisible)}>
		{activeName ? `⚙️ GCP: ${activeName}` : '⚠️ GCP Setup Required'}
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
				<h3>GCP Credentials</h3>
				<p class="hint">GCP 서비스 계정 정보를 관리합니다.</p>

				<div class="cred-list">
					{#each credentials as cred}
						<div class="cred-item {activeName === cred.name ? 'active' : ''}">
							<div class="cred-info">
								<span class="cred-name">{cred.name}</span>
								<span class="cred-project">{cred.project_id}</span>
							</div>
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
					<label for="name">Label (e.g. MyProject)</label>
					<input id="name" type="text" bind:value={newCred.name} placeholder="Credential name" />
				</div>

				<div class="input-group">
					<label for="projectId">Project ID</label>
					<input
						id="projectId"
						type="text"
						bind:value={newCred.project_id}
						placeholder="GCP Project ID"
					/>
				</div>

				<div class="input-group">
					<label for="serviceAccountJson">Service Account JSON</label>
					<textarea
						id="serviceAccountJson"
						bind:value={newCred.service_account_json}
						placeholder="Paste Service Account JSON key content here"
						rows="6"
					></textarea>
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
		max-width: 500px;
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

	.cred-info {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}

	.cred-name {
		font-size: 0.9rem;
		font-weight: 500;
		color: var(--color-text-primary);
	}

	.cred-project {
		font-size: 0.7rem;
		color: var(--color-text-muted);
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
		cursor: pointer;
	}

	.del-btn {
		background: var(--color-danger-bg);
		color: var(--color-danger);
		border: none;
		padding: 0.2rem 0.5rem;
		font-size: 0.8rem;
		border-radius: 0.4rem;
		cursor: pointer;
	}

	.divider {
		height: 1px;
		background: var(--color-border);
		margin: 1.5rem 0;
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

	input,
	textarea {
		background: var(--color-bg-tertiary);
		border: 1px solid var(--color-border);
		color: var(--color-text-primary);
		padding: 0.5rem 0.8rem;
		border-radius: 0.6rem;
		outline: none;
		font-size: 0.85rem;
		font-family: inherit;
		resize: vertical;
	}

	input:focus,
	textarea:focus {
		border-color: var(--color-accent);
	}

	.save-btn {
		background: #34a853;
		border: none;
		color: #fff;
		width: 100%;
		padding: 0.7rem;
		border-radius: 0.8rem;
		cursor: pointer;
		font-weight: 700;
		margin-top: 1rem;
		transition: all 0.2s;
	}

	.save-btn:hover {
		background: #2d9249;
		transform: translateY(-2px);
	}
</style>
