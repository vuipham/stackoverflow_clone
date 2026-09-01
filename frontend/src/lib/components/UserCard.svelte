<script lang="ts">
	import type { AuthorInfo } from '$lib/api/client';

	let { author, date, label = 'đã đăng' }: { author?: AuthorInfo | null; date: string; label?: string } = $props();

	function formatDate(d: string) {
		try {
			return new Date(d).toLocaleDateString('vi-VN', {
				day: 'numeric',
				month: 'numeric',
				year: 'numeric',
				hour: '2-digit',
				minute: '2-digit'
			});
		} catch {
			return d;
		}
	}
</script>

<div class="user-card">
	<div class="card-action-time">{label} {formatDate(date)}</div>
	<div class="user-details">
		<div class="avatar-box">
			{(author?.displayName ?? 'U').charAt(0).toUpperCase()}
		</div>
		<div class="user-info-meta">
			<span class="user-name">{author?.displayName ?? 'Thành viên'}</span>
			<span class="user-rep">{author?.reputation?.toLocaleString('vi-VN') ?? 1} <small>rep</small></span>
		</div>
	</div>
</div>

<style>
	.user-card {
		background: #e1ecf4;
		border-radius: 4px;
		padding: 0.5rem 0.7rem;
		min-width: 170px;
		font-size: 0.78rem;
		color: #525960;
		box-sizing: border-box;
	}

	.card-action-time {
		color: #6a737c;
		margin-bottom: 0.35rem;
		font-size: 0.75rem;
	}

	.user-details {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.avatar-box {
		width: 32px;
		height: 32px;
		border-radius: 4px;
		background: #0074cc;
		color: white;
		font-weight: bold;
		font-size: 0.95rem;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.user-info-meta {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.user-name {
		color: #0074cc;
		font-weight: 600;
	}

	.user-rep {
		color: #6a737c;
		font-weight: bold;
		font-size: 0.75rem;
	}

	.user-rep small {
		font-weight: normal;
		color: #838c95;
	}
</style>
