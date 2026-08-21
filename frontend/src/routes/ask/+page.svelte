<script lang="ts">
	import { onMount } from 'svelte';
	import { createQuestion, ApiError } from '$lib/api/client';
	import { currentUser, authReady } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let title = $state('');
	let body = $state('');
	let tagsInput = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		const unsub = authReady.subscribe((ready) => {
			if (ready && !$currentUser) goto('/login');
		});
		return unsub;
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const tags = tagsInput
				.split(',')
				.map((t) => t.trim().toLowerCase())
				.filter(Boolean);
			const { question } = await createQuestion({ title, body, tags });
			goto(`/questions/${question.id}`);
		} catch (err) {
			if (err instanceof ApiError) {
				const detail = err.detail as { error?: string } | string;
				error = typeof detail === 'string' ? detail : detail.error || 'Tạo câu hỏi thất bại';
			} else {
				error = 'Tạo câu hỏi thất bại';
			}
		} finally {
			loading = false;
		}
	}
</script>

<h1>Đặt câu hỏi mới</h1>

<form onsubmit={handleSubmit}>
	<label>
		Tiêu đề
		<input bind:value={title} required minlength="5" placeholder="Câu hỏi của bạn là gì?" />
	</label>
	<label>
		Nội dung
		<textarea bind:value={body} required rows="6" placeholder="Mô tả chi tiết..."></textarea>
	</label>
	<label>
		Tags (cách nhau bằng dấu phẩy)
		<input bind:value={tagsInput} placeholder="nlp, search, mongodb" />
	</label>

	{#if error}<p class="error">{error}</p>{/if}

	<button type="submit" disabled={loading}>{loading ? 'Đang đăng...' : 'Đăng câu hỏi'}</button>
</form>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		max-width: 600px;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.9rem;
		color: #3b4759;
	}
	input,
	textarea {
		padding: 0.6rem 0.7rem;
		border: 1px solid #d0d5dd;
		border-radius: 6px;
		font-size: 0.95rem;
		font-family: inherit;
	}
	button {
		align-self: flex-start;
		padding: 0.6rem 1.4rem;
		border: none;
		border-radius: 6px;
		background: #0074cc;
		color: white;
		font-weight: 600;
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.error {
		color: #d63384;
		font-size: 0.85rem;
	}
</style>
