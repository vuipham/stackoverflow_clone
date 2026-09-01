<script lang="ts">
	import { onMount } from 'svelte';
	import { createQuestion, ApiError } from '$lib/api/client';
	import { currentUser, authReady } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';

	let title = $state('');
	let body = $state('');
	let tagsInput = $state('');
	let error = $state('');
	let loading = $state(false);
	let activeTab = $state<'write' | 'preview'>('write');

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

<div class="ask-container">
	<div class="ask-main">
		<h1>Đặt một câu hỏi công khai</h1>

		<!-- SO Tip Box -->
		<div class="so-notice-box">
			<h3>Viết một câu hỏi tốt</h3>
			<p>Bạn đã sẵn sàng đặt câu hỏi lập trình. Dưới đây là các gợi ý giúp câu hỏi của bạn nhanh nhận được câu trả lời tốt nhất:</p>
			<ul>
				<li>Tóm tắt vấn đề cụ thể trong tiêu đề ngắn gọn.</li>
				<li>Mô tả chi tiết kịch bản, các bước đã thử và mã lỗi (nếu có).</li>
				<li>Thêm đoạn mã nguồn (code snippet) minh họa.</li>
				<li>Gán từ khóa (tags) chính xác với công nghệ sử dụng.</li>
			</ul>
		</div>

		<form onsubmit={handleSubmit} class="ask-form">
			<!-- Title Card -->
			<div class="form-card">
				<label for="q-title" class="card-label">Tiêu đề</label>
				<span class="card-desc">Hãy cụ thể và hình dung bạn đang đặt câu hỏi cho một đồng nghiệp.</span>
				<input
					id="q-title"
					bind:value={title}
					required
					minlength="5"
					placeholder="Ví dụ: Làm thế nào để tối ưu truy vấn MongoDB với 1.000.000 bản ghi?"
				/>
			</div>

			<!-- Body Card with Live Preview -->
			<div class="form-card">
				<div class="body-header">
					<div>
						<label for="q-body" class="card-label">Nội dung chi tiết</label>
						<span class="card-desc">Bao gồm tất cả thông tin mà ai đó cần để giải đáp câu hỏi của bạn. Hỗ trợ Markdown.</span>
					</div>
					<div class="tab-toggle">
						<button
							type="button"
							class="tab-btn"
							class:active={activeTab === 'write'}
							onclick={() => (activeTab = 'write')}
						>
							Soạn thảo
						</button>
						<button
							type="button"
							class="tab-btn"
							class:active={activeTab === 'preview'}
							onclick={() => (activeTab = 'preview')}
						>
							Xem trước
						</button>
					</div>
				</div>

				{#if activeTab === 'write'}
					<textarea
						id="q-body"
						bind:value={body}
						required
						rows="10"
						placeholder="Mô tả chi tiết vấn đề, dán mã nguồn dùng syntax ```code```..."
					></textarea>
				{:else}
					<div class="preview-box">
						{#if body.trim()}
							<MarkdownRenderer content={body} />
						{:else}
							<p class="empty-preview">Chưa có nội dung để xem trước...</p>
						{/if}
					</div>
				{/if}
			</div>

			<!-- Tags Card -->
			<div class="form-card">
				<label for="q-tags" class="card-label">Thẻ (Tags)</label>
				<span class="card-desc">Thêm tối đa 5 thẻ để mô tả chủ đề câu hỏi (phân cách bằng dấu phẩy).</span>
				<input
					id="q-tags"
					bind:value={tagsInput}
					placeholder="vd: python, fastapi, mongodb, redis"
				/>
			</div>

			{#if error}<p class="error">{error}</p>{/if}

			<button type="submit" class="btn-submit" disabled={loading}>
				{loading ? 'Đang đăng câu hỏi...' : 'Đăng câu hỏi của bạn'}
			</button>
		</form>
	</div>
</div>

<style>
	.ask-container {
		max-width: 850px;
		margin: 0 auto;
	}

	h1 {
		font-size: 1.6rem;
		color: #232629;
		margin-bottom: 1.2rem;
	}

	.so-notice-box {
		background: #ebf5fb;
		border: 1px solid #a6d3f2;
		border-radius: 4px;
		padding: 1.2rem;
		margin-bottom: 1.5rem;
	}

	.so-notice-box h3 {
		margin: 0 0 0.5rem;
		font-size: 1.1rem;
		color: #0074cc;
	}

	.so-notice-box p {
		margin: 0 0 0.6rem;
		font-size: 0.88rem;
		color: #3b4045;
	}

	.so-notice-box ul {
		margin: 0;
		padding-left: 1.2rem;
		font-size: 0.85rem;
		color: #3b4045;
	}

	.so-notice-box li {
		margin-bottom: 0.3rem;
	}

	.ask-form {
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}

	.form-card {
		background: white;
		border: 1px solid #e3e6e8;
		border-radius: 4px;
		padding: 1.2rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		box-shadow: 0 1px 3px rgba(0,0,0,0.04);
	}

	.card-label {
		font-weight: 600;
		font-size: 0.95rem;
		color: #0c0d0e;
	}

	.card-desc {
		font-size: 0.8rem;
		color: #6a737c;
		margin-bottom: 0.4rem;
	}

	input,
	textarea {
		padding: 0.7rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.95rem;
		font-family: inherit;
		outline: none;
	}

	input:focus,
	textarea:focus {
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}

	.body-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
	}

	.tab-toggle {
		display: flex;
		border: 1px solid #babfc4;
		border-radius: 3px;
		overflow: hidden;
	}

	.tab-btn {
		background: white;
		border: none;
		padding: 0.3rem 0.7rem;
		font-size: 0.8rem;
		color: #6a737c;
		cursor: pointer;
	}

	.tab-btn.active {
		background: #e3e6e8;
		color: #0c0d0e;
		font-weight: 600;
	}

	.preview-box {
		border: 1px solid #e3e6e8;
		border-radius: 4px;
		padding: 1rem;
		min-height: 180px;
		background: #f8f9fa;
	}

	.empty-preview {
		color: #838c95;
		font-size: 0.88rem;
		font-style: italic;
	}

	.btn-submit {
		align-self: flex-start;
		padding: 0.7rem 1.4rem;
		border: none;
		border-radius: 4px;
		background: #0a95ff;
		color: white;
		font-weight: 600;
		font-size: 0.9rem;
		cursor: pointer;
	}

	.btn-submit:hover:not(:disabled) {
		background: #0074cc;
	}

	.btn-submit:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		color: #c02d0e;
		font-size: 0.88rem;
	}
</style>
