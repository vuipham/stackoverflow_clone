<script lang="ts">
	import { onMount } from 'svelte';
	import { listMyBookmarks, toggleBookmark } from '$lib/api/client';
	import { currentUser } from '$lib/stores/auth';
	import { showToast } from '$lib/stores/toast';

	interface BookmarkQuestion {
		id: string;
		title: string;
		tags: string[];
		voteScore: number;
		answerCount: number;
		createdAt: string;
	}

	let questions = $state<BookmarkQuestion[]>([]);
	let total = $state(0);
	let page = $state(1);
	let totalPages = $state(1);
	let loading = $state(true);
	let errorMsg = $state('');

	async function loadBookmarks(p = 1) {
		loading = true;
		errorMsg = '';
		try {
			const res = await listMyBookmarks(p, 15);
			questions = res.questions;
			total = res.total;
			page = res.page;
			totalPages = res.totalPages;
		} catch {
			errorMsg = 'Không thể tải danh sách câu hỏi đã lưu.';
		} finally {
			loading = false;
		}
	}

	async function handleRemove(qid: string) {
		try {
			await toggleBookmark(qid);
			questions = questions.filter((q) => q.id !== qid);
			total = Math.max(0, total - 1);
			showToast('Đã bỏ lưu câu hỏi', 'success');
		} catch {
			showToast('Không thể bỏ lưu câu hỏi. Vui lòng thử lại.', 'error');
		}
	}

	onMount(() => {
		if ($currentUser) {
			loadBookmarks();
		}
	});
</script>

<svelte:head>
	<title>Câu hỏi đã lưu - Knowledge Hub</title>
</svelte:head>

<div class="bookmarks-page">
	<div class="page-header">
		<h1>🔖 Câu hỏi đã lưu (Bookmarks)</h1>
		<p class="subtitle">Danh sách các câu hỏi bạn đã đánh dấu để xem lại sau ({total} câu hỏi)</p>
	</div>

	{#if !$currentUser}
		<div class="notice">
			<p>Vui lòng <a href="/login">đăng nhập</a> để xem danh sách câu hỏi đã lưu.</p>
		</div>
	{:else if loading}
		<p class="muted">Đang tải câu hỏi đã lưu...</p>
	{:else if errorMsg}
		<p class="error">{errorMsg}</p>
	{:else if questions.length === 0}
		<div class="empty-state">
			<span class="empty-icon">🔖</span>
			<h3>Bạn chưa lưu câu hỏi nào</h3>
			<p>Bấm vào biểu tượng 🔖 ở trang chi tiết câu hỏi để lưu vào danh sách này.</p>
			<a href="/questions" class="btn-primary">Khám phá câu hỏi</a>
		</div>
	{:else}
		<ul class="question-list">
			{#each questions as q}
				<li class="q-card">
					<div class="q-stats">
						<div class="stat"><span class="num">{q.voteScore}</span> vote</div>
						<div class="stat" class:has-ans={q.answerCount > 0}>
							<span class="num">{q.answerCount}</span> trả lời
						</div>
					</div>
					<div class="q-content">
						<h3 class="q-title"><a href={`/questions/${q.id}`}>{q.title}</a></h3>
						<div class="q-tags">
							{#each q.tags as tag}
								<a href={`/questions?tag=${encodeURIComponent(tag)}`} class="tag">{tag}</a>
							{/each}
						</div>
					</div>
					<button class="btn-remove" onclick={() => handleRemove(q.id)} title="Bỏ lưu">
						❌ Bỏ lưu
					</button>
				</li>
			{/each}
		</ul>

		{#if totalPages > 1}
			<div class="pagination">
				{#each Array(totalPages) as _, i}
					<button
						class:active={page === i + 1}
						onclick={() => loadBookmarks(i + 1)}
					>
						{i + 1}
					</button>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.bookmarks-page {
		max-width: 900px;
	}

	.page-header {
		margin-bottom: 1.5rem;
		border-bottom: 1px solid #e3e6e8;
		padding-bottom: 1rem;
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

	.question-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.q-card {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border-bottom: 1px solid #e3e6e8;
		background: white;
	}

	.q-stats {
		display: flex;
		gap: 0.8rem;
		font-size: 0.78rem;
		color: #6a737c;
		flex-shrink: 0;
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 45px;
	}

	.stat.has-ans {
		color: #2e7d32;
		font-weight: 600;
	}

	.num {
		font-size: 0.95rem;
		font-weight: 700;
	}

	.q-content {
		flex: 1;
		min-width: 0;
	}

	.q-title {
		font-size: 1rem;
		margin: 0 0 0.4rem;
	}

	.q-title a {
		color: #0a95ff;
		text-decoration: none;
	}

	.q-title a:hover {
		color: #0074cc;
	}

	.q-tags {
		display: flex;
		gap: 0.4rem;
		flex-wrap: wrap;
	}

	.tag {
		background: #e1ecf4;
		color: #39739d;
		font-size: 0.75rem;
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
		text-decoration: none;
	}

	.btn-remove {
		background: none;
		border: 1px solid #dc3545;
		color: #dc3545;
		padding: 0.3rem 0.6rem;
		border-radius: 4px;
		font-size: 0.78rem;
		cursor: pointer;
		flex-shrink: 0;
	}

	.btn-remove:hover {
		background: #dc3545;
		color: white;
	}

	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
		color: #6a737c;
	}

	.empty-icon {
		font-size: 3rem;
	}

	.btn-primary {
		display: inline-block;
		margin-top: 1rem;
		background: #0a95ff;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		text-decoration: none;
		font-weight: 500;
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
</style>
