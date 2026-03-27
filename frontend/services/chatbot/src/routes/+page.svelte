<script lang="ts">
	import { onMount } from 'svelte';

	const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

	type Message = { role: 'user' | 'assistant' | 'thinking'; content: string };

	let messages = $state<Message[]>([]);
	let input = $state('');
	let isLoading = $state(false);
	let chatContainer = $state<HTMLDivElement | null>(null);

	let awsCred = $state('');
	let azureCred = $state('');
	let gcpCred = $state('');
	let theme = $state('dark');

	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		awsCred = urlParams.get('aws') || '';
		azureCred = urlParams.get('azure') || '';
		gcpCred = urlParams.get('gcp') || '';
		theme = urlParams.get('theme') || 'dark';

		document.documentElement.setAttribute('data-theme', theme);

		const handleMessage = (event: MessageEvent) => {
			if (event.data.type === 'THEME_UPDATE') {
				theme = event.data.theme;
				document.documentElement.setAttribute('data-theme', theme);
			}
		};
		window.addEventListener('message', handleMessage);
		return () => window.removeEventListener('message', handleMessage);
	});

	function scrollToBottom() {
		setTimeout(() => {
			if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
		}, 0);
	}

	async function sendMessage() {
		if (!input.trim() || isLoading) return;

		const userMessage = input;
		messages.push({ role: 'user', content: userMessage });
		input = '';
		isLoading = true;
		scrollToBottom();

		// Insert placeholder thinking message
		messages.push({ role: 'thinking', content: '' });
		const thinkingIdx = messages.length - 1;
		let hasThinking = false;
		let responseIdx = -1;

		try {
			const response = await fetch(`${API_BASE}/chat/stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					message: userMessage,
					session_id: 'default',
					config: {
						aws_credential_name: awsCred,
						azure_credential_name: azureCred,
						gcp_credential_name: gcpCred
					}
				})
			});

			if (!response.ok) throw new Error('Failed to fetch response');

			const reader = response.body!.getReader();
			const decoder = new TextDecoder();

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const text = decoder.decode(value, { stream: true });
				const lines = text.split('\n').filter((l) => l.trim());

				for (const line of lines) {
					try {
						const event = JSON.parse(line);

						if (event.type === 'thinking') {
							hasThinking = true;
							messages[thinkingIdx].content += event.token;
							scrollToBottom();
						} else if (event.type === 'thinking_done') {
							// thinking stream finished — keep showing until response is ready
						} else if (event.type === 'token') {
							isLoading = false;
							if (responseIdx === -1) {
								messages.push({ role: 'assistant', content: event.token });
								responseIdx = messages.length - 1;
							} else {
								messages[responseIdx].content += event.token;
							}
							scrollToBottom();
						} else if (event.type === 'done') {
							// Remove the thinking message — only keep final response
							messages.splice(thinkingIdx, 1);
							scrollToBottom();
						} else if (event.type === 'error') {
							messages.splice(thinkingIdx, 1);
							messages.push({ role: 'assistant', content: `오류가 발생했습니다:\n${event.error}` });
						}
					} catch {
						// ignore malformed lines
					}
				}
			}
		} catch (error) {
			console.error('Chat error:', error);
			messages.splice(thinkingIdx, 1);
			messages.push({
				role: 'assistant',
				content: '죄송합니다. 오류가 발생했습니다. 나중에 다시 시도해주세요.'
			});
		} finally {
			isLoading = false;
			scrollToBottom();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}
</script>

<div class="chat-main" class:dark={theme === 'dark'}>
	<div class="messages-container" bind:this={chatContainer}>
		{#each messages as msg}
			{#if msg.role === 'thinking'}
				<div class="message-wrapper thinking-wrapper">
					<div class="thinking-bubble">
						<span class="thinking-label">
							<span class="thinking-dots">
								<span></span><span></span><span></span>
							</span>
							생각 중...
						</span>
						<div class="thinking-content">{msg.content}</div>
					</div>
				</div>
			{:else}
				<div class="message-wrapper" class:user={msg.role === 'user'}>
					<div class="message">
						{msg.content}
					</div>
				</div>
			{/if}
		{/each}
		{#if isLoading}
			<div class="message-wrapper">
				<div class="message loading">
					<div class="dot"></div>
					<div class="dot"></div>
					<div class="dot"></div>
				</div>
			</div>
		{/if}
	</div>

	<div class="input-area">
		<textarea
			bind:value={input}
			onkeydown={handleKeydown}
			placeholder="AI에게 무엇이든 물어보세요..."
			rows="1"
		></textarea>
		<button onclick={sendMessage} disabled={isLoading || !input.trim()} aria-label="Send message">
			<svg
				width="20"
				height="20"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg
			>
		</button>
	</div>
</div>

<style>
	:global(html, body) {
		margin: 0;
		padding: 0;
		height: 100%;
		background: transparent !important;
	}

	.chat-main {
		display: flex;
		flex-direction: column;
		height: 100vh;
		background: var(--color-bg-card, #fff);
		color: var(--color-text-primary, #111);
		font-family: 'Inter', sans-serif;
	}

	.chat-main.dark {
		--color-bg-card: #1a1b1e;
		--color-text-primary: #e4e6eb;
		--color-border: #2f3037;
		--color-purple: #a855f7;
		--color-bg-tertiary: #25262b;
		--color-thinking-bg: #1e1a2e;
		--color-thinking-border: #4a3570;
		--color-thinking-text: #b09cd8;
	}

	.chat-main:not(.dark) {
		--color-thinking-bg: #f5f0ff;
		--color-thinking-border: #d4b8ff;
		--color-thinking-text: #6b4fa0;
	}

	.messages-container {
		flex: 1;
		overflow-y: auto;
		padding: 20px;
		display: flex;
		flex-direction: column;
		gap: 15px;
	}

	.messages-container::-webkit-scrollbar {
		width: 6px;
	}

	.messages-container::-webkit-scrollbar-track {
		background: transparent;
	}

	.messages-container::-webkit-scrollbar-thumb {
		background: var(--color-border);
		border-radius: 3px;
	}

	.messages-container::-webkit-scrollbar-thumb:hover {
		background: var(--color-purple);
	}

	.message-wrapper {
		display: flex;
		flex-direction: column;
	}

	.message-wrapper.user {
		align-items: flex-end;
	}

	.message {
		max-width: 85%;
		padding: 12px 16px;
		border-radius: 18px;
		font-size: 0.95rem;
		line-height: 1.5;
		white-space: pre-wrap;
	}

	.message-wrapper.user .message {
		background: #a855f7;
		color: white;
		border-bottom-right-radius: 4px;
	}

	.message-wrapper:not(.user) .message {
		background: var(--color-bg-tertiary, #f1f3f5);
		color: var(--color-text-primary);
		border-bottom-left-radius: 4px;
	}

	/* ── Thinking bubble ─────────────────────────────────── */
	.thinking-wrapper {
		align-items: flex-start;
	}

	.thinking-bubble {
		max-width: 90%;
		background: var(--color-thinking-bg, #f5f0ff);
		border: 1px dashed var(--color-thinking-border, #d4b8ff);
		border-radius: 14px;
		padding: 10px 14px;
		font-size: 0.82rem;
		line-height: 1.5;
		color: var(--color-thinking-text, #6b4fa0);
	}

	.thinking-label {
		display: flex;
		align-items: center;
		gap: 6px;
		font-weight: 600;
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 6px;
		opacity: 0.8;
	}

	.thinking-content {
		white-space: pre-wrap;
		word-break: break-word;
		opacity: 0.85;
		font-style: italic;
		max-height: 180px;
		overflow-y: auto;
	}

	.thinking-content::-webkit-scrollbar {
		width: 4px;
	}
	.thinking-content::-webkit-scrollbar-thumb {
		background: var(--color-thinking-border);
		border-radius: 2px;
	}

	/* Animated thinking dots */
	.thinking-dots {
		display: inline-flex;
		gap: 3px;
		align-items: center;
	}

	.thinking-dots span {
		width: 5px;
		height: 5px;
		background: var(--color-thinking-text, #6b4fa0);
		border-radius: 50%;
		animation: thinking-bounce 1.2s infinite ease-in-out both;
	}

	.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
	.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }
	.thinking-dots span:nth-child(3) { animation-delay: 0s; }

	@keyframes thinking-bounce {
		0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
		40% { transform: scale(1); opacity: 1; }
	}

	/* ── Input area ──────────────────────────────────────── */
	.input-area {
		padding: 20px;
		border-top: 1px solid var(--color-border, #eee);
		display: flex;
		gap: 10px;
		align-items: flex-end;
		background: var(--color-bg-card);
	}

	textarea {
		flex: 1;
		background: var(--color-bg-tertiary, #f8f9fa);
		border: 1px solid var(--color-border, #eee);
		border-radius: 12px;
		padding: 12px 15px;
		color: var(--color-text-primary);
		font-family: inherit;
		font-size: 0.95rem;
		resize: none;
		outline: none;
		transition: border-color 0.2s;
	}

	textarea:focus {
		border-color: #a855f7;
	}

	button {
		width: 45px;
		height: 45px;
		border-radius: 12px;
		background: #a855f7;
		color: white;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	button:hover:not(:disabled) {
		background: #9333ea;
		transform: translateY(-2px);
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.loading {
		display: flex;
		gap: 4px;
		padding: 15px 20px !important;
	}

	.dot {
		width: 6px;
		height: 6px;
		background: currentColor;
		border-radius: 50%;
		opacity: 0.5;
		animation: bounce 1.4s infinite ease-in-out both;
	}

	.dot:nth-child(1) { animation-delay: -0.32s; }
	.dot:nth-child(2) { animation-delay: -0.16s; }

	@keyframes bounce {
		0%, 80%, 100% { transform: scale(0); }
		40% { transform: scale(1); }
	}
</style>
