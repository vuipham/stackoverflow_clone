<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { listQuestions, listTags, type Question, type Tag } from '$lib/api/client';

	let questions = $state<Question[]>([]);
	let tags = $state<Tag[]>([]);
	let loading = $state(true);
	let errorMsg = $state('');

	let activeTag = $derived(page.url.searchParams.get('tag') ?? '');

	async function load(tag: string) {
		loading = true;
		errorMsg = '';
		try {
			const [qRes, tRes] = await Promise.all([listQuestions(tag || undefined), listTags()]);
			questions = qRes.questions;
			tags = tRes.tags.slice(0, 20);
		} catch {
			errorMsg = 'Không tải được danh sách câu hỏi. Kiểm tra backend đã chạy chưa (http://localhost:8000).';
		} finally {
			loading = false;
		}
	}

	onMount(() => load(activeTag));
	$effect(() => {
		load(activeTag);
	});
</script>

<div class="header-row">
	<h1>Câu hỏi{activeTag ? ` — tag: ${activeTag}` : ''}</h1>
	<a class="btn" href="/ask">Đặt câu hỏi mới</a>
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
	<p>Đang tải...</p>
{:else if errorMsg}
	<p class="error">{errorMsg}</p>
{:else if questions.length === 0}
	<p class="empty">Chưa có câu hỏi nào{activeTag ? ' với tag này' : ''}. Hãy là người đầu tiên đặt câu hỏi!</p>
{:else}
	<ul class="question-list">
		{#each questions as q}
			<li>
				<div class="stats">
					<span class="vote">{q.voteScore}<br /><small>votes</small></span>
					<span class="answers" class:has-accepted={q.acceptedAnswerId}>
						{q.answerCount}<br /><small>trả lời</small>
					</span>
				</div>
				<div class="content">
					<a class="title" href={`/questions/${q.id}`}>{q.title}</a>
					<div class="tags">
						{#each q.tags as tag}
							<a class="tag" href={`/questions?tag=${tag}`}>{tag}</a>
						{/each}
					</div>
					<div class="meta">
						{q.viewCount} lượt xem · {new Date(q.createdAt).toLocaleDateString('vi-VN')}
						{#if !q.isIndexed}
							<span class="not-indexed" title="Chưa được vector hóa cho tìm kiếm ngữ nghĩa (Tuần 2)"
								>· chưa index</span
							>
						{/if}
					</div>
				</div>
			</li>
		{/each}
	</ul>
{/if}

<style>
	.header-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	.btn {
		text-decoration: none;
		background: #0074cc;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.9rem;
	}
	.question-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
	}
	.question-list li {
		display: flex;
		gap: 1rem;
		padding: 1rem 0;
		border-bottom: 1px solid #eaecef;
	}
	.stats {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		text-align: center;
		min-width: 60px;
		color: #5b6673;
		font-size: 0.95rem;
	}
	.stats small {
		color: #9aa4b2;
		font-weight: normal;
	}
	.answers.has-accepted {
		background: #d6f5dd;
		border-radius: 6px;
		color: #1a7a3a;
	}
	.content {
		flex: 1;
	}
	.title {
		color: #0074cc;
		text-decoration: none;
		font-weight: 600;
		font-size: 1.05rem;
	}
	.tags {
		margin: 0.4rem 0;
		display: flex;
		gap: 0.4rem;
		flex-wrap: wrap;
	}
	.tag {
		background: #e1ecf4;
		color: #39739d;
		text-decoration: none;
		font-size: 0.78rem;
		padding: 0.15rem 0.5rem;
		border-radius: 4px;
	}
	.tag-cloud {
		display: flex;
		gap: 0.4rem;
		flex-wrap: wrap;
		margin-bottom: 1.2rem;
	}
	.tag-pill {
		background: white;
		border: 1px solid #d0d5dd;
		color: #39739d;
		text-decoration: none;
		font-size: 0.78rem;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
	}
	.tag-pill.active {
		background: #0074cc;
		border-color: #0074cc;
		color: white;
	}
	.tag-pill.clear {
		color: #d63384;
		border-color: #f3c6d8;
	}
	.tag-pill .count {
		color: #9aa4b2;
		font-size: 0.72rem;
	}
	.tag-pill.active .count {
		color: #d7e9fa;
	}
	.meta {
		font-size: 0.8rem;
		color: #9aa4b2;
	}
	.not-indexed {
		color: #c98a1f;
	}
	.error {
		color: #d63384;
	}
	.empty {
		color: #8a94a3;
	}
</style>
