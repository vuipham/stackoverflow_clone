<script lang="ts">
	import { currentUser } from '$lib/stores/auth';
</script>

<section class="hero">
	<h1>Hệ thống quản trị tri thức</h1>
	<p>
		Đặt câu hỏi, chia sẻ kiến thức, tìm kiếm bài viết theo tiêu đề bằng mô hình
		Vector Space Model (TF-IDF / Sentence-BERT) + Cosine Similarity.
	</p>
	<div class="actions">
		<a class="btn primary" href="/questions">Xem câu hỏi</a>
		{#if $currentUser}
			<a class="btn" href="/ask">Đặt câu hỏi mới</a>
		{:else}
			<a class="btn" href="/register">Bắt đầu ngay</a>
		{/if}
	</div>
</section>

<style>
	.hero {
		text-align: center;
		padding: 3rem 1rem;
	}
	h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	p {
		color: #5b6673;
		max-width: 560px;
		margin: 0 auto 1.5rem;
	}
	.actions {
		display: flex;
		gap: 0.75rem;
		justify-content: center;
	}
	.btn {
		text-decoration: none;
		padding: 0.6rem 1.2rem;
		border-radius: 8px;
		border: 1px solid #0074cc;
		color: #0074cc;
		font-weight: 500;
	}
	.btn.primary {
		background: #0074cc;
		color: white;
	}
</style>
