<script lang="ts">
	import { register, ApiError } from '$lib/api/client';
	import { setSession } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let username = $state('');
	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const { token, user } = await register({ username, email, password, displayName });
			setSession(token, user);
			goto('/questions');
		} catch (err) {
			error = err instanceof ApiError ? String(err.detail) : 'Đăng ký thất bại';
		} finally {
			loading = false;
		}
	}
</script>

<h1>Đăng ký tài khoản</h1>
<p class="note">Reputation mặc định khi tạo tài khoản mới là <strong>1 điểm</strong> — đúng như cơ chế thật của Stack Overflow.</p>

<form onsubmit={handleSubmit}>
	<label>
		Username
		<input bind:value={username} required minlength="3" />
	</label>
	<label>
		Email
		<input type="email" bind:value={email} required />
	</label>
	<label>
		Tên hiển thị (tuỳ chọn)
		<input bind:value={displayName} />
	</label>
	<label>
		Mật khẩu
		<input type="password" bind:value={password} required minlength="6" />
	</label>

	{#if error}<p class="error">{error}</p>{/if}

	<button type="submit" disabled={loading}>{loading ? 'Đang xử lý...' : 'Đăng ký'}</button>
</form>

<p class="switch">Đã có tài khoản? <a href="/login">Đăng nhập</a></p>

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
	button {
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
	.note {
		color: #5b6673;
		font-size: 0.9rem;
		max-width: 380px;
	}
	.switch {
		margin-top: 1rem;
		font-size: 0.9rem;
	}
</style>
