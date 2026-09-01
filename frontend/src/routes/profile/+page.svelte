<script lang="ts">
	import { onMount } from 'svelte';
	import { getMyProfile, ApiError, type UserProfile } from '$lib/api/client';
	import { currentUser, authReady } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let profile = $state<UserProfile | null>(null);
	let loading = $state(true);
	let errorMsg = $state('');
	let activeTab = $state<'reputation' | 'questions' | 'answers'>('questions');

	onMount(() => {
		const unsub = authReady.subscribe((ready) => {
			if (ready) {
				if (!$currentUser) goto('/login');
				else loadProfile();
			}
		});
		return unsub;
	});

	async function loadProfile() {
		loading = true;
		errorMsg = '';
		try {
			profile = await getMyProfile();
		} catch (err) {
			errorMsg = err instanceof ApiError ? String(err.detail) : 'Không thể tải hồ sơ';
		} finally {
			loading = false;
		}
	}

	function reasonLabel(reason: string): string {
		const labels: Record<string, string> = {
			upvote_received: '▲ Bài viết được upvote',
			downvote_received: '▼ Bài viết bị downvote',
			downvote_cast: '▼ Chi phí downvote',
			upvote_cancelled: '↩ Upvote bị hủy',
			downvote_cancelled: '↩ Downvote bị hủy',
			upvote_reversed: '↔ Đổi upvote → downvote',
			downvote_reversed: '↔ Đổi downvote → upvote',
			downvote_cast_cancelled: '↩ Hoàn chi phí downvote',
			answer_accepted: '✔ Câu trả lời được chấp nhận',
			admin_adjust: '⚙️ Quản trị viên điều chỉnh'
		};
		return labels[reason] ?? reason;
	}
</script>

<svelte:head>
	<title>Hồ sơ cá nhân</title>
</svelte:head>

