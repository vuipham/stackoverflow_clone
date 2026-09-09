<script lang="ts">
	import { page } from '$app/state';
	import { currentUser } from '$lib/stores/auth';

	let currentPath = $derived(page.url.pathname);
</script>

<aside class="left-sidebar">
	<nav class="sidebar-nav">
		<a href="/" class="nav-item" class:active={currentPath === '/'}>
			<span class="icon">🏠</span>
			<span class="label">Trang chủ</span>
		</a>

		<div class="nav-section-title">PUBLIC</div>

		<a href="/questions" class="nav-item" class:active={currentPath.startsWith('/questions')}>
			<span class="icon">🌐</span>
			<span class="label">Câu hỏi</span>
		</a>

		<a href="/tags" class="nav-item" class:active={currentPath.startsWith('/tags')}>
			<span class="icon">🏷️</span>
			<span class="label">Thẻ (Tags)</span>
		</a>

		<a href="/users" class="nav-item" class:active={currentPath.startsWith('/users')}>
			<span class="icon">👥</span>
			<span class="label">Thành viên (Users)</span>
		</a>

		<a href="/search" class="nav-item" class:active={currentPath.startsWith('/search')}>
			<span class="icon">🔍</span>
			<span class="label">Tìm kiếm</span>
		</a>

		{#if $currentUser}
			<a href="/bookmarks" class="nav-item" class:active={currentPath.startsWith('/bookmarks')}>
				<span class="icon">🔖</span>
				<span class="label">Đã lưu (Bookmarks)</span>
			</a>
			<a href="/profile" class="nav-item" class:active={currentPath.startsWith('/profile')}>
				<span class="icon">👤</span>
				<span class="label">Hồ sơ cá nhân</span>
			</a>
		{/if}

		{#if $currentUser?.isAdmin}
			<div class="nav-section-title admin-title">ADMINISTRATOR</div>
			<a href="/admin" class="nav-item admin-item" class:active={currentPath.startsWith('/admin')}>
				<span class="icon">⚙️</span>
				<span class="label">Quản trị hệ thống</span>
			</a>
		{/if}
	</nav>
</aside>

<style>
	.left-sidebar {
		width: 220px;
		flex-shrink: 0;
		border-right: 1px solid #e3e6e8;
		padding: 1.5rem 0;
		background: white;
		min-height: calc(100vh - 56px);
		box-sizing: border-box;
	}

	.sidebar-nav {
		display: flex;
		flex-direction: column;
		position: sticky;
		top: 70px;
	}

	.nav-section-title {
		font-size: 0.7rem;
		font-weight: 700;
		color: #6a737c;
		padding: 0.8rem 1rem 0.4rem;
		letter-spacing: 0.5px;
	}

	.admin-title {
		color: #d63384;
		margin-top: 0.5rem;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.55rem 1rem;
		color: #525960;
		text-decoration: none;
		font-size: 0.85rem;
		border-right: 3px solid transparent;
		transition: all 0.15s ease;
	}

	.nav-item:hover {
		color: #0c0d0e;
		background: #f8f9f9;
	}

	.nav-item.active {
		font-weight: 700;
		color: #0c0d0e;
		background: #f1f2f3;
		border-right-color: #f48225;
	}

	.admin-item.active {
		border-right-color: #d63384;
		color: #d63384;
		background: #fdf2f8;
	}

	.icon {
		font-size: 0.95rem;
		width: 18px;
		text-align: center;
	}

	.label {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
</style>
