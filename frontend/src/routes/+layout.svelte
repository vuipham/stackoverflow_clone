<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { currentUser, authReady, restoreSession, clearSession } from '$lib/stores/auth';

	let { children } = $props();

	onMount(() => {
		restoreSession();
	});

	function handleLogout() {
		clearSession();
		window.location.href = '/';
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app-shell">
	<header>
		<a href="/" class="brand">📚 Knowledge Hub</a>
		<nav>
			<a href="/questions">Câu hỏi</a>
			<a href="/search">🔍 Tìm kiếm</a>
			{#if $currentUser}
				<a href="/ask">Đặt câu hỏi</a>
			{/if}
			{#if $currentUser?.isAdmin}
				<a href="/admin">Quản trị</a>
			{/if}
		</nav>
		<div class="auth-area">
			{#if !$authReady}
				<span class="muted">Đang tải...</span>
			{:else if $currentUser}
				<span class="rep-badge" title="Điểm reputation">
					{$currentUser.displayName} · {$currentUser.reputation} rep
					{#if $currentUser.isAdmin}<span class="admin-tag">Admin</span>{/if}
				</span>
				<button onclick={handleLogout}>Đăng xuất</button>
			{:else}
				<a href="/login">Đăng nhập</a>
				<a href="/register">Đăng ký</a>
			{/if}
		</div>
	</header>

	<main>
		{@render children()}
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family:
			system-ui,
			-apple-system,
			'Segoe UI',
			sans-serif;
		background: #f8f9fa;
		color: #1a1a2e;
	}

	.app-shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	header {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 0.75rem 1.5rem;
		background: white;
		border-bottom: 1px solid #e2e5e9;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.brand {
		font-weight: 700;
		text-decoration: none;
		color: #1a1a2e;
		font-size: 1.1rem;
	}

	nav {
		display: flex;
		gap: 1rem;
		flex: 1;
	}

	nav a {
		text-decoration: none;
		color: #3b4759;
		font-size: 0.95rem;
	}

	nav a:hover {
		color: #0074cc;
	}

	.auth-area {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.9rem;
	}

	.auth-area a {
		text-decoration: none;
		color: #0074cc;
	}

	.rep-badge {
		background: #f0f5fb;
		padding: 0.3rem 0.7rem;
		border-radius: 6px;
		font-weight: 500;
	}

	.admin-tag {
		background: #d63384;
		color: white;
		font-size: 0.7rem;
		padding: 0.1rem 0.4rem;
		border-radius: 4px;
		margin-left: 0.4rem;
	}

	.muted {
		color: #8a94a3;
	}

	button {
		background: none;
		border: 1px solid #d0d5dd;
		border-radius: 6px;
		padding: 0.35rem 0.7rem;
		cursor: pointer;
		font-size: 0.85rem;
	}

	button:hover {
		background: #f2f4f7;
	}

	main {
		flex: 1;
		max-width: 900px;
		width: 100%;
		margin: 0 auto;
		padding: 1.5rem;
		box-sizing: border-box;
	}
</style>