{#if loading}
	<p>Đang tải hồ sơ...</p>
{:else if errorMsg}
	<p class="error">{errorMsg}</p>
{:else if profile}
	<div class="profile-header">
		<div class="avatar">{profile.user.displayName[0]?.toUpperCase()}</div>
		<div>
			<h1>{profile.user.displayName}</h1>
			<p class="username">@{profile.user.username}{profile.user.isAdmin ? ' 👑 Admin' : ''}</p>
			<div class="rep-badge">
				<span class="rep-score">{profile.user.reputation}</span>
				<span class="rep-label">điểm reputation</span>
			</div>
		</div>
	</div>

	<div class="tabs">
		<button class:active={activeTab === 'questions'} onclick={() => (activeTab = 'questions')}>
			Câu hỏi ({profile.questions.length})
		</button>
		<button class:active={activeTab === 'answers'} onclick={() => (activeTab = 'answers')}>
			Câu trả lời ({profile.answers.length})
		</button>
		<button class:active={activeTab === 'reputation'} onclick={() => (activeTab = 'reputation')}>
			Lịch sử điểm ({profile.reputationLog.length})
		</button>
	</div>

	{#if activeTab === 'questions'}
		{#if profile.questions.length === 0}
			<p class="empty">Chưa có câu hỏi nào.</p>
		{:else}
			<ul class="item-list">
				{#each profile.questions as q}
					<li>
						<div class="item-stats">
							<span class:positive={q.voteScore > 0} class:negative={q.voteScore < 0}>
								{q.voteScore} votes
							</span>
							<span>{q.answerCount} trả lời</span>
						</div>
						<div class="item-content">
							<a href="/questions/{q.id}">{q.title}</a>
							<div class="tags">
								{#each q.tags as tag}
									<a href="/questions?tag={tag}" class="tag">{tag}</a>
								{/each}
							</div>
							<small class="meta">{new Date(q.createdAt).toLocaleDateString('vi-VN')}</small>
						</div>
					</li>
				{/each}
			</ul>
		{/if}

	{:else if activeTab === 'answers'}
		{#if profile.answers.length === 0}
			<p class="empty">Chưa có câu trả lời nào.</p>
		{:else}
			<ul class="item-list">
				{#each profile.answers as a}
					<li>
						<div class="item-stats">
							<span class:positive={a.voteScore > 0} class:negative={a.voteScore < 0}>
								{a.voteScore} votes
							</span>
							{#if a.isAccepted}<span class="accepted-mark">✔ Chấp nhận</span>{/if}
						</div>
						<div class="item-content">
							<a href="/questions/{a.questionId}">{a.body}</a>
							<small class="meta">{new Date(a.createdAt).toLocaleDateString('vi-VN')}</small>
						</div>
					</li>
				{/each}
			</ul>
		{/if}

	{:else if activeTab === 'reputation'}
		{#if profile.reputationLog.length === 0}
			<p class="empty">Chưa có lịch sử điểm nào.</p>
		{:else}
			<table class="rep-table">
				<thead>
					<tr><th>Thay đổi</th><th>Lý do</th><th>Thời gian</th></tr>
				</thead>
				<tbody>
					{#each profile.reputationLog as log}
						<tr>
							<td class="delta" class:positive={log.delta > 0} class:negative={log.delta < 0}>
								{log.delta > 0 ? '+' : ''}{log.delta}
							</td>
							<td>{reasonLabel(log.reason)}</td>
							<td class="meta">{log.at ? new Date(log.at).toLocaleString('vi-VN') : '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	{/if}
{/if}

<style>
	.profile-header {
		display: flex;
		gap: 1.2rem;
		align-items: center;
		margin-bottom: 2rem;
	}
	.avatar {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		background: #0074cc;
		color: white;
		font-size: 1.8rem;
		font-weight: 700;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}
	h1 {
		margin: 0;
		font-size: 1.4rem;
	}
	.username {
		color: #8a94a3;
		font-size: 0.9rem;
		margin: 0.2rem 0;
	}
	.rep-badge {
		display: inline-flex;
		align-items: baseline;
		gap: 0.3rem;
		margin-top: 0.3rem;
	}
	.rep-score {
		font-size: 1.5rem;
		font-weight: 700;
		color: #0074cc;
	}
	.rep-label {
		font-size: 0.8rem;
		color: #8a94a3;
	}
	.tabs {
		display: flex;
		gap: 0;
		border-bottom: 2px solid #eaecef;
		margin-bottom: 1.2rem;
	}
	.tabs button {
		padding: 0.55rem 1.1rem;
		border: none;
		background: none;
		cursor: pointer;
		font-size: 0.9rem;
		color: #5b6673;
		border-bottom: 2px solid transparent;
		margin-bottom: -2px;
	}
	.tabs button.active {
		color: #0074cc;
		border-bottom-color: #0074cc;
		font-weight: 600;
	}
	.item-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.item-list li {
		display: flex;
		gap: 1rem;
		padding: 0.9rem 0;
		border-bottom: 1px solid #eaecef;
	}
	.item-stats {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		min-width: 80px;
		font-size: 0.82rem;
		color: #5b6673;
		text-align: center;
	}
	.item-content {
		flex: 1;
	}
	.item-content a {
		color: #0074cc;
		text-decoration: none;
		font-weight: 500;
	}
	.item-content a:hover {
		text-decoration: underline;
	}
	.tags {
		display: flex;
		gap: 0.3rem;
		flex-wrap: wrap;
		margin: 0.3rem 0;
	}
	.tag {
		background: #e1ecf4;
		color: #39739d;
		text-decoration: none;
		font-size: 0.75rem;
		padding: 0.1rem 0.4rem;
		border-radius: 4px;
	}
	.meta {
		color: #9aa4b2;
		font-size: 0.78rem;
	}
	.positive {
		color: #1a7a3a;
		font-weight: 600;
	}
	.negative {
		color: #d63384;
		font-weight: 600;
	}
	.accepted-mark {
		color: #1a7a3a;
		font-size: 0.78rem;
	}
	.rep-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.87rem;
	}
	.rep-table th,
	.rep-table td {
		text-align: left;
		padding: 0.5rem 0.6rem;
		border-bottom: 1px solid #eaecef;
	}
	.rep-table th {
		color: #5b6673;
		font-weight: 600;
	}
	.delta {
		font-weight: 700;
		font-size: 1rem;
	}
	.empty {
		color: #8a94a3;
	}
	.error {
		color: #d63384;
	}
</style>
