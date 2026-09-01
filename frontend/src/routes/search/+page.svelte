<script lang="ts">
	import { searchTfidf, ApiError, type SearchResultItem } from '$lib/api/client';

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

	async function runSearch(p = 1, size = pageSize) {
		if (!query.trim()) return;
		loading = true;
		errorMsg = '';
		searched = true;
		try {
			const res = await searchTfidf(query, p, size);
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

	function handleSubmit(e: Event) {
		e.preventDefault();
		currentPage = 1;
		runSearch(1, pageSize);
	}

	function goToPage(p: number) {
		if (p < 1 || p > totalPages || p === currentPage) return;
		currentPage = p;
		runSearch(p, pageSize);
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function changePageSize(size: number) {
		pageSize = size;
		currentPage = 1;
		runSearch(1, size);
	}

	// Stack Overflow pagination number logic
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
</script>

<div class="search-header">
	<h1>Tìm kiếm câu hỏi</h1>
	<p class="subtitle">
		Tìm kiếm bằng <strong>TF-IDF</strong> (Vector Space Model) + Cosine Similarity
	</p>
</div>

<form onsubmit={handleSubmit} class="search-form">
	<input
		bind:value={query}
		placeholder="Nhập câu hỏi hoặc từ khóa, vd: 'lỗi kết nối MongoDB'..."
		autofocus
	/>
	<button type="submit" disabled={loading}>
		{loading ? '⏳ Đang tìm...' : '🔍 Tìm kiếm'}
	</button>
</form>

{#if searched && !loading}
	<div class="result-summary">
		{#if total > 0}
			<span class="result-count">Hiển thị {results.length} / {total} kết quả</span>
			<span class="timing">⏱ {elapsedMs}ms</span>
		{/if}
	</div>
{/if}

{#if errorMsg}
	<p class="error">{errorMsg}</p>
{/if}

{#if searched && !loading && !errorMsg && results.length === 0}
	<div class="empty-state">
		<div class="empty-icon">🔍</div>
		<p class="empty-msg">Không tìm thấy kết quả phù hợp cho "<strong>{query}</strong>".</p>
		<p class="empty-hint">Chưa có câu hỏi nào liên quan đến chủ đề này trong hệ thống.</p>
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
						{r.answerCount}<small>câu trả lời</small>
					</span>
					<span class="stat-item similarity" title="Độ tương đồng cosine">
						{r.similarityPercent}%<small>tương đồng</small>
					</span>
				</div>
				<div class="content">
					<a class="title" href={`/questions/${r.questionId}`}>{r.title}</a>
					<div class="tags">
						{#each r.tags as tag}
							<a class="tag" href={`/questions?tag=${tag}`}>{tag}</a>
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

<style>
	.search-header {
		margin-bottom: 1rem;
	}
	h1 {
		font-size: 1.6rem;
		color: #232629;
		margin: 0;
	}
	.subtitle {
		color: #6a737c;
		font-size: 0.88rem;
		margin: 0.3rem 0 0;
	}
	.search-form {
		display: flex;
		gap: 0.6rem;
		margin: 1.2rem 0 0.5rem;
	}
	.search-form input {
		flex: 1;
		padding: 0.7rem 1rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.95rem;
		outline: none;
		transition: border-color 0.15s;
	}
	.search-form input:focus {
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}
	.search-form button {
		padding: 0.7rem 1.4rem;
		border: none;
		border-radius: 4px;
		background: #0a95ff;
		color: white;
		font-weight: 600;
		font-size: 0.9rem;
		cursor: pointer;
		transition: background 0.15s;
	}
	.search-form button:hover:not(:disabled) {
		background: #0074cc;
	}
	.search-form button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.result-summary {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin: 0.5rem 0 1rem;
		border-bottom: 1px solid #e3e6e8;
		padding-bottom: 0.6rem;
	}
	.result-count {
		font-size: 0.9rem;
		color: #6a737c;
	}
	.timing {
		font-size: 0.82rem;
		color: #9aa4b2;
	}
	.error {
		color: #c02d0e;
		background: #fdf2f0;
		padding: 0.6rem 0.9rem;
		border-radius: 4px;
		border-left: 3px solid #c02d0e;
		font-size: 0.88rem;
	}
	.empty-state {
		padding: 2.5rem 2rem;
		text-align: center;
		background: #f8f9fa;
		border: 1px solid #e3e6e8;
		border-radius: 6px;
		margin: 1rem 0;
	}
	.empty-icon {
		font-size: 2.5rem;
		margin-bottom: 1rem;
	}
	.empty-msg {
		margin: 0 0 0.5rem;
		font-size: 1rem;
		color: #3d4752;
	}
	.empty-hint {
		margin: 0 0 1.5rem;
		font-size: 0.85rem;
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
		transition: background 0.15s;
	}
	.ask-btn:hover {
		background: #0074cc;
	}
	.result-list {
		list-style: none;
		padding: 0;
		margin: 0;
		border-top: 1px solid #e3e6e8;
	}
	.result-list li {
		display: flex;
		gap: 1rem;
		padding: 1rem 0;
		border-bottom: 1px solid #e3e6e8;
	}
	.stats {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		text-align: right;
		min-width: 95px;
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
	.stat-item.similarity {
		color: #0074cc;
	}
	.stat-item.answers.has-accepted {
		color: #2e7d32;
		background: #d4edda;
		border-radius: 3px;
		padding: 0.15rem 0.4rem;
		align-items: center;
	}
	.content {
		flex: 1;
	}
	.title {
		color: #0074cc;
		text-decoration: none;
		font-weight: 500;
		font-size: 1.02rem;
		line-height: 1.4;
		display: block;
	}
	.title:hover {
		color: #0a95ff;
	}
	.tags {
		margin: 0.5rem 0 0;
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
		transition: background 0.1s;
	}
	.tag:hover {
		background: #d0e3f1;
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
		transition: all 0.1s;
	}
	.so-page-btn:hover {
		background: #d6d9dc;
		color: #0c0d0e;
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
		transition: all 0.1s;
	}
	.so-size-btn:hover {
		background: #d6d9dc;
	}
	.so-size-btn.active {
		background: #3c4146;
		border-color: #3c4146;
		color: white;
		font-weight: 600;
	}
</style>