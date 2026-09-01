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
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
	import UserCard from '$lib/components/UserCard.svelte';
	import RightSidebar from '$lib/components/RightSidebar.svelte';

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

	let sortedAnswers = $derived(
		[...answers].sort((a, b) => Number(b.isAccepted) - Number(a.isAccepted) || b.voteScore - a.voteScore)
	);
</script>

{#if loading}
	<p>Đang tải chi tiết câu hỏi...</p>
{:else if errorMsg}
	<p class="error">{errorMsg}</p>
{:else if question}
	<div class="q-header">
		<h1>{question.title}</h1>
		<a href="/ask" class="btn-ask">Đặt câu hỏi</a>
	</div>

	<!-- Subtitle bar chuẩn Stack Overflow -->
	<div class="q-sub-meta">
		<span>Đã hỏi: <strong>{new Date(question.createdAt).toLocaleDateString('vi-VN')}</strong></span>
		<span>Được xem: <strong>{question.viewCount.toLocaleString('vi-VN')} lần</strong></span>
		<span class:indexed={question.isIndexed} class="index-status">
			{question.isIndexed ? '✅ Đã Vector Hóa Index' : '⏳ Chưa Vector Hóa'}
		</span>
	</div>

	<div class="so-two-col">
		<div class="so-main-content">
			<!-- Question post row -->
			<div class="post-layout">
				<div class="vote-col">
					<button
						class="vote-btn"
						disabled={!canUpvote}
						title={canUpvote ? 'Upvote' : `Cần tối thiểu ${PRIVILEGE.UPVOTE} reputation`}
						onclick={() => vote('question', question!.id, 1)}
					>
						▲
					</button>
					<span class="score">{question.voteScore}</span>
					<button
						class="vote-btn"
						disabled={!canDownvote}
						title={canDownvote ? 'Downvote' : `Cần tối thiểu ${PRIVILEGE.DOWNVOTE} reputation`}
						onclick={() => vote('question', question!.id, -1)}
					>
						▼
					</button>
				</div>

				<div class="post-body">
					<MarkdownRenderer content={question.body} />

					<div class="tags">
						{#each question.tags as tag}
							<a class="tag" href={`/questions?tag=${encodeURIComponent(tag)}`}>{tag}</a>
						{/each}
					</div>

					<div class="post-footer">
						<div></div>
						<UserCard author={question.author} date={question.createdAt} label="đã hỏi" />
					</div>

					<CommentsSection targetType="question" targetId={question.id} ownerId={question.authorId} />
				</div>
			</div>

			{#if voteMsg}<p class="vote-msg">{voteMsg}</p>{/if}

			<!-- Answers Section -->
			<div class="answers-header">
				<h2>{answers.length} Câu trả lời</h2>
			</div>

			<ul class="answer-list">
				{#each sortedAnswers as a}
					<li class:accepted={a.isAccepted}>
						<div class="post-layout">
							<div class="vote-col">
								<button
									class="vote-btn"
									disabled={!canUpvote}
									title={canUpvote ? 'Upvote' : `Cần tối thiểu ${PRIVILEGE.UPVOTE} reputation`}
									onclick={() => vote('answer', a.id, 1)}
								>
									▲
								</button>
								<span class="score">{a.voteScore}</span>
								<button
									class="vote-btn"
									disabled={!canDownvote}
									title={canDownvote ? 'Downvote' : `Cần tối thiểu ${PRIVILEGE.DOWNVOTE} reputation`}
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

							<div class="post-body">
								<MarkdownRenderer content={a.body} />

								<div class="post-footer">
									<div></div>
									<UserCard author={a.author} date={a.createdAt} label="đã trả lời" />
								</div>

								<CommentsSection targetType="answer" targetId={a.id} ownerId={a.authorId} />
							</div>
						</div>
					</li>
				{/each}
				{#if answers.length === 0}
					<p class="empty">Chưa có câu trả lời nào. Hãy là người đầu tiên trả lời!</p>
				{/if}
			</ul>

			<!-- Answer Form -->
			{#if $currentUser}
				<div class="new-answer-box">
					<h3>Câu trả lời của bạn</h3>
					<form class="answer-form" onsubmit={submitAnswer}>
						<textarea
							bind:value={newAnswerBody}
							rows="6"
							required
							placeholder="Viết câu trả lời của bạn (hỗ trợ Markdown code blocks ```code```)..."
						></textarea>
						{#if answerError}<p class="error">{answerError}</p>{/if}
						<button type="submit" disabled={postingAnswer || !newAnswerBody.trim()}>
							{postingAnswer ? 'Đang đăng...' : 'Đăng câu trả lời'}
						</button>
					</form>
				</div>
			{:else}
				<p class="login-hint"><a href="/login">Đăng nhập</a> để trả lời câu hỏi này.</p>
			{/if}
		</div>

		<!-- Right Sidebar -->
		<RightSidebar />
	</div>
{/if}

<style>
	.q-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
	}

	h1 {
		margin: 0;
		font-size: 1.5rem;
		color: #232629;
		line-height: 1.35;
	}

	.btn-ask {
		text-decoration: none;
		background: #0a95ff;
		color: white;
		padding: 0.55rem 0.95rem;
		border-radius: 4px;
		font-size: 0.85rem;
		font-weight: 500;
		flex-shrink: 0;
	}

	.q-sub-meta {
		display: flex;
		gap: 1.5rem;
		padding-bottom: 0.8rem;
		margin: 0.5rem 0 1.2rem;
		border-bottom: 1px solid #e3e6e8;
		font-size: 0.82rem;
		color: #6a737c;
	}

	.q-sub-meta strong {
		color: #232629;
	}

	.so-two-col {
		display: flex;
		gap: 2rem;
	}

	.so-main-content {
		flex: 1;
		min-width: 0;
	}

	.post-layout {
		display: flex;
		gap: 1.2rem;
	}

	.vote-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
		min-width: 42px;
	}

	.vote-btn {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		border: 1px solid #babfc4;
		background: white;
		font-size: 0.95rem;
		cursor: pointer;
		color: #6a737c;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.vote-btn:not(:disabled):hover {
		background: #fdf7e7;
		border-color: #f48225;
		color: #f48225;
	}

	.vote-btn:disabled {
		opacity: 0.35;
		cursor: not-allowed;
	}

	.score {
		font-size: 1.3rem;
		font-weight: 700;
		color: #232629;
	}

	.accepted-badge {
		color: #2e7d32;
		font-size: 1.5rem;
		margin-top: 0.3rem;
	}

	.accept-btn {
		font-size: 0.7rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid #2e7d32;
		color: #2e7d32;
		background: white;
		border-radius: 3px;
		cursor: pointer;
	}

	.accept-btn:hover {
		background: #e8f5e9;
	}

	.post-body {
		flex: 1;
		min-width: 0;
	}

	.tags {
		display: flex;
		gap: 0.4rem;
		margin: 1rem 0;
		flex-wrap: wrap;
	}

	.tag {
		background: #e1ecf4;
		color: #39739d;
		text-decoration: none;
		font-size: 0.76rem;
		padding: 0.2rem 0.5rem;
		border-radius: 3px;
	}

	.post-footer {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		margin: 1rem 0;
	}

	.vote-msg {
		font-size: 0.85rem;
		color: #c02d0e;
		margin-top: 0.5rem;
	}

	.answers-header {
		margin-top: 2rem;
		padding-top: 1rem;
		border-top: 1px solid #e3e6e8;
	}

	.answers-header h2 {
		font-size: 1.3rem;
		color: #232629;
	}

	.answer-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.answer-list li {
		padding: 1.2rem 0;
		border-bottom: 1px solid #e3e6e8;
	}

	.answer-list li.accepted {
		background: #f4fbf6;
		border-left: 4px solid #2e7d32;
		padding-left: 0.8rem;
	}

	.new-answer-box {
		margin-top: 2.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e3e6e8;
	}

	.new-answer-box h3 {
		font-size: 1.1rem;
		margin-bottom: 0.8rem;
	}

	.answer-form {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.answer-form textarea {
		padding: 0.7rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.95rem;
		font-family: inherit;
		outline: none;
	}

	.answer-form textarea:focus {
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}

	.answer-form button {
		align-self: flex-start;
		padding: 0.6rem 1.2rem;
		border: none;
		border-radius: 4px;
		background: #0a95ff;
		color: white;
		font-weight: 600;
		cursor: pointer;
	}

	.login-hint {
		margin-top: 2rem;
		font-size: 0.9rem;
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
