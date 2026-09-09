<script lang="ts">
	import { onMount } from 'svelte';
	import { listTags, type Tag } from '$lib/api/client';

	let tags = $state<Tag[]>([]);
	let searchQuery = $state('');
	let loading = $state(true);
	let errorMsg = $state('');

	let filteredTags = $derived(
		tags.filter(
			(t) =>
				t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(t.description && t.description.toLowerCase().includes(searchQuery.toLowerCase()))
		)
	);

	onMount(async () => {
		try {
			const res = await listTags();
			tags = res.tags;
		} catch {
			errorMsg = 'Không thể tải danh sách thẻ.';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Thẻ (Tags) - Knowledge Hub</title>
</svelte:head>

<div class="tags-page">
	<div class="page-header">
		<h1>🏷️ Thẻ (Tags)</h1>
		<p class="subtitle">Thẻ là nhãn phân loại câu hỏi giúp tìm kiếm và theo dõi các chủ đề bạn quan tâm.</p>
	</div>

	<div class="search-bar">
		<input
			type="text"
			bind:value={searchQuery}
			placeholder="Lọc thẻ theo tên hoặc mô tả..."
		/>
	</div>

	{#if loading}
		<p class="muted">Đang tải danh sách thẻ...</p>
	{:else if errorMsg}
		<p class="error">{errorMsg}</p>
	{:else if filteredTags.length === 0}
		<p class="empty">Không tìm thấy thẻ nào khớp với từ khóa "{searchQuery}".</p>
	{:else}
		<div class="tags-grid">
			{#each filteredTags as t}
				<div class="tag-card">
					<div class="card-top">
						<a href={`/questions?tag=${encodeURIComponent(t.name)}`} class="tag-badge">{t.name}</a>
						<span class="count">{t.questionCount.toLocaleString('vi-VN')} câu hỏi</span>
					</div>
					<p class="description">
						{t.description || 'Chưa có mô tả chi tiết cho thẻ này.'}
					</p>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.tags-page {
		max-width: 1000px;
	}

	.page-header {
		margin-bottom: 1.2rem;
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

	.search-bar {
		margin-bottom: 1.5rem;
	}

	.search-bar input {
		width: 100%;
		max-width: 350px;
		padding: 0.5rem 0.8rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.9rem;
		outline: none;
	}

	.search-bar input:focus {
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}

	.tags-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 1rem;
	}

	.tag-card {
		background: white;
		border: 1px solid #d6d9dc;
		border-radius: 4px;
		padding: 0.8rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.card-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.tag-badge {
		background: #e1ecf4;
		color: #39739d;
		font-size: 0.82rem;
		padding: 0.2rem 0.5rem;
		border-radius: 3px;
		text-decoration: none;
		font-weight: 500;
	}

	.tag-badge:hover {
		background: #b3d3ea;
	}

	.count {
		font-size: 0.75rem;
		color: #6a737c;
	}

	.description {
		font-size: 0.8rem;
		color: #525960;
		margin: 0;
		line-height: 1.35;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.muted {
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
