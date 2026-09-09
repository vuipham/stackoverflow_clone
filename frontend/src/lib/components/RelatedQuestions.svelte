<script lang="ts">
	import { getRelatedQuestions, type RelatedQuestion } from '$lib/api/client';
	import { onMount } from 'svelte';

	let { questionId }: { questionId: string } = $props();

	let related = $state<RelatedQuestion[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const res = await getRelatedQuestions(questionId, 5);
			related = res.related;
		} catch {
			/* ignore: index chưa có thì chỉ ẩn widget */
		} finally {
			loading = false;
		}
	});
</script>

{#if loading || related.length > 0}
	<div class="related-box">
		<h3 class="related-title">Câu hỏi liên quan</h3>
		{#if loading}
			<p class="related-loading">Đang tải...</p>
		{:else}
			<ul class="related-list">
				{#each related as r}
					<li>
						<a href={`/questions/${r.questionId}`} class="related-link">
							<span class="related-score" class:has-answer={r.answerCount > 0}>
								{r.answerCount}
							</span>
							<span class="related-text">{r.title}</span>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
{/if}

<style>
	.related-box {
		background: white;
		border: 1px solid #d6d9dc;
		border-radius: 4px;
		margin-bottom: 1rem;
		overflow: hidden;
	}

	.related-title {
		font-size: 0.85rem;
		font-weight: 600;
		color: #232629;
		background: #f8f9f9;
		margin: 0;
		padding: 0.6rem 0.8rem;
		border-bottom: 1px solid #e3e6e8;
	}

	.related-loading {
		padding: 0.8rem;
		font-size: 0.82rem;
		color: #6a737c;
		margin: 0;
	}

	.related-list {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.related-list li {
		border-bottom: 1px solid #f0f0f0;
	}

	.related-list li:last-child {
		border-bottom: none;
	}

	.related-link {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		padding: 0.55rem 0.8rem;
		text-decoration: none;
		color: #0a95ff;
		font-size: 0.8rem;
		line-height: 1.4;
		transition: background 0.12s;
	}

	.related-link:hover {
		background: #f0f7ff;
		color: #0074cc;
	}

	.related-score {
		flex-shrink: 0;
		min-width: 22px;
		height: 22px;
		border-radius: 3px;
		border: 1px solid #babfc4;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.7rem;
		font-weight: 600;
		color: #6a737c;
		background: white;
		margin-top: 1px;
	}

	.related-score.has-answer {
		border-color: #2e7d32;
		color: #2e7d32;
		background: #f4fbf6;
	}

	.related-text {
		flex: 1;
		min-width: 0;
	}
</style>
