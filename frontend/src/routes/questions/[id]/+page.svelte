<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import {
		updateQuestion,
		updateAnswer,
		getQuestion,
		castVote,
		listAnswers,
		createAnswer,
		acceptAnswer,
		checkBookmark,
		toggleBookmark,
		getQuestionRevisions,
		closeQuestion,
		reopenQuestion,
		setBounty,
		ApiError,
		type Question,
		type Answer,
		type Revision
	} from '$lib/api/client';
	import { currentUser, PRIVILEGE } from '$lib/stores/auth';
	import { fetchMe } from '$lib/api/client';
	import { showToast } from '$lib/stores/toast';
	import CommentsSection from '$lib/components/CommentsSection.svelte';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
	import UserCard from '$lib/components/UserCard.svelte';
	import RightSidebar from '$lib/components/RightSidebar.svelte';
	import RelatedQuestions from '$lib/components/RelatedQuestions.svelte';

	let question = $state<Question | null>(null);
	let answers = $state<Answer[]>([]);
	let loading = $state(true);
	let errorMsg = $state('');
	let voteMsg = $state('');

	let newAnswerBody = $state('');
	let postingAnswer = $state(false);
	let answerError = $state('');
	let answerTab = $state<'write' | 'preview'>('write');

	let isBookmarked = $state(false);

	// Từ khóa tìm kiếm truyền từ trang /search qua ?q= để highlight trong nội dung bài viết (kiểu SO)
	let highlightQ = $derived(page.url.searchParams.get('q') ?? '');

	// Modal Lịch sử chỉnh sửa
	let showRevisions = $state(false);
	let revisions = $state<Revision[]>([]);
	let loadingRevisions = $state(false);

	// Modal Bounty
	let showBountyModal = $state(false);
	let bountyAmount = $state(50);
	let bountyError = $state('');

	// Modal Close
	let showCloseModal = $state(false);
	let closeReason = $state('Trùng lặp hoặc không phù hợp');

	async function load() {
		loading = true;
		const id = page.params.id;
		if (!id) {
			errorMsg = 'Thiếu ID câu hỏi';
			loading = false;
			return;
		}
		try {
			// Lam moi thong tin user (reputation/isAdmin) de quyen hien nut Sua dung voi DB
			if ($currentUser) {
				fetchMe().then((u) => currentUser.set(u)).catch(() => {});
			}
			const [qRes, aRes] = await Promise.all([getQuestion(id), listAnswers(id)]);
			question = qRes.question;
			answers = aRes.answers;
			if ($currentUser) {
				checkBookmark(id).then((r) => (isBookmarked = r.bookmarked)).catch(() => {});
			}
		} catch {
			errorMsg = 'Không tìm thấy câu hỏi hoặc backend chưa chạy.';
		} finally {
			loading = false;
		}
	}

	async function handleToggleBookmark() {
		if (!question || !$currentUser) return;
		try {
			const res = await toggleBookmark(question.id);
			isBookmarked = res.bookmarked;
			showToast(res.bookmarked ? 'Đã lưu câu hỏi vào danh sách yêu thích' : 'Đã bỏ lưu câu hỏi', 'success');
		} catch (err) {
			showToast(err instanceof ApiError ? String(err.detail) : 'Thao tác thất bại', 'error');
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
			showToast(voteMsg, 'error');
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
			showToast('Đã đăng câu trả lời thành công', 'success');
		} catch (err) {
			if (err instanceof ApiError) {
				const detail = err.detail as { error?: string } | string;
				answerError = typeof detail === 'string' ? detail : detail.error || 'Đăng câu trả lời thất bại';
			} else {
				answerError = 'Đăng câu trả lời thất bại';
			}
			showToast(answerError, 'error');
		} finally {
			postingAnswer = false;
		}
	}

	async function handleAccept(answerId: string) {
		try {
			await acceptAnswer(answerId);
			answers = answers.map((a) => ({ ...a, isAccepted: a.id === answerId }));
			if (question) question.acceptedAnswerId = answerId;
			showToast('Đã chấp nhận câu trả lời này', 'success');
		} catch (err) {
			if (err instanceof ApiError) {
				const detail = err.detail as { error?: string } | string;
				voteMsg = typeof detail === 'string' ? detail : detail.error || 'Không thể chấp nhận câu trả lời';
				showToast(voteMsg, 'error');
			}
		}
	}

	async function openRevisionsModal() {
		if (!question) return;
		showRevisions = true;
		loadingRevisions = true;
		try {
			const res = await getQuestionRevisions(question.id);
			revisions = res.revisions;
		} catch {
			// không làm giãn phiên bản revisions nếu backend lỗi
		} finally {
			loadingRevisions = false;
		}
	}

	async function submitCloseQuestion() {
		if (!question) return;
		try {
			await closeQuestion(question.id, closeReason);
			question.isClosed = true;
			question.closeReason = closeReason;
			showCloseModal = false;
			showToast('Đã đóng câu hỏi', 'success');
		} catch (err) {
			voteMsg = err instanceof ApiError ? String(err.detail) : 'Không thể đóng câu hỏi';
			showToast(voteMsg, 'error');
		}
	}

	async function submitReopenQuestion() {
		if (!question) return;
		try {
			await reopenQuestion(question.id);
			question.isClosed = false;
			question.closeReason = null;
			showToast('Đã mở lại câu hỏi', 'success');
		} catch (err) {
			voteMsg = err instanceof ApiError ? String(err.detail) : 'Không thể mở lại câu hỏi';
			showToast(voteMsg, 'error');
		}
	}

	async function submitBounty() {
		if (!question) return;
		bountyError = '';
		try {
			await setBounty(question.id, bountyAmount);
			question.bounty = bountyAmount;
			showBountyModal = false;
			showToast(`Đã treo thưởng +${bountyAmount} reputation`, 'success');
		} catch (err) {
			bountyError = err instanceof ApiError ? String(err.detail) : 'Đặt bounty thất bại';
			showToast(bountyError, 'error');
		}
	}

	let canUpvote = $derived(($currentUser?.reputation ?? 0) >= PRIVILEGE.UPVOTE);
	let canDownvote = $derived(($currentUser?.reputation ?? 0) >= PRIVILEGE.DOWNVOTE);
	let isQuestionOwner = $derived(!!question && $currentUser?.id === question.authorId);

	let sortedAnswers = $derived(
		[...answers].sort((a, b) => Number(b.isAccepted) - Number(a.isAccepted) || b.voteScore - a.voteScore)
	);


	// ==== Sửa bài viết (chủ sở hữu luôn được sửa; người khác cần rep >= EDIT_OTHERS_POST) ====
	let canEditQuestion = $derived(
		!!$currentUser &&
		(isQuestionOwner || $currentUser.isAdmin || ($currentUser.reputation ?? 0) >= PRIVILEGE.EDIT_OTHERS_POST)
	);

	function canEditAnswer(a: Answer): boolean {
		if (!$currentUser) return false;
		return a.authorId === $currentUser.id || $currentUser.isAdmin || ($currentUser.reputation ?? 0) >= PRIVILEGE.EDIT_OTHERS_POST;
	}

	// Modal sửa câu hỏi
	let showEditQuestion = $state(false);
	let editTitle = $state('');
	let editBody = $state('');
	let editTagsInput = $state('');
	let editTab = $state<'write' | 'preview'>('write');
	let savingEdit = $state(false);
	let editError = $state('');

	// Sửa câu trả lời (inline)
	let editingAnswerId = $state<string | null>(null);
	let editAnswerBody = $state('');
	let savingAnswerEdit = $state(false);
	let editAnswerError = $state('');

	function openEditQuestion() {
		if (!question) return;
		editTitle = question.title;
		editBody = question.body;
		editTagsInput = question.tags.join(', ');
		editTab = 'write';
		editError = '';
		showEditQuestion = true;
	}

	function parseEditError(err: unknown, fallback: string): string {
		if (err instanceof ApiError) {
			const d = err.detail;
			if (typeof d === 'string') return d;
			if (d && typeof d === 'object' && 'error' in d && typeof (d as { error?: unknown }).error === 'string') {
				return (d as { error: string }).error;
			}
		}
		return fallback;
	}

	async function submitEditQuestion() {
		if (!question) return;
		editError = '';
		if (editTitle.trim().length < 5) {
			editError = 'Tiêu đề phải có ít nhất 5 ký tự';
			return;
		}
		if (!editBody.trim()) {
			editError = 'Nội dung không được để trống';
			return;
		}
		savingEdit = true;
		try {
			const tags = editTagsInput.split(',').map((t) => t.trim().toLowerCase()).filter(Boolean);
			const res = await updateQuestion(question.id, { title: editTitle.trim(), body: editBody, tags });
			question = res.question;
			showEditQuestion = false;
			showToast('Đã lưu chỉnh sửa câu hỏi', 'success');
		} catch (err) {
			editError = parseEditError(err, 'Lưu chỉnh sửa thất bại');
			showToast(editError, 'error');
		} finally {
			savingEdit = false;
		}
	}

	function startEditAnswer(a: Answer) {
		editingAnswerId = a.id;
		editAnswerBody = a.body;
		editAnswerError = '';
	}

	function cancelEditAnswer() {
		editingAnswerId = null;
		editAnswerBody = '';
		editAnswerError = '';
	}

	async function submitEditAnswer() {
		if (!editingAnswerId) return;
		if (!editAnswerBody.trim()) {
			editAnswerError = 'Nội dung không được để trống';
			return;
		}
		savingAnswerEdit = true;
		editAnswerError = '';
		try {
			const res = await updateAnswer(editingAnswerId, editAnswerBody);
			answers = answers.map((x) => (x.id === res.answer.id ? { ...x, body: res.answer.body } : x));
			editingAnswerId = null;
			editAnswerBody = '';
			showToast('Đã lưu chỉnh sửa câu trả lời', 'success');
		} catch (err) {
			editAnswerError = parseEditError(err, 'Lưu chỉnh sửa thất bại');
			showToast(editAnswerError, 'error');
		} finally {
			savingAnswerEdit = false;
		}
	}
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

	<!-- Bounty Banner -->
	{#if question.bounty && question.bounty > 0}
		<div class="bounty-banner">
			<span class="bounty-badge">+{question.bounty} bounty</span>
			<span>Câu hỏi này đang có phần thưởng cống hiến <strong>+{question.bounty} reputation</strong> cho câu trả lời được chấp nhận!</span>
		</div>
	{/if}

	<!-- Closed Question Alert Banner -->
	{#if question.isClosed}
		<div class="closed-banner">
			<span>🔒 <strong>Câu hỏi này đã bị đóng.</strong> Lý do: {question.closeReason ?? 'Trùng lặp hoặc không phù hợp'}. Không thể đăng thêm câu trả lời.</span>
		</div>
	{/if}

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
					{#if $currentUser}
						<button
							class="bookmark-btn"
							class:bookmarked={isBookmarked}
							title={isBookmarked ? 'Bỏ lưu câu hỏi này' : 'Lưu câu hỏi này'}
							onclick={handleToggleBookmark}
						>
							🔖
						</button>
					{/if}
				</div>

				<div class="post-body">
					<MarkdownRenderer content={question.body} highlight={highlightQ} />

					<div class="tags">
						{#each question.tags as tag}
							<a class="tag" href={`/questions?tag=${encodeURIComponent(tag)}`}>{tag}</a>
						{/each}
					</div>

					<div class="post-footer">
						<div class="post-actions">
							<button class="action-btn" onclick={openRevisionsModal}>📜 Lịch sử chỉnh sửa</button>

							{#if canEditQuestion}
								<button class="action-btn" onclick={openEditQuestion}>✏️ Sửa</button>
							{/if}
							{#if $currentUser && !question.bounty && ($currentUser.reputation ?? 1) >= 50}
								<button class="action-btn bounty-btn" onclick={() => (showBountyModal = true)}>💰 Treo thưởng Bounty</button>
							{/if}
							{#if $currentUser && (isQuestionOwner || $currentUser.isAdmin || ($currentUser.reputation ?? 1) >= 500)}
								{#if question.isClosed}
									<button class="action-btn" onclick={submitReopenQuestion}>🔓 Mở lại câu hỏi</button>
								{:else}
									<button class="action-btn close-btn" onclick={() => (showCloseModal = true)}>🔒 Đóng câu hỏi</button>
								{/if}
							{/if}
						</div>
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
								{#if editingAnswerId === a.id}
									<div class="answer-edit-box">
										<textarea bind:value={editAnswerBody} rows="6" placeholder="Chỉnh sửa câu trả lời (hỗ trợ Markdown)..."></textarea>
										{#if editAnswerError}<p class="error">{editAnswerError}</p>{/if}
										<div class="answer-edit-actions">
											<button class="action-btn save-btn" onclick={submitEditAnswer} disabled={savingAnswerEdit || !editAnswerBody.trim()}>
												{savingAnswerEdit ? 'Đang lưu...' : 'Lưu chỉnh sửa'}
											</button>
											<button class="action-btn" onclick={cancelEditAnswer}>Hủy</button>
										</div>
									</div>
								{:else}
								<MarkdownRenderer content={a.body} highlight={highlightQ} />
								{/if}

								<div class="post-footer">
									<div class="answer-actions">
										{#if canEditAnswer(a) && editingAnswerId !== a.id}
											<button class="action-btn" onclick={() => startEditAnswer(a)}>✏️ Sửa</button>
										{/if}
									</div>
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
				{#if question.isClosed}
					<p class="closed-notice">🔒 Câu hỏi này đã đóng, không thể gửi thêm câu trả lời.</p>
				{:else}
					<div class="new-answer-box">
						<div class="answer-header">
							<h3>Câu trả lời của bạn</h3>
							<div class="tab-toggle">
								<button type="button" class:active={answerTab === 'write'} onclick={() => (answerTab = 'write')}>Soạn thảo</button>
								<button type="button" class:active={answerTab === 'preview'} onclick={() => (answerTab = 'preview')}>Xem trước</button>
							</div>
						</div>
						<form class="answer-form" onsubmit={submitAnswer}>
							{#if answerTab === 'write'}
								<textarea
									bind:value={newAnswerBody}
									rows="6"
									required
									placeholder="Viết câu trả lời của bạn (hỗ trợ Markdown code blocks ```code```)..."
								></textarea>
							{:else}
								<div class="preview-box">
									{#if newAnswerBody.trim()}
										<MarkdownRenderer content={newAnswerBody} />
									{:else}
										<p class="empty-preview">Chưa có nội dung để xem trước...</p>
									{/if}
								</div>
							{/if}
							{#if answerError}<p class="error">{answerError}</p>{/if}
							<button type="submit" disabled={postingAnswer || !newAnswerBody.trim()}>
								{postingAnswer ? 'Đang đăng...' : 'Đăng câu trả lời'}
							</button>
						</form>
					</div>
				{/if}
			{:else}
				<p class="login-hint"><a href="/login">Đăng nhập</a> để trả lời câu hỏi này.</p>
			{/if}
		</div>

		<!-- Right Column -->
		<div class="so-right-col">
			<RelatedQuestions questionId={question.id} />
			<RightSidebar />
		</div>
	</div>
{/if}

<!-- Modals -->
{#if showRevisions}
	<div class="modal-backdrop" onclick={() => (showRevisions = false)}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h3>📜 Lịch sử chỉnh sửa (Revision History)</h3>
				<button class="close-btn-icon" onclick={() => (showRevisions = false)}>×</button>
			</div>
			{#if loadingRevisions}
				<p>Đang tải lịch sử...</p>
			{:else if revisions.length === 0}
				<p>Chưa có bản ghi chỉnh sửa nào.</p>
			{:else}
				<div class="revisions-list">
					{#each revisions as r, idx}
						<div class="revision-item">
							<div class="rev-header">
								<strong>Phiên bản #{idx + 1}</strong>
								<span class="rev-meta">bởi <strong>{r.editorName}</strong> lúc {new Date(r.createdAt).toLocaleString('vi-VN')}</span>
							</div>
							<p class="rev-comment"><em>{r.comment}</em></p>
							{#if r.title}<h4 class="rev-title">{r.title}</h4>{/if}
							<div class="rev-body">
								<MarkdownRenderer content={r.body} />
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}

{#if showBountyModal}
	<div class="modal-backdrop" onclick={() => (showBountyModal = false)}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h3>💰 Treo thưởng Bounty</h3>
				<button class="close-btn-icon" onclick={() => (showBountyModal = false)}>×</button>
			</div>
			<p>Chọn số điểm Reputation bạn muốn treo thưởng cho câu trả lời tốt nhất:</p>
			<div class="bounty-options">
				{#each [50, 100, 200, 500] as amt}
					<button class:active={bountyAmount === amt} onclick={() => (bountyAmount = amt)}>
						+{amt} rep
					</button>
				{/each}
			</div>
			{#if bountyError}<p class="error">{bountyError}</p>{/if}
			<div class="modal-actions">
				<button class="btn-cancel" onclick={() => (showBountyModal = false)}>Hủy</button>
				<button class="btn-confirm" onclick={submitBounty}>Xác nhận treo thưởng +{bountyAmount} rep</button>
			</div>
		</div>
	</div>
{/if}

{#if showCloseModal}
	<div class="modal-backdrop" onclick={() => (showCloseModal = false)}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h3>🔒 Đóng câu hỏi</h3>
				<button class="close-btn-icon" onclick={() => (showCloseModal = false)}>×</button>
			</div>
			<p>Nhập lý do đóng câu hỏi:</p>
			<input type="text" class="modal-input" bind:value={closeReason} placeholder="Ví dụ: Trùng lặp câu hỏi, thiếu chi tiết..." />
			<div class="modal-actions">
				<button class="btn-cancel" onclick={() => (showCloseModal = false)}>Hủy</button>
				<button class="btn-confirm danger" onclick={submitCloseQuestion}>Xác nhận đóng</button>
			</div>
		</div>
	</div>
{/if}

{#if showEditQuestion}
	<div class="modal-backdrop" onclick={() => (showEditQuestion = false)}>
		<div class="modal-content edit-modal" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h3>✏️ Sửa câu hỏi</h3>
				<button class="close-btn-icon" onclick={() => (showEditQuestion = false)}>×</button>
			</div>
			<label class="edit-label" for="edit-q-title">Tiêu đề</label>
			<input type="text" class="modal-input" id="edit-q-title" bind:value={editTitle} placeholder="Tiêu đề câu hỏi (tối thiểu 5 ký tự)..." />
			<div class="edit-tab-toggle">
				<button type="button" class:active={editTab === 'write'} onclick={() => (editTab = 'write')}>Soạn thảo</button>
				<button type="button" class:active={editTab === 'preview'} onclick={() => (editTab = 'preview')}>Xem trước</button>
			</div>
			{#if editTab === 'write'}
				<textarea class="edit-textarea" bind:value={editBody} rows="8" placeholder="Nội dung câu hỏi (hỗ trợ Markdown code blocks)..."></textarea>
			{:else}
				<div class="preview-box">
					{#if editBody.trim()}
						<MarkdownRenderer content={editBody} />
					{:else}
						<p class="empty-preview">Chưa có nội dung để xem trước...</p>
					{/if}
				</div>
			{/if}
			<label class="edit-label" for="edit-q-tags">Thẻ (phân cách bằng dấu phẩy)</label>
			<input type="text" class="modal-input" id="edit-q-tags" bind:value={editTagsInput} placeholder="vd: python, fastapi, mongodb" />
			{#if editError}<p class="error">{editError}</p>{/if}
			<div class="modal-actions">
				<button class="btn-cancel" onclick={() => (showEditQuestion = false)}>Hủy</button>
				<button class="btn-confirm" onclick={submitEditQuestion} disabled={savingEdit}>
					{savingEdit ? 'Đang lưu...' : 'Lưu chỉnh sửa'}
				</button>
			</div>
		</div>
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

	.bookmark-btn {
		width: 32px;
		height: 32px;
		border-radius: 4px;
		border: 1px solid #babfc4;
		background: white;
		font-size: 0.9rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 0.5rem;
		transition: all 0.15s;
	}

	.bookmark-btn:hover {
		background: #fdf7e7;
		border-color: #f48225;
	}

	.bookmark-btn.bookmarked {
		background: #fef3d6;
		border-color: #f48225;
		box-shadow: 0 0 0 2px rgba(244, 130, 37, 0.2);
	}

	.so-right-col {
		width: 300px;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		flex-shrink: 0;
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

	.bounty-banner {
		background: #fdf7e7;
		border: 1px solid #f48225;
		border-radius: 4px;
		padding: 0.8rem 1rem;
		margin-bottom: 1.2rem;
		display: flex;
		align-items: center;
		gap: 0.8rem;
		font-size: 0.88rem;
		color: #3b4045;
	}

	.bounty-badge {
		background: #f48225;
		color: white;
		font-weight: 700;
		padding: 0.25rem 0.6rem;
		border-radius: 3px;
		font-size: 0.82rem;
	}

	.closed-banner {
		background: #fdf2f2;
		border: 1px solid #d63384;
		border-radius: 4px;
		padding: 0.8rem 1rem;
		margin-bottom: 1.2rem;
		font-size: 0.88rem;
		color: #842029;
	}

	.post-actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.action-btn {
		background: none;
		border: none;
		color: #6a737c;
		font-size: 0.78rem;
		cursor: pointer;
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
	}

	.action-btn:hover {
		background: #e3e6e8;
		color: #0c0d0e;
	}

	.action-btn.bounty-btn {
		color: #b28d00;
		font-weight: 600;
	}

	.action-btn.close-btn {
		color: #c02d0e;
	}

	.answer-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.tab-toggle {
		display: flex;
		border: 1px solid #babfc4;
		border-radius: 3px;
		overflow: hidden;
	}

	.tab-toggle button {
		background: white;
		border: none;
		padding: 0.3rem 0.6rem;
		font-size: 0.78rem;
		color: #6a737c;
		cursor: pointer;
	}

	.tab-toggle button.active {
		background: #e3e6e8;
		color: #0c0d0e;
		font-weight: 600;
	}

	.preview-box {
		border: 1px solid #e3e6e8;
		border-radius: 4px;
		padding: 1rem;
		min-height: 120px;
		background: #f8f9fa;
	}

	.empty-preview {
		color: #838c95;
		font-size: 0.88rem;
		font-style: italic;
	}

	.closed-notice {
		color: #842029;
		font-weight: 500;
		font-size: 0.9rem;
		margin-top: 1.5rem;
	}

	/* Modal CSS */
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		background: rgba(0, 0, 0, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		border-radius: 6px;
		padding: 1.5rem;
		width: 90%;
		max-width: 550px;
		max-height: 85vh;
		overflow-y: auto;
		box-shadow: 0 4px 12px rgba(0,0,0,0.15);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.modal-header h3 {
		margin: 0;
		font-size: 1.2rem;
	}

	.close-btn-icon {
		background: none;
		border: none;
		font-size: 1.5rem;
		cursor: pointer;
		color: #6a737c;
	}

	.revisions-list {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}

	.revision-item {
		border: 1px solid #e3e6e8;
		border-radius: 4px;
		padding: 0.8rem;
		background: #f8f9fa;
	}

	.rev-header {
		display: flex;
		justify-content: space-between;
		font-size: 0.82rem;
		color: #232629;
	}

	.rev-meta {
		color: #6a737c;
	}

	.rev-comment {
		font-size: 0.8rem;
		color: #0074cc;
		margin: 0.3rem 0;
	}

	.rev-title {
		font-size: 0.95rem;
		margin: 0.4rem 0;
	}

	.rev-body {
		font-size: 0.85rem;
		background: white;
		padding: 0.6rem;
		border-radius: 3px;
		border: 1px solid #e3e6e8;
	}

	.bounty-options {
		display: flex;
		gap: 0.6rem;
		margin: 1rem 0;
	}

	.bounty-options button {
		flex: 1;
		padding: 0.6rem;
		border: 1px solid #babfc4;
		background: white;
		border-radius: 4px;
		font-weight: 600;
		cursor: pointer;
	}

	.bounty-options button.active {
		border-color: #f48225;
		background: #fdf7e7;
		color: #f48225;
	}

	.modal-input {
		width: 100%;
		padding: 0.6rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		margin: 0.8rem 0;
		font-size: 0.9rem;
	}

	.modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.6rem;
		margin-top: 1rem;
	}

	.btn-cancel {
		background: white;
		border: 1px solid #babfc4;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		cursor: pointer;
	}

	.btn-confirm {
		background: #0a95ff;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		font-weight: 600;
		cursor: pointer;
	}

	.btn-confirm.danger {
		background: #c02d0e;
	}

	.error {
		color: #c02d0e;
	}

	.empty {
		color: #6a737c;
		font-size: 0.9rem;
	}


	/* Sửa câu hỏi (modal) & sửa câu trả lời (inline) */
	.edit-modal {
		max-width: 640px;
	}

	.edit-label {
		display: block;
		font-size: 0.85rem;
		font-weight: 600;
		color: #232629;
		margin: 0.6rem 0 0.3rem;
	}

	.edit-textarea {
		width: 100%;
		padding: 0.6rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.92rem;
		font-family: inherit;
		resize: vertical;
	}

	.edit-textarea:focus {
		outline: none;
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}

	.edit-tab-toggle {
		display: flex;
		border: 1px solid #babfc4;
		border-radius: 3px;
		overflow: hidden;
		width: fit-content;
		margin-top: 0.5rem;
	}

	.edit-tab-toggle button {
		background: white;
		border: none;
		padding: 0.25rem 0.7rem;
		font-size: 0.8rem;
		color: #6a737c;
		cursor: pointer;
	}

	.edit-tab-toggle button.active {
		background: #e3e6e8;
		color: #0c0d0e;
		font-weight: 600;
	}

	.answer-edit-box {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.answer-edit-box textarea {
		width: 100%;
		padding: 0.6rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.92rem;
		font-family: inherit;
		resize: vertical;
	}

	.answer-edit-box textarea:focus {
		outline: none;
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}

	.answer-edit-actions {
		display: flex;
		gap: 0.5rem;
	}

	.answer-actions {
		display: flex;
		gap: 0.5rem;
	}

	.save-btn {
		background: #0a95ff;
		color: white;
		border-color: #0a95ff;
	}

	.save-btn:hover:not(:disabled) {
		background: #0074cc;
		border-color: #0074cc;
	}

	.action-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>
