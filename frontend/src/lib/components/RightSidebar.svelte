<script lang="ts">
	let hotQuestions = [
		{ id: '1', title: 'Cách tối ưu truy vấn MongoDB trên 1.000.000 bản ghi?' },
		{ id: '2', title: 'Phân biệt giữa TF-IDF và Vector Embeddings trong Semantic Search?' },
		{ id: '3', title: 'Tại sao FastAPI nhanh hơn Flask trong xử lý bất đồng bộ?' },
		{ id: '4', title: 'Best practice thiết lập JWT Authentication trong microservices?' },
		{ id: '5', title: 'Cách phòng chống SQL Injection và XSS trong web app?' }
	];
</script>

<aside class="so-sidebar">
	<!-- Yellow Meta Widget -->
	<div class="sidebar-box yellow-box">
		<div class="box-header">The Overflow Blog</div>
		<ul class="box-list">
			<li>
				<span class="icon">✏️</span>
				<a href="/questions">Tối ưu hóa công cụ tìm kiếm tri thức quy mô 1 triệu bản ghi</a>
			</li>
			<li>
				<span class="icon">✏️</span>
				<a href="/questions">Hệ thống tính điểm Reputation và Phân quyền theo ngưỡng</a>
			</li>
		</ul>
		<div class="box-header">Featured on Meta</div>
		<ul class="box-list">
			<li>
				<span class="icon">💬</span>
				<a href="/questions">Thảo luận về nâng cấp thuật toán TF-IDF Search Engine</a>
			</li>
		</ul>
	</div>

	<!-- Hot Questions Widget -->
	<div class="sidebar-box">
		<div class="box-header plain">Hot Network Questions</div>
		<ul class="hot-list">
			{#each hotQuestions as hq}
				<li>
					<span class="hot-icon">🔥</span>
					<a href="/questions">{hq.title}</a>
				</li>
			{/each}
		</ul>
	</div>
</aside>

<style>
	.so-sidebar {
		width: 300px;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		flex-shrink: 0;
	}

	.sidebar-box {
		border: 1px solid #d6d9dc;
		border-radius: 4px;
		background: white;
		overflow: hidden;
		box-shadow: 0 1px 2px rgba(0,0,0,0.05);
	}

	.sidebar-box.yellow-box {
		background: #fdf7e7;
		border-color: #f1e5bc;
	}

	.box-header {
		padding: 0.6rem 0.8rem;
		font-size: 0.82rem;
		font-weight: bold;
		color: #525960;
		border-bottom: 1px solid #f1e5bc;
		background: #fbf3d5;
	}

	.box-header.plain {
		background: #f8f9fa;
		border-bottom: 1px solid #d6d9dc;
		color: #232629;
	}

	.box-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.box-list li {
		padding: 0.6rem 0.8rem;
		display: flex;
		gap: 0.5rem;
		font-size: 0.82rem;
		border-bottom: 1px solid #f1e5bc;
	}

	.box-list li:last-child {
		border-bottom: none;
	}

	.box-list a {
		color: #3b4045;
		text-decoration: none;
		line-height: 1.35;
	}

	.box-list a:hover {
		color: #0074cc;
	}

	.hot-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.hot-list li {
		padding: 0.6rem 0.8rem;
		display: flex;
		gap: 0.5rem;
		font-size: 0.82rem;
		border-bottom: 1px solid #e3e6e8;
	}

	.hot-list li:last-child {
		border-bottom: none;
	}

	.hot-list a {
		color: #0074cc;
		text-decoration: none;
		line-height: 1.35;
	}

	.hot-list a:hover {
		color: #0a95ff;
	}

	.hot-icon {
		font-size: 0.9rem;
	}
</style>
