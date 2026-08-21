<script lang="ts">
	import { onMount } from 'svelte';
	import {
		listComments,
		createComment,
		deleteComment,
		ApiError,
		type Comment
	} from '$lib/api/client';
	import { currentUser, PRIVILEGE } from '$lib/stores/auth';

	let { targetType, targetId, ownerId }: {
		targetType: 'question' | 'answer';
		targetId: string;
		ownerId: string;
	} = $props();

	let comments = $state<Comment[]>([]);
	let newContent = $state('');
	let loading = $state(true);
	let posting = $state(false);
	let errorMsg = $state('');
	let expanded = $state(false);

	async function load() {
		loading = true;
		try {
			const res = await listComments(targetType, targetId);
			comments = res.comments;
		} catch {
			// im lặng - bình luận không phải nội dung bắt buộc phải tải thành công
		} finally {
			loading = false;
		}
	}

	onMount(load);

	// Dưới 50 rep chỉ bình luận được bài của chính mình - hiện tooltip đúng lý do trước khi user bấm gửi
	let isOwnPost = $derived($currentUser?.id === ownerId);
	let canComment = $derived(
		!!$currentUser && (isOwnPost || ($currentUser.reputation ?? 0) >= PRIVILEGE.COMMENT_ON_OTHERS)
	);

	async function submit(e: Event) {
		e.preventDefault();
		if (!newContent.trim()) return;
		posting = true;
		errorMsg = '';
		try {
			const res = await createComment(targetType, targetId, newContent.trim());
			comments = [...comments, res.comment];
			newContent = '';
		} catch (err) {
			if (err instanceof ApiError) {
				const detail = err.detail as { error?: string } | string;
				errorMsg = typeof detail === 'string' ? detail : detail.error || 'Bình luận thất bại';
			} else {
				errorMsg = 'Bình luận thất bại';
			}
		} finally {
			posting = false;
		}
	}

	async function remove(id: string) {
		try {
			await deleteComment(id);
			comments = comments.filter((c) => c.id !== id);
		} catch {
			// bỏ qua - nút xóa chỉ hiện cho người có quyền nên hiếm khi lỗi
		}
	}
</script>

<div class="comments-block">
	{#if !expanded}
		<button class="toggle-link" onclick={() => (expanded = true)}>
			💬 {loading ? 'Bình luận' : `${comments.length} bình luận`}
		</button>
	{:else}
		<div class="comments-list">
			{#each comments as c}
				<div class="comment-row">
					<span class="comment-content">{c.content}</span>
					{#if $currentUser && ($currentUser.id === c.authorId || $currentUser.isAdmin)}
						<button class="delete-link" onclick={() => remove(c.id)}>xóa</button>
					{/if}
				</div>
			{/each}
			{#if comments.length === 0}
				<p class="no-comments">Chưa có bình luận nào.</p>
			{/if}
		</div>

		{#if $currentUser}
			<form class="comment-form" onsubmit={submit}>
				<input
					bind:value={newContent}
					maxlength="1000"
					placeholder={canComment
						? 'Thêm bình luận...'
						: `Cần >= ${PRIVILEGE.COMMENT_ON_OTHERS} reputation để bình luận bài người khác`}
					disabled={!canComment}
				/>
				<button type="submit" disabled={posting || !canComment || !newContent.trim()}>Gửi</button>
			</form>
			{#if errorMsg}<p class="error">{errorMsg}</p>{/if}
		{/if}
	{/if}
</div>

<style>
	.comments-block {
		margin-top: 0.6rem;
	}
	.toggle-link {
		background: none;
		border: none;
		color: #6a7685;
		font-size: 0.82rem;
		cursor: pointer;
		padding: 0;
	}
	.toggle-link:hover {
		color: #0074cc;
	}
	.comments-list {
		border-top: 1px solid #f0f1f3;
		padding-top: 0.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	.comment-row {
		font-size: 0.85rem;
		color: #3b4759;
		display: flex;
		justify-content: space-between;
		gap: 0.5rem;
	}
	.comment-content {
		flex: 1;
	}
	.delete-link {
		background: none;
		border: none;
		color: #d63384;
		font-size: 0.75rem;
		cursor: pointer;
		padding: 0;
	}
	.no-comments {
		font-size: 0.82rem;
		color: #b0b8c1;
		margin: 0;
	}
	.comment-form {
		display: flex;
		gap: 0.5rem;
		margin-top: 0.6rem;
	}
	.comment-form input {
		flex: 1;
		padding: 0.4rem 0.6rem;
		border: 1px solid #e0e3e8;
		border-radius: 5px;
		font-size: 0.85rem;
	}
	.comment-form button {
		padding: 0.4rem 0.9rem;
		border: none;
		border-radius: 5px;
		background: #f0f5fb;
		color: #0074cc;
		font-size: 0.82rem;
		cursor: pointer;
	}
	.comment-form button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.error {
		font-size: 0.78rem;
		color: #d63384;
		margin: 0.3rem 0 0;
	}
</style>
