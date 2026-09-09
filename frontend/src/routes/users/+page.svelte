<script lang="ts">
	import { onMount } from 'svelte';
	import { listUsers, type LeaderboardUser } from '$lib/api/client';

	let users = $state<LeaderboardUser[]>([]);
	let total = $state(0);
	let page = $state(1);
	let totalPages = $state(1);
	let searchQuery = $state('');
	let sort = $state('reputation');
	let loading = $state(true);
	let errorMsg = $state('');

	async function load(p = 1) {
		loading = true;
		errorMsg = '';
		try {
			const res = await listUsers(p, 24, searchQuery, sort);
			users = res.users;
			total = res.total;
			page = res.page;
			totalPages = res.totalPages;
		} catch {
			errorMsg = 'Không thể tải danh sách người dùng.';
		} finally {
			loading = false;
		}
	}

	function handleSearch(e: Event) {
		e.preventDefault();
		load(1);
	}

	onMount(() => {
		load(1);
	});
</script>

<svelte:head>
	<title>Thành viên (Users) - Knowledge Hub</title>
</svelte:head>

<div class="users-page">
	<div class="page-header">
		<h1>👥 Bảng xếp hạng thành viên</h1>
		<p class="subtitle">Danh sách thành viên cộng đồng xếp theo điểm danh tiếng (Reputation) và huy hiệu đạt được ({total} thành viên)</p>
	</div>

	<div class="controls-bar">
		<form onsubmit={handleSearch} class="search-box">
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Lọc theo tên thành viên..."
			/>
			<button type="submit">Tìm</button>
		</form>

		<div class="sort-tabs">
			<button
				class:active={sort === 'reputation'}
				onclick={() => {
					sort = 'reputation';
					load(1);
				}}
			>
				🏆 Rep cao nhất
			</button>
			<button
				class:active={sort === 'newest'}
				onclick={() => {
					sort = 'newest';
					load(1);
				}}
			>
				✨ Thành viên mới
			</button>
		</div>
	</div>

	{#if loading}
		<p class="muted">Đang tải danh sách thành viên...</p>
	{:else if errorMsg}
		<p class="error">{errorMsg}</p>
	{:else if users.length === 0}
		<p class="empty">Không tìm thấy thành viên nào khớp với "{searchQuery}".</p>
	{:else}
		<div class="users-grid">
			{#each users as u, idx}
				<div class="user-card">
					<div class="rank-num">#{(page - 1) * 24 + idx + 1}</div>
					<a href={`/profile?id=${u.id}`} class="avatar">
						{u.displayName.charAt(0).toUpperCase()}
					</a>
					<div class="user-info">
						<a href={`/profile?id=${u.id}`} class="name">
							{u.displayName}
							{#if u.isAdmin}<span class="admin-badge">Admin</span>{/if}
						</a>
						<div class="rep"><strong class="rep-num">{u.reputation.toLocaleString('vi-VN')}</strong> rep</div>
						{#if u.badges && u.badges.length > 0}
							<div class="badges">
								{#each u.badges as b}
									<span class={`badge-pill ${b.tier}`} title={b.description}>
										● {b.name}
									</span>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>

		{#if totalPages > 1}
			<div class="pagination">
				{#each Array(totalPages) as _, i}
					<button
						class:active={page === i + 1}
						onclick={() => load(i + 1)}
					>
						{i + 1}
					</button>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.users-page {
		max-width: 1000px;
	}

	.page-header {
		margin-bottom: 1.2rem;
	}

	h1 {
		font-size: 1.6rem;
		margin: 0 0 0.4rem;
	}

	.subtitle {
		color: #6a737c;
		font-size: 0.9rem;
		margin: 0;
	}

	.controls-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.search-box {
		display: flex;
		gap: 0.4rem;
	}

	.search-box input {
		padding: 0.45rem 0.8rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.88rem;
		width: 250px;
		outline: none;
	}

	.search-box input:focus {
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}

	.search-box button {
		background: #0a95ff;
		color: white;
		border: none;
		border-radius: 4px;
		padding: 0.45rem 0.8rem;
		cursor: pointer;
		font-size: 0.85rem;
	}

	.sort-tabs {
		display: flex;
		border: 1px solid #babfc4;
		border-radius: 4px;
		overflow: hidden;
	}

	.sort-tabs button {
		background: white;
		border: none;
		border-right: 1px solid #babfc4;
		padding: 0.45rem 0.8rem;
		font-size: 0.82rem;
		cursor: pointer;
		color: #525960;
	}

	.sort-tabs button:last-child {
		border-right: none;
	}

	.sort-tabs button.active {
		background: #e3e6e8;
		color: #0c0d0e;
		font-weight: 600;
	}

	.users-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 1rem;
	}

	.user-card {
		background: white;
		border: 1px solid #d6d9dc;
		border-radius: 6px;
		padding: 0.8rem;
		display: flex;
		align-items: center;
		gap: 0.8rem;
		position: relative;
	}

	.rank-num {
		position: absolute;
		top: 6px;
		right: 8px;
		font-size: 0.72rem;
		font-weight: bold;
		color: #9199a1;
	}

	.avatar {
		width: 42px;
		height: 42px;
		border-radius: 50%;
		background: #f48225;
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.1rem;
		font-weight: bold;
		text-decoration: none;
		flex-shrink: 0;
	}

	.user-info {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		min-width: 0;
		flex: 1;
	}

	.name {
		font-weight: 600;
		color: #0a95ff;
		text-decoration: none;
		font-size: 0.9rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.name:hover {
		color: #0074cc;
	}

	.admin-badge {
		background: #d63384;
		color: white;
		font-size: 0.65rem;
		padding: 0.1rem 0.3rem;
		border-radius: 3px;
		margin-left: 0.3rem;
		font-weight: normal;
	}

	.rep {
		font-size: 0.78rem;
		color: #6a737c;
	}

	.rep-num {
		color: #232629;
	}

	.badges {
		display: flex;
		gap: 0.3rem;
		flex-wrap: wrap;
		margin-top: 0.2rem;
	}

	.badge-pill {
		font-size: 0.68rem;
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
		font-weight: 500;
	}

	.badge-pill.bronze {
		background: #f4e8d2;
		color: #ab6a15;
	}

	.badge-pill.silver {
		background: #e3e6e8;
		color: #6a737c;
	}

	.badge-pill.gold {
		background: #fff4d5;
		color: #b28d00;
	}

	.pagination {
		display: flex;
		gap: 0.3rem;
		margin-top: 1.5rem;
	}

	.pagination button {
		border: 1px solid #babfc4;
		background: white;
		padding: 0.3rem 0.6rem;
		border-radius: 3px;
		cursor: pointer;
	}

	.pagination button.active {
		background: #f48225;
		color: white;
		border-color: #f48225;
	}

	.muted {
		color: #6a737c;
	}

	.error {
		color: #c02d0e;
	}

	.empty {
		color: #6a737c;
		font-size: 0.9rem;
	}
</style>
