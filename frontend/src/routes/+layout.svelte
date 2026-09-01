<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { currentUser, authReady, restoreSession, clearSession } from '$lib/stores/auth';

	let { children } = $props();
	let searchQuery = $state('');

	onMount(() => {
		restoreSession();
	});

	function handleLogout() {
		clearSession();
		window.location.href = '/';
	}

	function handleHeaderSearch(e: Event) {
		e.preventDefault();
		if (!searchQuery.trim()) return;
		goto(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
		searchQuery = '';
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Knowledge Hub - Stack Overflow Clone</title>
</svelte:head>

<div class="app-shell">
	<header class="so-header">
		<a href="/" class="brand">
			<svg class="so-logo-icon" viewBox="0 0 32 37" width="24" height="24">
				<path fill="#BCBBBB" d="M26 33v-9h4v13H0V24h4v9h22Z"/>
				<path fill="#F48024" d="m21.5 0-2.7 2 9.9 13.3 2.7-2L21.5 0ZM26 18.4l-12-6.8 1.9-3.4 12 6.8-1.9 3.4ZM10.7 22.8l13.5-3.6.9 3.4-13.5 3.6-.9-3.4ZM8 28.5h14v4H8v-4Z"/>
			</svg>
			<span class="brand-name">Stack<b>Overflow</b> <small class="brand-sub">Clone</small></span>
		</a>

		<nav class="nav-links">
			<a href="/questions">Câu hỏi</a>
			<a href="/search">Tìm kiếm</a>
			{#if $currentUser?.isAdmin}
				<a href="/admin" class="admin-link">Quản trị</a>
			{/if}
		</nav>

		<!-- Thanh tìm kiếm toàn cục (Global Search Bar) -->
		<form onsubmit={handleHeaderSearch} class="header-search-form">
			<span class="search-icon">🔍</span>
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Tìm kiếm câu hỏi (nhập từ khóa...)"
			/>
		</form>

		<div class="auth-area">
			{#if !$authReady}
				<span class="muted">Đang tải...</span>
			{:else if $currentUser}
				<a href="/ask" class="btn-ask-sm">Đặt câu hỏi</a>
				<a href="/profile" class="rep-badge" title="Xem hồ sơ cá nhân">
					<span class="avatar-circle">{$currentUser.displayName.charAt(0).toUpperCase()}</span>
					<span class="user-name">{$currentUser.displayName}</span>
					<span class="rep-num">{$currentUser.reputation.toLocaleString('vi-VN')} rep</span>
					{#if $currentUser.isAdmin}<span class="admin-tag">Admin</span>{/if}
				</a>
				<button class="btn-logout" onclick={handleLogout}>Đăng xuất</button>
			{:else}
				<a href="/login" class="btn-login">Đăng nhập</a>
				<a href="/register" class="btn-signup">Đăng ký</a>
			{/if}
		</div>
	</header>

	<div class="main-wrapper">
		<main>
			{@render children()}
		</main>
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
		background: #f8f9fa;
		color: #232629;
	}

	.app-shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	/* Header chuẩn Stack Overflow */
	.so-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.5rem 1.5rem;
		background: white;
		border-top: 3px solid #f48225;
		border-bottom: 1px solid #d6d9dc;
		position: sticky;
		top: 0;
		z-index: 100;
		box-shadow: 0 1px 2px rgba(0,0,0,0.05);
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		text-decoration: none;
		color: #0c0d0e;
	}

	.brand-name {
		font-size: 1.1rem;
		letter-spacing: -0.3px;
	}

	.brand-name b {
		font-weight: 700;
	}

	.brand-sub {
		font-size: 0.75rem;
		color: #6a737c;
		background: #e1ecf4;
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
		margin-left: 0.2rem;
	}

	.nav-links {
		display: flex;
		gap: 0.8rem;
	}

	.nav-links a {
		text-decoration: none;
		color: #525960;
		font-size: 0.88rem;
		padding: 0.3rem 0.6rem;
		border-radius: 999px;
		transition: all 0.15s;
	}

	.nav-links a:hover {
		background: #e3e6e8;
		color: #0c0d0e;
	}

	.nav-links a.admin-link {
		color: #d63384;
		font-weight: 600;
	}

	/* Global Search Bar */
	.header-search-form {
		flex: 1;
		position: relative;
		max-width: 600px;
	}

	.search-icon {
		position: absolute;
		left: 0.7rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.85rem;
		color: #838c95;
		pointer-events: none;
	}

	.header-search-form input {
		width: 100%;
		padding: 0.45rem 0.8rem 0.45rem 2.2rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.88rem;
		box-sizing: border-box;
		outline: none;
		transition: all 0.15s;
	}

	.header-search-form input:focus {
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}

	.auth-area {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		font-size: 0.88rem;
	}

	.btn-ask-sm {
		text-decoration: none;
		background: #0a95ff;
		color: white;
		padding: 0.4rem 0.8rem;
		border-radius: 3px;
		font-size: 0.82rem;
		font-weight: 500;
	}

	.btn-ask-sm:hover {
		background: #0074cc;
	}

	.rep-badge {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		background: #f8f9fa;
		border: 1px solid #d6d9dc;
		padding: 0.25rem 0.6rem;
		border-radius: 4px;
		text-decoration: none;
		color: #0c0d0e;
		font-size: 0.82rem;
	}

	.rep-badge:hover {
		background: #f1f2f4;
	}

	.avatar-circle {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background: #f48225;
		color: white;
		font-size: 0.72rem;
		font-weight: bold;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}

	.user-name {
		font-weight: 600;
	}

	.rep-num {
		color: #6a737c;
		font-weight: bold;
	}

	.admin-tag {
		background: #d63384;
		color: white;
		font-size: 0.68rem;
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
	}

	.btn-login {
		text-decoration: none;
		color: #39739d;
		background: #e1ecf4;
		border: 1px solid #7aa7c7;
		padding: 0.4rem 0.8rem;
		border-radius: 3px;
		font-size: 0.82rem;
	}

	.btn-login:hover {
		background: #b3d3ea;
	}

	.btn-signup {
		text-decoration: none;
		color: white;
		background: #0a95ff;
		padding: 0.4rem 0.8rem;
		border-radius: 3px;
		font-size: 0.82rem;
	}

	.btn-signup:hover {
		background: #0074cc;
	}

	.btn-logout {
		background: transparent;
		border: 1px solid #d6d9dc;
		border-radius: 3px;
		padding: 0.35rem 0.65rem;
		cursor: pointer;
		font-size: 0.8rem;
		color: #525960;
	}

	.btn-logout:hover {
		background: #f8f9fa;
		color: #c02d0e;
	}

	.main-wrapper {
		flex: 1;
		width: 100%;
		background: white;
	}

	main {
		max-width: 1100px;
		width: 100%;
		margin: 0 auto;
		padding: 1.5rem;
		box-sizing: border-box;
	}

	.muted {
		color: #8a94a3;
	}
</style>
