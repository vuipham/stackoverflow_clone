<script lang="ts">
	import { login, ApiError } from '$lib/api/client';
	import { setSession } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	const TEST_ACCOUNTS = [
		{ username: 'newbie', reputation: 1 },
		{ username: 'voter', reputation: 20 },
		{ username: 'commenter', reputation: 60 },
		{ username: 'critic', reputation: 130 },
		{ username: 'editor', reputation: 600 },
		{ username: 'veteran', reputation: 2200 },
		{ username: 'admin', reputation: 1, tag: 'Admin' }
	];

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const { token, user } = await login({ username, password });
			setSession(token, user);
			goto('/questions');
		} catch (err) {
			error = err instanceof ApiError ? String(err.detail) : 'Đăng nhập thất bại';
		} finally {
			loading = false;
		}
	}

	function fillTestAccount(u: string) {
		username = u;
		password = 'Test@123';
	}
</script>

<h1>Đăng nhập</h1>

<form onsubmit={handleSubmit}>
	<label>
		Username
		<input bind:value={username} required />
	</label>
	<label>
		Mật khẩu
		<input type="password" bind:value={password} required />
	</label>

	{#if error}<p class="error">{error}</p>{/if}

	<button type="submit" disabled={loading}>{loading ? 'Đang xử lý...' : 'Đăng nhập'}</button>
</form>

<p class="switch">Chưa có tài khoản? <a href="/register">Đăng ký</a></p>

<div class="test-accounts">
	<p class="hint">
		Tài khoản test có sẵn sau khi chạy <code>python -m app.seed</code>
		(mật khẩu chung: <code>Test@123</code>) — bấm để điền nhanh:
	</p>
	<div class="chips">
		{#each TEST_ACCOUNTS as acc}
			<button type="button" class="chip" onclick={() => fillTestAccount(acc.username)}>
				{acc.username} · {acc.reputation} rep{acc.tag ? ` · ${acc.tag}` : ''}
			</button>
		{/each}
	</div>
</div>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
		max-width: 380px;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.9rem;
		color: #3b4759;
	}
	input {
		padding: 0.55rem 0.7rem;
		border: 1px solid #d0d5dd;
		border-radius: 6px;
		font-size: 0.95rem;
	}
	button[type='submit'] {
		padding: 0.65rem;
		border: none;
		border-radius: 6px;
		background: #0074cc;
		color: white;
		font-weight: 600;
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.error {
		color: #d63384;
		font-size: 0.85rem;
	}
	.switch {
		margin-top: 1rem;
		font-size: 0.9rem;
	}
	.test-accounts {
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px dashed #d0d5dd;
		max-width: 500px;
	}
	.hint {
		font-size: 0.82rem;
		color: #8a94a3;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	.chip {
		font-size: 0.8rem;
		background: #f0f5fb;
		border: 1px solid #d6e4f5;
		border-radius: 999px;
		padding: 0.3rem 0.8rem;
		cursor: pointer;
	}
	.chip:hover {
		background: #e1edfa;
	}
</style>
