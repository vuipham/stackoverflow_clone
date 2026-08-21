<script lang="ts">
	import { searchTfidf, searchSbert, ApiError, type SearchResultItem } from '$lib/api/client';

	let query = $state('');
	let method = $state<'tfidf' | 'sbert'>('tfidf');
	let results = $state<SearchResultItem[]>([]);
	let elapsedMs = $state<number | null>(null);
	let loading = $state(false);
	let errorMsg = $state('');
	let searched = $state(false);

	async function runSearch(e?: Event) {
		e?.preventDefault();
		if (!query.trim()) return;
		loading = true;
		errorMsg = '';
		searched = true;
		try {
			const res = method === 'tfidf' ? await searchTfidf(query) : await searchSbert(query);
			results = res.results;
			elapsedMs = res.elapsedMs;
		} catch (err) {
			results = [];
			elapsedMs = null;
			if (err instanceof ApiError && err.status === 503) {
				errorMsg = 'Model SBERT chưa sẵn sàng trên server (chưa cài đặt hoặc chưa tải được model).';
			} else if (err instanceof ApiError) {
				errorMsg = typeof err.detail === 'string' ? err.detail : 'Tìm kiếm thất bại';
			} else {
				errorMsg = 'Tìm kiếm thất bại - kiểm tra backend đã reindex chưa (POST /api/admin/search/reindex).';
			}
		} finally {
			loading = false;
		}
	}

	function switchMethod(m: 'tfidf' | 'sbert') {
		method = m;
		if (searched && query.trim()) runSearch();
	}
</script>

<h1>Tìm kiếm ngữ nghĩa</h1>
<p class="subtitle">
	So sánh 2 phương pháp: <strong>TF-IDF</strong> (khớp từ khóa, Vector Space Model cổ điển) và
	<strong>SBERT</strong> (hiểu ngữ nghĩa câu, dùng model pretrained).
</p>

<form onsubmit={runSearch} class="search-form">
	<input
		bind:value={query}
		placeholder="Nhập câu hỏi hoặc từ khóa, vd: 'lỗi kết nối cơ sở dữ liệu'..."
	/>
	<button type="submit" disabled={loading}>{loading ? 'Đang tìm...' : 'Tìm kiếm'}</button>
</form>

<div class="method-toggle">
	<button class:active={method === 'tfidf'} onclick={() => switchMethod('tfidf')}> TF-IDF </button>
	<button class:active={method === 'sbert'} onclick={() => switchMethod('sbert')}> SBERT </button>
</div>

{#if elapsedMs !== null}
	<p class="timing">⏱ Trả về trong <strong>{elapsedMs}ms</strong> ({results.length} kết quả)</p>
{/if}

{#if errorMsg}
	<p class="error">{errorMsg}</p>
{/if}

{#if searched && !loading && !errorMsg && results.length === 0}
	<p class="empty">
		Không tìm thấy kết quả liên quan. Đảm bảo backend đã chạy
		<code>POST /api/admin/search/reindex</code> ít nhất 1 lần sau khi seed dữ liệu.
	</p>
{/if}

<ul class="result-list">
	{#each results as r}
		<li>
			<div class="score-col">
				<span class="score">{r.similarityPercent}%</span>
				<small>tương đồng</small>
			</div>
			<div class="content">
				<a class="title" href={`/questions/${r.questionId}`}>{r.title}</a>
				<div class="tags">
					{#each r.tags as tag}
						<span class="tag">{tag}</span>
					{/each}
				</div>
				<div class="meta">{r.voteScore} votes · {r.answerCount} trả lời</div>
			</div>
		</li>
	{/each}
</ul>

<style>
	.subtitle {
		color: #5b6673;
		font-size: 0.9rem;
		margin-top: -0.5rem;
	}
	.search-form {
		display: flex;
		gap: 0.6rem;
		margin: 1.2rem 0 0.8rem;
	}
	.search-form input {
		flex: 1;
		padding: 0.65rem 0.9rem;
		border: 1px solid #d0d5dd;
		border-radius: 6px;
		font-size: 1rem;
	}
	.search-form button {
		padding: 0.65rem 1.3rem;
		border: none;
		border-radius: 6px;
		background: #0074cc;
		color: white;
		font-weight: 600;
		cursor: pointer;
	}
	.search-form button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.method-toggle {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	.method-toggle button {
		padding: 0.4rem 1rem;
		border: 1px solid #d0d5dd;
		border-radius: 999px;
		background: white;
		cursor: pointer;
		font-size: 0.85rem;
		font-weight: 500;
		color: #5b6673;
	}
	.method-toggle button.active {
		background: #0074cc;
		border-color: #0074cc;
		color: white;
	}
	.timing {
		font-size: 0.85rem;
		color: #5b6673;
		margin-bottom: 0.8rem;
	}
	.error {
		color: #d63384;
	}
	.empty {
		color: #8a94a3;
	}
	.result-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.result-list li {
		display: flex;
		gap: 1rem;
		padding: 0.9rem 0;
		border-bottom: 1px solid #eaecef;
	}
	.score-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 70px;
		text-align: center;
	}
	.score {
		font-size: 1.1rem;
		font-weight: 700;
		color: #0074cc;
	}
	.score-col small {
		color: #9aa4b2;
		font-size: 0.72rem;
	}
	.content {
		flex: 1;
	}
	.title {
		color: #0074cc;
		text-decoration: none;
		font-weight: 600;
		font-size: 1.02rem;
	}
	.tags {
		margin: 0.35rem 0;
		display: flex;
		gap: 0.4rem;
		flex-wrap: wrap;
	}
	.tag {
		background: #e1ecf4;
		color: #39739d;
		font-size: 0.76rem;
		padding: 0.15rem 0.5rem;
		border-radius: 4px;
	}
	.meta {
		font-size: 0.8rem;
		color: #9aa4b2;
	}
</style>
