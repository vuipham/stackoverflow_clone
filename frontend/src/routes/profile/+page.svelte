<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getMyProfile, getUserProfile, updateProfile, ApiError, type UserProfile } from '$lib/api/client';
	import { currentUser, authReady } from '$lib/stores/auth';
	import { showToast } from '$lib/stores/toast';
	import { goto } from '$app/navigation';

	let profile = $state<UserProfile & { badges?: { badgeCode: string; name: string; tier: string; description: string }[] } | null>(null);
	let loading = $state(true);
	let errorMsg = $state('');
	let activeTab = $state<'reputation' | 'questions' | 'answers' | 'badges'>('badges');

	// ---- Chỉnh sửa hồ sơ (UC009) ----
	let editing = $state(false);
	let editName = $state('');
	let editEmail = $state('');
	let saving = $state(false);
	let saveError = $state('');

	let isOwnProfile = $derived(
		!page.url.searchParams.get('id') || page.url.searchParams.get('id') === $currentUser?.id
	);

	function startEdit() {
		if (!profile) return;
		editName = profile.user.displayName;
		editEmail = profile.user.email ?? '';
		saveError = '';
		editing = true;
	}

	function cancelEdit() {
		editing = false;
		saveError = '';
	}

	async function saveProfile() {
		if (!profile) return;
		const name = editName.trim();
		const email = editEmail.trim();
		if (name.length < 3 || name.length > 50) {
			saveError = 'Tên hiển thị phải từ 3 đến 50 ký tự';
			return;
		}
		if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
			saveError = 'Email không hợp lệ';
			return;
		}
		// Chỉ gửi trường thực sự thay đổi
		const payload: { displayName?: string; email?: string } = {};
		if (name !== profile.user.displayName) payload.displayName = name;
		if (email !== (profile.user.email ?? '')) payload.email = email;
		if (Object.keys(payload).length === 0) {
			editing = false;
			return;
		}
		saving = true;
		saveError = '';
		try {
			const res = await updateProfile(payload);
			profile = { ...profile, user: { ...profile.user, ...res.user } };
			if ($currentUser) currentUser.set({ ...$currentUser, displayName: res.user.displayName, email: res.user.email });
			showToast(res.message || 'Đã cập nhật hồ sơ thành công', 'success');
			editing = false;
		} catch (err) {
			const msg = err instanceof ApiError ? String(err.detail) : 'Không thể cập nhật hồ sơ';
			saveError = msg;
			showToast(msg, 'error');
		} finally {
			saving = false;
		}
	}

	$effect(() => {
		const targetId = page.url.searchParams.get('id');
		if (targetId) {
			loadUserProfile(targetId);
		} else if ($authReady) {
			if (!$currentUser) {
				loading = false;
				goto('/login');
			} else {
				loadProfile();
			}
		}
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

	async function loadUserProfile(userId: string) {
		loading = true;
		errorMsg = '';
		try {
			profile = await getUserProfile(userId);
		} catch (err) {
			errorMsg = err instanceof ApiError ? String(err.detail) : 'Không thể tải hồ sơ người dùng';
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
			bounty_created: '💰 Treo thưởng Bounty',
			bounty_won: '💰 Nhận thưởng Bounty',
			admin_adjust: '⚙️ Quản trị viên điều chỉnh'
		};
		return labels[reason] ?? reason;
	}
</script>

<svelte:head>
	<title>{profile?.user.displayName ?? 'Hồ sơ người dùng'} - Knowledge Hub</title>
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
		{#if isOwnProfile && !editing}
			<button class="edit-btn" onclick={startEdit}>✏️ Chỉnh sửa hồ sơ</button>
		{/if}
	</div>

	{#if editing && isOwnProfile}
		<div class="edit-form">
			<h2>Chỉnh sửa hồ sơ</h2>
			<label>
				Tên hiển thị
				<input bind:value={editName} minlength="3" maxlength="50" placeholder="Ví dụ: Nguyễn Văn A" />
			</label>
			<label>
				Email
				<input type="email" bind:value={editEmail} placeholder="you@example.com" />
			</label>
			<p class="hint">Username không thể thay đổi.</p>
			{#if saveError}<p class="error">{saveError}</p>{/if}
			<div class="form-actions">
				<button class="btn-save" onclick={saveProfile} disabled={saving}>
					{saving ? 'Đang lưu...' : 'Lưu thay đổi'}
				</button>
				<button class="btn-cancel" onclick={cancelEdit} disabled={saving}>Hủy</button>
			</div>
		</div>
	{/if}

	<div class="tabs">
		<button class:active={activeTab === 'badges'} onclick={() => (activeTab = 'badges')}>
			🏆 Huy hiệu ({(profile.badges || []).length})
		</button>
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

	{#if activeTab === 'badges'}
		{#if !profile.badges || profile.badges.length === 0}
			<p class="empty">Chưa có huy hiệu nào. Hãy tham gia đặt câu hỏi và trả lời để nhận huy hiệu!</p>
		{:else}
			<div class="badges-grid">
				{#each profile.badges as b}
					<div class={`badge-card ${b.tier}`}>
						<span class="badge-icon">
							{b.tier === 'gold' ? '🥇' : b.tier === 'silver' ? '🥈' : '🥉'}
						</span>
						<div class="badge-info">
							<strong class="badge-title">{b.name}</strong>
							<p class="badge-desc">{b.description}</p>
						</div>
					</div>
				{/each}
			</div>
		{/if}

	{:else if activeTab === 'questions'}
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
	.edit-btn {
		align-self: flex-start;
		margin-left: auto;
		background: #f8f9fa;
		border: 1px solid #9fa6ad;
		border-radius: 4px;
		padding: 0.45rem 0.85rem;
		font-size: 0.82rem;
		color: #525960;
		cursor: pointer;
	}
	.edit-btn:hover {
		background: #f1f2f3;
		border-color: #0074cc;
		color: #0074cc;
	}
	.edit-form {
		background: #f8f9fa;
		border: 1px solid #d6d9dc;
		border-radius: 6px;
		padding: 1.2rem 1.4rem;
		margin-bottom: 1.4rem;
		display: flex;
		flex-direction: column;
		gap: 0.7rem;
	}
	.edit-form h2 {
		margin: 0;
		font-size: 1.05rem;
		color: #232629;
	}
	.edit-form label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.85rem;
		font-weight: 600;
		color: #3b4045;
	}
	.edit-form input {
		padding: 0.5rem 0.7rem;
		border: 1px solid #babfc4;
		border-radius: 4px;
		font-size: 0.9rem;
	}
	.edit-form input:focus {
		outline: none;
		border-color: #0a95ff;
		box-shadow: 0 0 0 3px rgba(10, 149, 255, 0.15);
	}
	.hint {
		margin: 0;
		font-size: 0.78rem;
		color: #8a94a3;
	}
	.success {
		margin: 0;
		color: #1a7a3a;
		font-size: 0.85rem;
	}
	.form-actions {
		display: flex;
		gap: 0.6rem;
	}
	.btn-save {
		background: #0a95ff;
		color: white;
		border: none;
		border-radius: 4px;
		padding: 0.5rem 1rem;
		font-size: 0.86rem;
		font-weight: 500;
		cursor: pointer;
	}
	.btn-save:hover {
		background: #0074cc;
	}
	.btn-save:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.btn-cancel {
		background: white;
		color: #525960;
		border: 1px solid #9fa6ad;
		border-radius: 4px;
		padding: 0.5rem 1rem;
		font-size: 0.86rem;
		cursor: pointer;
	}
	.btn-cancel:hover {
		background: #f1f2f3;
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
	.badges-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 1rem;
	}

	.badge-card {
		background: white;
		border: 1px solid #d6d9dc;
		border-radius: 6px;
		padding: 0.8rem;
		display: flex;
		align-items: flex-start;
		gap: 0.7rem;
	}

	.badge-card.bronze {
		border-left: 4px solid #ab6a15;
		background: #fffdf9;
	}

	.badge-card.silver {
		border-left: 4px solid #6a737c;
		background: #f8f9f9;
	}

	.badge-card.gold {
		border-left: 4px solid #b28d00;
		background: #fffdf0;
	}

	.badge-icon {
		font-size: 1.4rem;
		line-height: 1;
	}

	.badge-info {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.badge-title {
		font-size: 0.9rem;
		color: #232629;
	}

	.badge-desc {
		font-size: 0.78rem;
		color: #6a737c;
		margin: 0;
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
