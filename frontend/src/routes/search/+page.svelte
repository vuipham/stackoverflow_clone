<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { searchTfidf, ApiError, type SearchResultItem } from '$lib/api/client';
	import RightSidebar from '$lib/components/RightSidebar.svelte';

	let query = $state('');
	let results = $state<SearchResultItem[]>([]);
	let elapsedMs = $state<number | null>(null);
	let loading = $state(false);
	let errorMsg = $state('');
	let searched = $state(false);

	let currentPage = $state(1);
	let totalPages = $state(1);
	let total = $state(0);
	let pageSize = $state(15);

	let urlParamQ = $derived(page.url.searchParams.get('q') ?? '');
	let currentSort = $state<'relevance' | 'newest' | 'votes'>('relevance');

	async function runSearch(q: string, p = 1, size = pageSize, sort = currentSort) {
		if (!q.trim()) return;
		loading = true;
		errorMsg = '';
		searched = true;
		query = q;
		currentSort = sort;
		try {
			const res = await searchTfidf(q, p, size, 0, sort);
			results = res.results;
			elapsedMs = res.elapsedMs;
			total = res.total;
			totalPages = res.totalPages;
			currentPage = res.page;
		} catch (err) {
			results = [];
			elapsedMs = null;
			if (err instanceof ApiError) {
				errorMsg = typeof err.detail === 'string' ? err.detail : 'Tìm kiếm thất bại';
			} else {
				errorMsg = 'Tìm kiếm thất bại - kiểm tra backend đã reindex chưa.';
			}
		} finally {
			loading = false;
		}
	}

	function setSort(sort: 'relevance' | 'newest' | 'votes') {
		if (sort === currentSort) return;
		currentPage = 1;
		runSearch(query, 1, pageSize, sort);
	}

	function goToPage(p: number) {
		if (p < 1 || p > totalPages || p === currentPage) return;
		currentPage = p;
		runSearch(query, p, pageSize);
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function changePageSize(size: number) {
		pageSize = size;
		currentPage = 1;
		runSearch(query, 1, size);
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

	onMount(() => {
		if (urlParamQ) runSearch(urlParamQ, 1, pageSize);
	});

	$effect(() => {
		if (urlParamQ && urlParamQ !== query) {
			runSearch(urlParamQ, 1, pageSize);
		}
	});

	// --- Highlight từ khóa kiểu Stack Overflow ---
	// Tách các "term văn bản" từ query (bỏ [tag], -term, key:value, "phrase" đặc biệt)
	function extractTerms(q: string): string[] {
		const terms = new Set<string>();
		const tokens = q.match(/[A-Za-z0-9À-ỹà-ỹ_+#][A-Za-z0-9À-ỹà-ỹ_+#.-]*/g) ?? [];
		for (const raw of tokens) {
			if (raw.startsWith('[', 0) || raw.startsWith('-')) continue; // tag / loại trừ
			const lower = raw.toLowerCase();
			// 3+ ký tự (bỏ stopword ngắn)
			if (lower.length >= 3) terms.add(lower);
		}
		return [...terms];
	}

	// Trả về HTML an toàn với <mark> quanh các term khớp (dùng {@html})
	function highlightHtml(text: string, q: string): string {
		const terms = extractTerms(q);
		if (!text || terms.length === 0) return text;
		const esc = (s: string) => s.replace(/[&<>"']/g, (c) => (
			{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!
		));
		const escaped = esc(text);
		// Gộp các term để match 1 lần (tránh trùng highlight)
		const pattern = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
		const re = new RegExp(`(${pattern})`, 'gi');
		return escaped.replace(re, '<mark>$1</mark>');
	}
</script>

<svelte:head>
	<title>{query ? `Tìm kiếm: ${query}` : 'Tìm kiếm'} - Knowledge Hub</title>
</svelte:head>

<div class="so-two-column-layout">
	<!-- Main Search Content Column -->
	<div class="so-main-col">
		<div class="search-header">
			{#if searched}
				<h1>Kết quả tìm kiếm</h1>
				{#if query}
					<p class="subtitle">cho '<strong>{query}</strong>'</p>
				{/if}
			{:else}
				<h1>Tìm kiếm câu hỏi</h1>
			{/if}
		</div>

		{#if searched}
			<div class="so-sort-bar">
				<div class="sort-group">
					<button class="sort-tab" class:active={currentSort === 'relevance'} onclick={() => setSort('relevance')}>Relevance</button>
					<button class="sort-tab" class:active={currentSort === 'newest'} onclick={() => setSort('newest')}>Newest</button>
					<button class="sort-tab" class:active={currentSort === 'votes'} onclick={() => setSort('votes')}>Votes</button>
				</div>
			</div>
		{/if}

		{#if searched && !loading}
			<div class="result-summary">
				{#if total > 0}
					<span class="result-count">Hiển thị <strong>{results.length}</strong> / <strong>{total}</strong> kết quả phù hợp nhất</span>
					<span class="timing">⏱ Xử lý trong {elapsedMs}ms</span>
				{/if}
			</div>
		{/if}

		{#if errorMsg}
			<div class="error-box">⚠️ {errorMsg}</div>
		{/if}

		{#if searched && !loading && !errorMsg && results.length === 0}
			<div class="empty-state">
				<div class="empty-icon">🔍</div>
				<p class="empty-msg">Không tìm thấy kết quả phù hợp cho "<strong>{query}</strong>".</p>
				<p class="empty-hint">Hãy thử tìm với các từ khóa đơn giản hơn hoặc kiểm tra xem bài viết đã được Index chưa.</p>
				<a class="ask-btn" href="/ask">✏️ Đặt câu hỏi mới</a>
			</div>
		{/if}

		{#if results.length > 0}
			<ul class="result-list">
				{#each results as r}
					<li>
						<div class="stats">
							<span class="stat-item votes" title="Điểm vote">{r.voteScore}<small>votes</small></span>
							<span
								class="stat-item answers"
								class:has-accepted={r.answerCount > 0}
								title="Số câu trả lời"
							>
								{r.answerCount}<small>trả lời</small>
							</span>
							<span class="stat-item similarity" title="Độ tương đồng cosine">
								<span class="sim-badge">{r.similarityPercent}%</span><small>khớp</small>
							</span>
						</div>
						<div class="content">
							<a class="title" href={`/questions/${r.questionId}?q=${encodeURIComponent(query)}`}>{@html highlightHtml(r.title, query)}</a>
							<div class="tags">
								{#each r.tags as tag}
									<a class="tag" href={`/?tag=${tag}`}>{tag}</a>
								{/each}
							</div>
						</div>
					</li>
				{/each}
			</ul>

			<!-- Thanh phân trang Stack Overflow style -->
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

	<!-- Right Sidebar / Search Hints -->
	<aside class="so-side-col">
		<div class="search-hints-card">
			<h3>💡 Mẹo tìm kiếm</h3>
			<ul class="hint-list">
				<li><code>[tag]</code> <span>tìm theo thẻ (vd: [python])</span></li>
				<li><code>"cụm từ"</code> <span>tìm chính xác từ khóa</span></li>
				<li><code>score:5</code> <span>bài viết có score &ge; 5</span></li>
				<li><code>answers:0</code> <span>câu hỏi chưa có lời giải</span></li>
				<li><code>is:accepted</code> <span>chỉ lấy câu đã chấp nhận</span></li>
			</ul>
		</div>

		<RightSidebar />
	</aside>
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

	.so-side-col {
		width: 300px;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.search-header h1 {
		font-size: 1.6rem;
		color: #232629;
		margin: 0;
	}

	.subtitle {
		color: #6a737c;
		font-size: 0.88rem;
		margin: 0.3rem 0 1rem;
	}

	.result-summary {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin: 0.5rem 0 1rem;
		border-bottom: 1px solid #e3e6e8;
		padding-bottom: 0.6rem;
		font-size: 0.9rem;
		color: #6a737c;
	}

	.timing {
		font-size: 0.82rem;
		color: #0074cc;
		font-weight: 500;
	}

	.error-box {
		color: #c02d0e;
		background: #fdf2f0;
		padding: 0.75rem 1rem;
		border-radius: 4px;
		border-left: 4px solid #c02d0e;
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.empty-state {
		padding: 3rem 2rem;
		text-align: center;
		background: #f8f9fa;
		border: 1px solid #e3e6e8;
		border-radius: 6px;
		margin: 1rem 0;
	}

	.empty-icon {
		font-size: 2.8rem;
		margin-bottom: 0.8rem;
	}

	.empty-msg {
		margin: 0 0 0.5rem;
		font-size: 1.05rem;
		color: #3d4752;
	}

	.empty-hint {
		margin: 0 0 1.5rem;
		font-size: 0.88rem;
		color: #6a737c;
	}

	.ask-btn {
		display: inline-block;
		padding: 0.6rem 1.4rem;
		background: #0a95ff;
		color: white;
		text-decoration: none;
		border-radius: 4px;
		font-weight: 600;
		font-size: 0.88rem;
	}

	.result-list {
		list-style: none;
		padding: 0;
		margin: 0;
		border-top: 1px solid #e3e6e8;
	}

	.result-list li {
		display: flex;
		gap: 1.2rem;
		padding: 1.1rem 0;
		border-bottom: 1px solid #e3e6e8;
	}

	.stats {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		text-align: right;
		min-width: 100px;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		font-size: 0.82rem;
		font-weight: 600;
		color: #6a737c;
	}

	.stat-item small {
		font-weight: 400;
		font-size: 0.72rem;
		color: #9aa4b2;
	}

	.stat-item.votes {
		color: #0c0d0e;
	}

	.sim-badge {
		background: #e1ecf4;
		color: #0074cc;
		padding: 0.1rem 0.4rem;
		border-radius: 3px;
		font-size: 0.82rem;
	}

	.stat-item.answers.has-accepted {
		color: #2e7d32;
		background: #d4edda;
		border-radius: 3px;
		padding: 0.2rem 0.4rem;
		align-items: center;
	}

	.content {
		flex: 1;
	}

	.title {
		color: #0074cc;
		text-decoration: none;
		font-weight: 500;
		font-size: 1.08rem;
		line-height: 1.4;
		display: block;
	}

	.title:hover {
		color: #0a95ff;
	}

	.title :global(mark) {
		background: #ffe58f;
		color: #0c0d0e;
		padding: 0 0.1em;
		border-radius: 2px;
	}

	.tags {
		margin: 0.6rem 0 0;
		display: flex;
		gap: 0.35rem;
		flex-wrap: wrap;
	}

	.tag {
		background: #e1ecf4;
		color: #39739d;
		text-decoration: none;
		font-size: 0.75rem;
		padding: 0.2rem 0.55rem;
		border-radius: 3px;
	}

	/* Search hints card */
	.search-hints-card {
		background: #fdf7e7;
		border: 1px solid #f1e5bc;
		border-radius: 4px;
		padding: 1rem;
	}

	.search-hints-card h3 {
		margin: 0 0 0.8rem;
		font-size: 0.92rem;
		color: #3b4045;
	}

	.hint-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		font-size: 0.8rem;
	}

	.hint-list li {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.hint-list code {
		background: #f1e5bc;
		padding: 0.15rem 0.35rem;
		border-radius: 3px;
		font-weight: 600;
		color: #0c0d0e;
	}

	.hint-list span {
		color: #525960;
	}

	/* Sort Bar Tabs (Stack Overflow style) */
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

	/* Pagination Stack Overflow Style */
	.so-pagination-container {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 1.8rem;
		padding-top: 1rem;
		border-top: 1px solid #e3e6e8;
		flex-wrap: wrap;
		gap: 1rem;
	}
	.so-pagination {
		display: flex;
		gap: 0.2rem;
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
		font-weight: 700;
	}
	.so-page-ellipsis {
		padding: 0 0.25rem;
		color: #6a737c;
		font-size: 0.85rem;
	}
	.so-per-page {
		display: flex;
		align-items: center;
		gap: 0.25rem;
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
</style>