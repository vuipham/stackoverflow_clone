<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import {
		getQuestion,
		castVote,
		listAnswers,
		createAnswer,
		acceptAnswer,
		ApiError,
		type Question,
		type Answer
	} from '$lib/api/client';
	import { currentUser, PRIVILEGE } from '$lib/stores/auth';
	import CommentsSection from '$lib/components/CommentsSection.svelte';

	let question = $state<Question | null>(null);
	let answers = $state<Answer[]>([]);
	let loading = $state(true);
	let errorMsg = $state('');
	let voteMsg = $state('');

	let newAnswerBody = $state('');
	let postingAnswer = $state(false);
	let answerError = $state('');

	async function load() {
		loading = true;
		const id = page.params.id;
		if (!id) {
			errorMsg = 'Thiếu ID câu hỏi';
			loading = false;
			return;
		}
		try {
			const [qRes, aRes] = await Promise.all([getQuestion(id), listAnswers(id)]);
			question = qRes.question;
			answers = aRes.answers;
		} catch {
			errorMsg = 'Không tìm thấy câu hỏi hoặc backend chưa chạy.';
		} finally {
			loading = false;
		}
	}

	onMount(load);

	async function vote(targetType: 'question' | 'answer', targetId: string, value: 1 | -1) {
		voteMsg = '';
		if (!$currentUser) {
			voteMsg = 'Cần đăng nhập để vote.';
			return;
		}
		try {
			const res = await castVote({ targetType, targetId, value });
			if (targetType === 'question' && question) {
				question.voteScore = res.newVoteScore;
			} else {
				const a = answers.find((x) => x.id === targetId);
				if (a) a.voteScore = res.newVoteScore;
			}
		} catch (err) {
			if (err instanceof ApiError) {
				const detail = err.detail as { error?: string } | string;
				voteMsg = typeof detail === 'string' ? detail : detail.error || 'Vote thất bại';
			} else {
				voteMsg = 'Vote thất bại';
			}
		}
	}

	async function submitAnswer(e: Event) {
		e.preventDefault();
		if (!question || !newAnswerBody.trim()) return;
		postingAnswer = true;
		answerError = '';
		try {
			const res = await createAnswer(question.id, newAnswerBody.trim());
			answers = [...answers, res.answer];
			question.answerCount += 1;
			newAnswerBody = '';
		} catch (err) {
			if (err instanceof ApiError) {
				const detail = err.detail as { error?: string } | string;
				answerError = typeof detail === 'string' ? detail : detail.error || 'Đăng câu trả lời thất bại';
			} else {
				answerError = 'Đăng câu trả lời thất bại';
			}
		} finally {
			postingAnswer = false;
		}
	}

	async function handleAccept(answerId: string) {
		try {
			await acceptAnswer(answerId);
			answers = answers.map((a) => ({ ...a, isAccepted: a.id === answerId }));
			if (question) question.acceptedAnswerId = answerId;
		} catch (err) {
			if (err instanceof ApiError) {
				const detail = err.detail as { error?: string } | string;
				voteMsg = typeof detail === 'string' ? detail : detail.error || 'Không thể chấp nhận câu trả lời';
			}
		}
	}

	let canUpvote = $derived(($currentUser?.reputation ?? 0) >= PRIVILEGE.UPVOTE);
	let canDownvote = $derived(($currentUser?.reputation ?? 0) >= PRIVILEGE.DOWNVOTE);
	let isQuestionOwner = $derived(!!question && $currentUser?.id === question.authorId);

	// Câu trả lời được accept lên đầu, còn lại xếp theo voteScore giảm dần
	let sortedAnswers = $derived(
		[...answers].sort((a, b) => Number(b.isAccepted) - Number(a.isAccepted) || b.voteScore - a.voteScore)
	);
</script>

