<script lang="ts">
	import { onMount } from 'svelte';
	import { currentUser } from '$lib/stores/auth';
	import {
		listNotifications,
		getUnreadCount,
		markAllRead,
		markOneRead,
		type Notification
	} from '$lib/api/client';

	let open = $state(false);
	let unread = $state(0);
	let notifications = $state<Notification[]>([]);
	let loading = $state(false);

	const EVENT_LABELS: Record<string, string> = {
		new_answer: '💬 trả lời câu hỏi của bạn',
		new_comment: '🗨️ bình luận bài của bạn',
		answer_accepted: '✅ câu trả lời của bạn được chấp nhận',
		question_upvoted: '▲ upvote câu hỏi của bạn',
		answer_upvoted: '▲ upvote câu trả lời của bạn'
	};

	async function fetchCount() {
		if (!$currentUser) return;
		try {
			const res = await getUnreadCount();
			unread = res.unreadCount;
		} catch {
			// lỗi đếm thông báo không chặn UI
		}
	}

	async function openPanel() {
		open = !open;
		if (open) {
			loading = true;
			try {
				const res = await listNotifications(1, 20);
				notifications = res.notifications;
			} finally {
				loading = false;
			}
		}
	}

	async function handleMarkAll() {
		await markAllRead();
		notifications = notifications.map((n) => ({ ...n, isRead: true }));
		unread = 0;
	}

	async function handleClick(n: Notification) {
		if (!n.isRead) {
			await markOneRead(n.id);
			notifications = notifications.map((x) => (x.id === n.id ? { ...x, isRead: true } : x));
			unread = Math.max(0, unread - 1);
		}
		window.location.href = `/questions/${n.questionId}`;
	}

	onMount(() => {
		fetchCount();
		// Poll mỗi 30s để cập nhật số thông báo chưa đọc
		const interval = setInterval(fetchCount, 30000);
		return () => clearInterval(interval);
	});
</script>

{#if $currentUser}
	<div class="notif-wrapper">
		<button class="bell-btn" onclick={openPanel} title="Thông báo" id="notif-bell-btn">
			🔔
			{#if unread > 0}
				<span class="badge">{unread > 99 ? '99+' : unread}</span>
			{/if}
		</button>

		{#if open}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="backdrop" onclick={() => (open = false)}></div>
			<div class="panel" id="notif-panel">
				<div class="panel-header">
					<span>Thông báo</span>
					{#if notifications.some((n) => !n.isRead)}
						<button class="mark-all-btn" onclick={handleMarkAll}>Đánh dấu tất cả đã đọc</button>
					{/if}
				</div>

				{#if loading}
					<p class="empty">Đang tải...</p>
				{:else if notifications.length === 0}
					<p class="empty">Chưa có thông báo nào.</p>
				{:else}
					<ul class="notif-list">
						{#each notifications as n}
							<!-- svelte-ignore a11y_click_events_have_key_events -->
							<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
							<li class:unread={!n.isRead} onclick={() => handleClick(n)}>
								<div class="notif-meta">
									<strong>{n.actorName}</strong>
									{EVENT_LABELS[n.eventType] ?? n.eventType}
								</div>
								<div class="notif-title">"{n.questionTitle}"</div>
								<div class="notif-time">
									{new Date(n.createdAt).toLocaleString('vi-VN')}
								</div>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		{/if}
	</div>
{/if}

<style>
	.notif-wrapper {
		position: relative;
	}

	.bell-btn {
		background: none;
		border: none;
		font-size: 1.2rem;
		cursor: pointer;
		padding: 0.3rem 0.5rem;
		border-radius: 4px;
		position: relative;
		line-height: 1;
	}

	.bell-btn:hover {
		background: rgba(255, 255, 255, 0.15);
	}

	.badge {
		position: absolute;
		top: -2px;
		right: -4px;
		background: #c02d0e;
		color: white;
		font-size: 0.6rem;
		font-weight: 700;
		min-width: 16px;
		height: 16px;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 3px;
		line-height: 1;
	}

	.backdrop {
		position: fixed;
		inset: 0;
		z-index: 99;
	}

	.panel {
		position: absolute;
		right: 0;
		top: calc(100% + 8px);
		width: 360px;
		background: white;
		border: 1px solid #d6d9dc;
		border-radius: 6px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
		z-index: 100;
		overflow: hidden;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #e3e6e8;
		font-weight: 600;
		font-size: 0.9rem;
		color: #232629;
	}

	.mark-all-btn {
		background: none;
		border: none;
		font-size: 0.75rem;
		color: #0a95ff;
		cursor: pointer;
		padding: 0;
	}

	.mark-all-btn:hover {
		text-decoration: underline;
	}

	.notif-list {
		list-style: none;
		margin: 0;
		padding: 0;
		max-height: 420px;
		overflow-y: auto;
	}

	.notif-list li {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #f0f0f0;
		cursor: pointer;
		transition: background 0.15s;
	}

	.notif-list li:hover {
		background: #f8f9f9;
	}

	.notif-list li.unread {
		background: #f0f7ff;
		border-left: 3px solid #0a95ff;
	}

	.notif-list li.unread:hover {
		background: #e6f2ff;
	}

	.notif-meta {
		font-size: 0.82rem;
		color: #3d4144;
		margin-bottom: 0.2rem;
	}

	.notif-title {
		font-size: 0.8rem;
		color: #232629;
		font-style: italic;
		margin-bottom: 0.2rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.notif-time {
		font-size: 0.72rem;
		color: #9199a1;
	}

	.empty {
		padding: 1.5rem 1rem;
		text-align: center;
		color: #6a737c;
		font-size: 0.85rem;
		margin: 0;
	}
</style>
