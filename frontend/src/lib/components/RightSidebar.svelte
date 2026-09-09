<script lang="ts">
	import { onMount } from 'svelte';
	import { listQuestions } from '$lib/api/client';

	interface HotQuestion {
		id: string;
		title: string;
	}

	// Dự phòng: nếu API lỗi thì vẫn hiển thị nội dung, link tới trang tìm kiếm
	let blogPosts = [
		{ title: 'Tối ưu hóa công cụ tìm kiếm tri thức quy mô 1 triệu bản ghi' },
		{ title: 'Hệ thống tính điểm Reputation và Phân quyền theo ngưỡng' }
	];
	let metaPosts = [{ title: 'Thảo luận về nâng cấp thuật toán TF-IDF Search Engine' }];
	let hotQuestions = $state<HotQuestion[] | null>(null);
	let loaded = $state(false);

	onMount(async () => {
		try {
			const res = await listQuestions(undefined, 1, 5, 'votes');
			hotQuestions = res.questions.map((q) => ({ id: q.id, title: q.title }));
		} catch {
			hotQuestions = [];
		} finally {
			loaded = true;
		}
	});
</script>

<aside class="so-sidebar">
	<!-- Yellow Meta Widget -->
	<div class="sidebar-box yellow-box">
		<div class="box-header">The Overflow Blog</div>
		<ul class="box-list">
			{#each blogPosts as bp}
				<li>
					<span class="icon">✏️</span>
					<a href={`/search?q=${encodeURIComponent(bp.title)}`}>{bp.title}</a>
				</li>
			{/each}
		</ul>
		<div class="box-header">Featured on Meta</div>
		<ul class="box-list">
			{#each metaPosts as mp}
				<li>
					<span class="icon">💬</span>
					<a href={`/search?q=${encodeURIComponent(mp.title)}`}>{mp.title}</a>
				</li>
			{/each}
		</ul>
	</div>

	<!-- Hot Questions Widget -->
	<div class="sidebar-box">
		<div class="box-header plain">Hot Network Questions</div>
		<ul class="hot-list">
			{#if !loaded}
				<li><span class="hot-icon">🔥</span><span class="muted-item">Đang tải...</span></li>
			{:else if hotQuestions && hotQuestions.length > 0}
				{#each hotQuestions as hq}
					<li>
						<span class="hot-icon">🔥</span>
						<a href={`/questions/${hq.id}`}>{hq.title}</a>
					</li>
				{/each}
			{:else}
				<li><span class="hot-icon">🔥</span><span class="muted-item">Chưa có câu hỏi nào.</span></li>
			{/if}
		</ul>
	</div>
</aside>

<style>
	.so-sidebar {
		width: 300px;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		flex-shrink: 0;
	}

	.sidebar-box {
		border: 1px solid #d6d9dc;
		border-radius: 4px;
		background: white;
		overflow: hidden;
		box-shadow: 0 1px 2px rgba(0,0,0,0.05);
	}

	.sidebar-box.yellow-box {
		background: #fdf7e7;
		border-color: #f1e5bc;
	}

	.box-header {
		padding: 0.6rem 0.8rem;
		font-size: 0.82rem;
		font-weight: bold;
		color: #525960;
		border-bottom: 1px solid #f1e5bc;
		background: #fbf3d5;
	}

	.box-header.plain {
		background: #f8f9fa;
		border-bottom: 1px solid #d6d9dc;
		color: #232629;
	}

	.box-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.box-list li {
		padding: 0.6rem 0.8rem;
		display: flex;
		gap: 0.5rem;
		font-size: 0.82rem;
		border-bottom: 1px solid #f1e5bc;
	}

	.box-list li:last-child {
		border-bottom: none;
	}

	.box-list a {
		color: #3b4045;
		text-decoration: none;
		line-height: 1.35;
	}

	.box-list a:hover {
		color: #0074cc;
	}

	.hot-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.hot-list li {
		padding: 0.6rem 0.8rem;
		display: flex;
		gap: 0.5rem;
		font-size: 0.82rem;
		border-bottom: 1px solid #e3e6e8;
	}

	.hot-list li:last-child {
		border-bottom: none;
	}

	.hot-list a {
		color: #0074cc;
		text-decoration: none;
		line-height: 1.35;
	}

	.hot-list a:hover {
		color: #0a95ff;
	}

	.hot-icon {
		font-size: 0.9rem;
	}

	.muted-item {
		color: #8a94a3;
	}
</style>
