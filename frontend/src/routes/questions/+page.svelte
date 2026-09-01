<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { listQuestions, listTags, type Question, type Tag } from '$lib/api/client';
	import RightSidebar from '$lib/components/RightSidebar.svelte';

	let questions = $state<Question[]>([]);
	let tags = $state<Tag[]>([]);
	let loading = $state(true);
	let errorMsg = $state('');

	let currentPage = $state(1);
	let totalPages = $state(1);
	let totalQuestions = $state(0);
	let pageSize = $state(20);
	let currentSort = $state<'newest' | 'votes' | 'active' | 'unanswered'>('newest');

	let activeTag = $derived(page.url.searchParams.get('tag') ?? '');

	async function load(tag: string, p = 1, limit = pageSize, sort = currentSort) {
		loading = true;
		errorMsg = '';
		try {
			const [qRes, tRes] = await Promise.all([listQuestions(tag || undefined, p, limit, sort), listTags()]);
			questions = qRes.questions;
			totalQuestions = qRes.total;
			totalPages = qRes.totalPages;
			currentPage = qRes.page;
			tags = tRes.tags.slice(0, 20);
		} catch {
			errorMsg = 'Không tải được danh sách câu hỏi. Kiểm tra backend đã chạy chưa (http://localhost:8000).';
		} finally {
			loading = false;
		}
	}

	function setSort(sort: 'newest' | 'votes' | 'active' | 'unanswered') {
		currentSort = sort;
		currentPage = 1;
		load(activeTag, 1, pageSize, sort);
	}

	function goToPage(p: number) {
		if (p < 1 || p > totalPages || p === currentPage) return;
		currentPage = p;
		load(activeTag, p, pageSize, currentSort);
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function changePageSize(size: number) {
		pageSize = size;
		currentPage = 1;
		load(activeTag, 1, size, currentSort);
	}

	function getPageNumbers(current: number, total: number): (number | string)[] {
		if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
		const pages: (number | string)[] = [1];
		if (current > 3) pages.push('...');
		const start = Math.max(2, current - 1);
		const end = Math.min(total - 1, current + 1);
		for (let i = start; i <= end; i++) pages.push(i);
		if (current < total - 2) pages.push('...');
		pages.push(total);
		return pages;
	}

	onMount(() => load(activeTag, 1, pageSize, currentSort));
	$effect(() => {
		load(activeTag, 1, pageSize, currentSort);
	});
</script>

<div class="so-two-column-layout">
	<!-- Left / Main Column -->
	<div class="so-main-col">
		<div class="header-row">
			<div>
				<h1>Tất cả câu hỏi{activeTag ? ` — tag: ${activeTag}` : ''}</h1>
				<p class="total-subtitle">Tổng cộng <strong>{totalQuestions.toLocaleString('vi-VN')}</strong> câu hỏi</p>
			</div>
			<a class="btn-ask" href="/ask">Đặt câu hỏi</a>
		</div>

		<!-- Stack Overflow Sort Filter Tabs -->
		<div class="so-sort-bar">
			<div class="sort-group">
				<button class="sort-tab" class:active={currentSort === 'newest'} onclick={() => setSort('newest')}>
					Newest
				</button>
				<button class="sort-tab" class:active={currentSort === 'active'} onclick={() => setSort('active')}>
					Active
				</button>
				<button class="sort-tab" class:active={currentSort === 'votes'} onclick={() => setSort('votes')}>
					Score
				</button>
				<button class="sort-tab" class:active={currentSort === 'unanswered'} onclick={() => setSort('unanswered')}>
					Unanswered
				</button>
			</div>
		</div>

		{#if tags.length > 0}
			<div class="tag-cloud">
				{#if activeTag}
					<a class="tag-pill clear" href="/questions">✕ Bỏ lọc</a>
				{/if}
				{#each tags as t}
					<a class="tag-pill" class:active={t.name === activeTag} href={`/questions?tag=${t.name}`}>
						{t.name} <span class="count">{t.questionCount}</span>
					</a>
				{/each}
			</div>
		{/if}

		{#if loading}
			<div class="loading-box">
				<span class="spinner"></span> Đang tải danh sách câu hỏi...
			</div>
		{:else if errorMsg}
			<p class="error">{errorMsg}</p>
		{:else if questions.length === 0}
			<p class="empty">Chưa có câu hỏi nào{activeTag ? ' với tag này' : ''}. Hãy là người đầu tiên đặt câu hỏi!</p>
		{:else}
			<ul class="question-list">
				{#each questions as q}
					<li>
						<div class="stats">
							<span class="stat-item vote">{q.voteScore} <small>votes</small></span>
							<span class="stat-item answers" class:has-accepted={q.acceptedAnswerId}>
								{q.answerCount} <small>câu trả lời</small>
							</span>
							<span class="stat-item views">{q.viewCount} <small>lượt xem</small></span>
						</div>
						<div class="content">
							<a class="title" href={`/questions/${q.id}`}>{q.title}</a>
							<div class="tags">
								{#each q.tags as tag}
									<a class="tag" href={`/questions?tag=${tag}`}>{tag}</a>
								{/each}
							</div>
							<div class="meta">
								<span class="author-badge">
									👤 <strong>{q.author?.displayName ?? 'Thành viên'}</strong>
									<span class="author-rep">({q.author?.reputation?.toLocaleString('vi-VN') ?? 1} rep)</span>
								</span>
								· đăng ngày {new Date(q.createdAt).toLocaleDateString('vi-VN')}
								{#if !q.isIndexed}
									<span class="not-indexed">· chưa index</span>
								{/if}
							</div>
						</div>
					</li>
				{/each}
			</ul>

			<!-- Phân trang Stack Overflow -->
			{#if totalPages > 1}
				<div class="so-pagination-container">
					<div class="so-pagination">
						{#if currentPage > 1}
							<button class="so-page-btn" onclick={() => goToPage(currentPage - 1)}>Prev</button>
						{/if}
						{#each getPageNumbers(currentPage, totalPages) as item}
							{#if typeof item === 'number'}
								<button
									class="so-page-btn"
									class:active={item === currentPage}
									onclick={() => goToPage(item)}
								>
									{item}
								</button>
							{:else}
								<span class="so-page-ellipsis">…</span>
							{/if}
						{/each}
						{#if currentPage < totalPages}
							<button class="so-page-btn" onclick={() => goToPage(currentPage + 1)}>Next</button>
						{/if}
					</div>

					<div class="so-per-page">
						<span class="per-page-label">mỗi trang:</span>
						{#each [15, 30, 50] as size}
							<button
								class="so-size-btn"
								class:active={pageSize === size}
								onclick={() => changePageSize(size)}
							>
								{size}
							</button>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<!-- Right Sidebar -->
	<RightSidebar />
</div>

<style>
	.so-two-column-layout {
		display: flex;
		gap: 2rem;
	}

	.so-main-col {
		flex: 1;
		min-width: 0;
	}

	.header-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}
	h1 {
		margin: 0;
		font-size: 1.6rem;
		color: #232629;
	}
	.total-subtitle {
		margin: 0.3rem 0 0;
		color: #6a737c;
		font-size: 0.88rem;
	}
	.btn-ask {
		text-decoration: none;
		background: #0a95ff;
		color: white;
		padding: 0.6rem 1rem;
		border-radius: 4px;
		font-size: 0.88rem;
		font-weight: 500;
	}
	.btn-ask:hover {
		background: #0074cc;
	}

	/* Sort Bar Tabs */
	.so-sort-bar {
		display: flex;
		justify-content: flex-end;
		margin-bottom: 1rem;
		border-bottom: 1px solid #e3e6e8;
		padding-bottom: 0.6rem;
	}

	.sort-group {
		display: flex;
		border: 1px solid #babfc4;
		border-radius: 3px;
		overflow: hidden;
	}

	.sort-tab {
		background: white;
		border: none;
		border-right: 1px solid #babfc4;
		padding: 0.4rem 0.8rem;
		font-size: 0.82rem;
		color: #6a737c;
		cursor: pointer;
	}

	.sort-tab:last-child {
		border-right: none;
	}

	.sort-tab:hover {
		background: #f8f9fa;
		color: #232629;
	}

	.sort-tab.active {
		background: #e3e6e8;
		color: #0c0d0e;
		font-weight: 600;
	}

	.loading-box {
		padding: 2rem;
		text-align: center;
		color: #6a737c;
	}
	.spinner {
		display: inline-block;
		width: 16px;
		height: 16px;
		border: 2px solid #0a95ff;
		border-radius: 50%;
		border-top-color: transparent;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.question-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		border-top: 1px solid #e3e6e8;
	}
	.question-list li {
		display: flex;
		gap: 1rem;
		padding: 1rem 0;
		border-bottom: 1px solid #e3e6e8;
	}
	.stats {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		text-align: right;
		min-width: 95px;
		color: #6a737c;
		font-size: 0.82rem;
	}
	.stat-item small {
		color: #6a737c;
	}
	.stat-item.vote {
		color: #0c0d0e;
		font-weight: 600;
	}
	.stat-item.answers.has-accepted {
		background: #2e7d32;
		color: white;
		border-radius: 3px;
		padding: 0.2rem 0.4rem;
	}
	.stat-item.answers.has-accepted small {
		color: white;
	}

	.content {
		flex: 1;
	}
	.title {
		color: #0074cc;
		text-decoration: none;
		font-weight: 500;
		font-size: 1.05rem;
		line-height: 1.4;
	}
	.title:hover {
		color: #0a95ff;
	}
	.tags {
		margin: 0.5rem 0 0.3rem;
		display: flex;
		gap: 0.35rem;
		flex-wrap: wrap;
	}
	.tag {
		background: #e1ecf4;
		color: #39739d;
		text-decoration: none;
		font-size: 0.75rem;
		padding: 0.2rem 0.5rem;
		border-radius: 3px;
	}
	.tag-cloud {
		display: flex;
		gap: 0.4rem;
		flex-wrap: wrap;
		margin-bottom: 1.2rem;
	}
	.tag-pill {
		background: white;
		border: 1px solid #babfc4;
		color: #39739d;
		text-decoration: none;
		font-size: 0.78rem;
		padding: 0.25rem 0.65rem;
		border-radius: 999px;
	}
	.tag-pill.active {
		background: #0a95ff;
		border-color: #0a95ff;
		color: white;
	}
	.tag-pill.clear {
		color: #d63384;
		border-color: #f3c6d8;
	}
	.tag-pill .count {
		color: #6a737c;
		font-size: 0.72rem;
	}
	.tag-pill.active .count {
		color: #d7e9fa;
	}
	.meta {
		font-size: 0.78rem;
		color: #6a737c;
		margin-top: 0.4rem;
	}
	.author-badge {
		color: #3b4045;
	}
	.author-rep {
		color: #6a737c;
	}
	.not-indexed {
		color: #c98a1f;
	}

	/* Pagination */
	.so-pagination-container {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 2rem;
		padding-top: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	.so-pagination {
		display: flex;
		gap: 0.25rem;
		align-items: center;
	}
	.so-page-btn {
		background: transparent;
		border: 1px solid #d6d9dc;
		border-radius: 3px;
		padding: 0.3rem 0.65rem;
		font-size: 0.82rem;
		color: #3c4146;
		cursor: pointer;
	}
	.so-page-btn.active {
		background: #f48225;
		border-color: #f48225;
		color: white;
		font-weight: 600;
	}
	.so-page-ellipsis {
		padding: 0 0.3rem;
		color: #6a737c;
		font-size: 0.85rem;
	}
	.so-per-page {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}
	.per-page-label {
		font-size: 0.82rem;
		color: #6a737c;
		margin-right: 0.2rem;
	}
	.so-size-btn {
		background: transparent;
		border: 1px solid #d6d9dc;
		border-radius: 3px;
		padding: 0.25rem 0.55rem;
		font-size: 0.8rem;
		color: #3c4146;
		cursor: pointer;
	}
	.so-size-btn.active {
		background: #3c4146;
		border-color: #3c4146;
		color: white;
		font-weight: 600;
	}
	.error {
		color: #d63384;
	}
	.empty {
		color: #6a737c;
	}
</style>