{#if loading}
	<p>Đang tải...</p>
{:else if errorMsg}
	<p class="error">{errorMsg}</p>
{:else if question}
	<h1>{question.title}</h1>
	<div class="tags">
		{#each question.tags as tag}
			<a class="tag" href={`/questions?tag=${encodeURIComponent(tag)}`}>{tag}</a>
		{/each}
	</div>

	<div class="body-row">
		<div class="vote-col">
			<button
				class="vote-btn"
				disabled={!canUpvote}
				title={canUpvote ? 'Upvote' : `Cần tối thiểu ${PRIVILEGE.UPVOTE} điểm reputation để upvote`}
				onclick={() => vote('question', question!.id, 1)}
			>
				▲
			</button>
			<span class="score">{question.voteScore}</span>
			<button
				class="vote-btn"
				disabled={!canDownvote}
				title={canDownvote
					? 'Downvote'
					: `Cần tối thiểu ${PRIVILEGE.DOWNVOTE} điểm reputation để downvote`}
				onclick={() => vote('question', question!.id, -1)}
			>
				▼
			</button>
		</div>
		<div class="body-content">
			<p>{question.body}</p>
			<CommentsSection targetType="question" targetId={question.id} ownerId={question.authorId} />
		</div>
	</div>

	{#if voteMsg}<p class="vote-msg">{voteMsg}</p>{/if}

	<div class="meta-box">
		<span>{question.viewCount} lượt xem</span>
		<span>{question.answerCount} câu trả lời</span>
		<span>Đăng lúc {new Date(question.createdAt).toLocaleString('vi-VN')}</span>
		<span class:indexed={question.isIndexed} class="index-status">
			{question.isIndexed ? '✅ Đã vector hóa (tìm kiếm được)' : '⏳ Chưa vector hóa'}
		</span>
	</div>

	<h2>{answers.length} Câu trả lời</h2>
	<ul class="answer-list">
		{#each sortedAnswers as a}
			<li class:accepted={a.isAccepted}>
				<div class="body-row">
					<div class="vote-col">
						<button
							class="vote-btn"
							disabled={!canUpvote}
							title={canUpvote ? 'Upvote' : `Cần tối thiểu ${PRIVILEGE.UPVOTE} điểm reputation`}
							onclick={() => vote('answer', a.id, 1)}
						>
							▲
						</button>
						<span class="score">{a.voteScore}</span>
						<button
							class="vote-btn"
							disabled={!canDownvote}
							title={canDownvote ? 'Downvote' : `Cần tối thiểu ${PRIVILEGE.DOWNVOTE} điểm reputation`}
							onclick={() => vote('answer', a.id, -1)}
						>
							▼
						</button>
						{#if a.isAccepted}
							<span class="accepted-badge" title="Câu trả lời được chấp nhận">✔</span>
						{:else if isQuestionOwner}
							<button class="accept-btn" onclick={() => handleAccept(a.id)}>Chấp nhận</button>
						{/if}
					</div>
					<div class="body-content">
						<p>{a.body}</p>
						<CommentsSection targetType="answer" targetId={a.id} ownerId={a.authorId} />
					</div>
				</div>
			</li>
		{/each}
		{#if answers.length === 0}
			<p class="empty">Chưa có câu trả lời nào. Hãy là người đầu tiên trả lời!</p>
		{/if}
	</ul>

	{#if $currentUser}
		<h3>Câu trả lời của bạn</h3>
		<form class="answer-form" onsubmit={submitAnswer}>
			<textarea bind:value={newAnswerBody} rows="5" required placeholder="Viết câu trả lời..."
			></textarea>
			{#if answerError}<p class="error">{answerError}</p>{/if}
			<button type="submit" disabled={postingAnswer || !newAnswerBody.trim()}>
				{postingAnswer ? 'Đang đăng...' : 'Đăng câu trả lời'}
			</button>
		</form>
	{:else}
		<p class="login-hint"><a href="/login">Đăng nhập</a> để trả lời câu hỏi này.</p>
	{/if}
{/if}

<style>
	h1 {
		margin-bottom: 0.5rem;
	}
	.tags {
		display: flex;
		gap: 0.4rem;
		margin-bottom: 1rem;
	}
	.tag {
		background: #e1ecf4;
		color: #39739d;
		text-decoration: none;
		font-size: 0.8rem;
		padding: 0.15rem 0.5rem;
		border-radius: 4px;
	}
	.body-row {
		display: flex;
		gap: 1.5rem;
	}
	.vote-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
		min-width: 40px;
	}
	.vote-btn {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		border: 1px solid #d0d5dd;
		background: white;
		font-size: 1rem;
		cursor: pointer;
	}
	.vote-btn:disabled {
		opacity: 0.35;
		cursor: not-allowed;
	}
	.vote-btn:not(:disabled):hover {
		background: #f0f5fb;
		border-color: #0074cc;
	}
	.score {
		font-size: 1.3rem;
		font-weight: 700;
	}
	.accepted-badge {
		color: #1a7a3a;
		font-size: 1.4rem;
	}
	.accept-btn {
		font-size: 0.7rem;
		padding: 0.25rem 0.4rem;
		border: 1px solid #1a7a3a;
		color: #1a7a3a;
		background: white;
		border-radius: 4px;
		cursor: pointer;
	}
	.accept-btn:hover {
		background: #e8f7ed;
	}
	.body-content {
		flex: 1;
		line-height: 1.6;
		white-space: pre-wrap;
	}
	.vote-msg {
		font-size: 0.85rem;
		color: #0074cc;
		margin-top: 0.5rem;
	}
	.meta-box {
		margin-top: 2rem;
		padding-top: 1rem;
		border-top: 1px solid #eaecef;
		display: flex;
		gap: 1.2rem;
		font-size: 0.85rem;
		color: #8a94a3;
		flex-wrap: wrap;
	}
	.index-status.indexed {
		color: #1a7a3a;
	}
	.error {
		color: #d63384;
	}
	.answer-list {
		list-style: none;
		padding: 0;
		margin: 0.5rem 0 0;
	}
	.answer-list li {
		padding: 1rem 0;
		border-bottom: 1px solid #eaecef;
	}
	.answer-list li.accepted {
		background: #f4fbf6;
	}
	.empty {
		color: #8a94a3;
		font-size: 0.9rem;
	}
	.answer-form {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		max-width: 700px;
		margin-top: 0.5rem;
	}
	.answer-form textarea {
		padding: 0.6rem 0.7rem;
		border: 1px solid #d0d5dd;
		border-radius: 6px;
		font-size: 0.95rem;
		font-family: inherit;
	}
	.answer-form button {
		align-self: flex-start;
		padding: 0.55rem 1.3rem;
		border: none;
		border-radius: 6px;
		background: #0074cc;
		color: white;
		font-weight: 600;
		cursor: pointer;
	}
	.answer-form button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.login-hint {
		font-size: 0.9rem;
		color: #5b6673;
	}
</style>
