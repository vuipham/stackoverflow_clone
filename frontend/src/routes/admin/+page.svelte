<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { currentUser, authReady } from '$lib/stores/auth';
	import {
		adminListUsers,
		adminBanUser,
		adminAdjustReputation,
		adminTriggerReindex,
		adminGetBenchmarkLog,
		listTags,
		updateTag,
		deleteTag,
		ApiError,
		type AdminUser,
		type Tag,
		type BenchmarkLogEntry
	} from '$lib/api/client';

	let users = $state<AdminUser[]>([]);
	let tags = $state<Tag[]>([]);
	let logs = $state<BenchmarkLogEntry[]>([]);
	let loading = $state(true);
	let reindexResult = $state<string>('');
	let reindexing = $state(false);
	let repDelta = $state<Record<string, number>>({});

	onMount(() => {
		const unsub = authReady.subscribe((ready) => {
			if (ready) {
				if (!$currentUser) goto('/login');
				else if (!$currentUser.isAdmin) goto('/questions');
				else loadAll();
			}
		});
		return unsub;
	});

	async function loadAll() {
		loading = true;
		try {
			const [uRes, tRes, lRes] = await Promise.all([
				adminListUsers(),
				listTags(),
				adminGetBenchmarkLog(20)
			]);
			users = uRes.users;
			tags = tRes.tags;
			logs = lRes.logs;
		} catch {
			// backend chưa chạy - trang vẫn hiện, chỉ rỗng dữ liệu
		} finally {
			loading = false;
		}
	}

	async function toggleBan(u: AdminUser) {
		const res = await adminBanUser(u.id, !u.isBanned);
		users = users.map((x) => (x.id === u.id ? res.user : x));
	}

	async function applyDelta(u: AdminUser) {
		const delta = repDelta[u.id];
		if (!delta) return;
		const res = await adminAdjustReputation(u.id, delta);
		users = users.map((x) => (x.id === u.id ? res.user : x));
		repDelta[u.id] = 0;
	}

	async function removeTag(t: Tag) {
		if (!confirm(`Xóa tag "${t.name}"? (không tự xóa tag khỏi câu hỏi đã gắn)`)) return;
		await deleteTag(t.id);
		tags = tags.filter((x) => x.id !== t.id);
	}

	async function editTagDescription(t: Tag) {
		const desc = prompt(`Mô tả mới cho tag "${t.name}":`, t.description);
		if (desc === null) return;
		const res = await updateTag(t.id, desc);
		tags = tags.map((x) => (x.id === t.id ? res.tag : x));
	}

	async function runReindex() {
		reindexing = true;
		reindexResult = '';
		try {
			const res = await adminTriggerReindex();
			reindexResult = JSON.stringify(res, null, 2);
			const lRes = await adminGetBenchmarkLog(20);
			logs = lRes.logs;
		} catch (err) {
			reindexResult = err instanceof ApiError ? `Lỗi: ${String(err.detail)}` : 'Reindex thất bại';
		} finally {
			reindexing = false;
		}
	}
</script>

<h1>Trang quản trị</h1>

{#if loading}
	<p>Đang tải...</p>
{:else}
	<section>
		<h2>Module tìm kiếm (TF-IDF / SBERT)</h2>
		<p class="hint">
			Bấm nút này sau mỗi lần seed/thêm nhiều câu hỏi để build lại toàn bộ chỉ mục.
		</p>
		<button class="primary" onclick={runReindex} disabled={reindexing}>
			{reindexing ? 'Đang reindex...' : 'Reindex toàn bộ'}
		</button>
		{#if reindexResult}
			<pre class="result-box">{reindexResult}</pre>
		{/if}

		<h3>Log thời gian phản hồi gần nhất</h3>
		{#if logs.length === 0}
			<p class="hint">Chưa có lượt search nào được ghi log.</p>
		{:else}
			<table>
				<thead>
					<tr><th>Phương pháp</th><th>Truy vấn</th><th>Thời gian (ms)</th><th>Số kết quả</th></tr>
				</thead>
				<tbody>
					{#each logs as l}
						<tr>
							<td>{l.method}</td>
							<td>{l.query}</td>
							<td>{l.elapsedMs}</td>
							<td>{l.resultCount}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	</section>

	<section>
		<h2>Quản lý user ({users.length})</h2>
		<table>
			<thead>
				<tr>
					<th>Username</th><th>Reputation</th><th>Trạng thái</th><th>Điều chỉnh rep</th><th></th>
				</tr>
			</thead>
			<tbody>
				{#each users as u}
					<tr>
						<td>{u.displayName} (@{u.username}){u.isAdmin ? ' 👑' : ''}</td>
						<td>{u.reputation}</td>
						<td>{u.isBanned ? '🚫 Đã khóa' : '✅ Bình thường'}</td>
						<td class="rep-cell">
							<input
								type="number"
								placeholder="+/- điểm"
								value={repDelta[u.id] ?? ''}
								oninput={(e) => (repDelta[u.id] = Number((e.target as HTMLInputElement).value))}
							/>
							<button onclick={() => applyDelta(u)}>Áp dụng</button>
						</td>
						<td>
							<button class:danger={!u.isBanned} onclick={() => toggleBan(u)}>
								{u.isBanned ? 'Mở khóa' : 'Khóa'}
							</button>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>

	<section>
		<h2>Quản lý tag ({tags.length})</h2>
		<table>
			<thead>
				<tr><th>Tag</th><th>Mô tả</th><th>Số câu hỏi</th><th></th></tr>
			</thead>
			<tbody>
				{#each tags as t}
					<tr>
						<td>{t.name}</td>
						<td>{t.description || '—'}</td>
						<td>{t.questionCount}</td>
						<td>
							<button onclick={() => editTagDescription(t)}>Sửa</button>
							<button class="danger" onclick={() => removeTag(t)}>Xóa</button>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
{/if}

<style>
	section {
		margin-bottom: 2.5rem;
	}
	h2 {
		font-size: 1.15rem;
		border-bottom: 1px solid #eaecef;
		padding-bottom: 0.4rem;
	}
	h3 {
		font-size: 0.95rem;
		margin-top: 1.2rem;
	}
	.hint {
		font-size: 0.85rem;
		color: #8a94a3;
	}
	.primary {
		padding: 0.5rem 1.1rem;
		border: none;
		border-radius: 6px;
		background: #0074cc;
		color: white;
		font-weight: 600;
		cursor: pointer;
	}
	.primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.result-box {
		background: #f6f8fa;
		border: 1px solid #eaecef;
		border-radius: 6px;
		padding: 0.8rem;
		font-size: 0.78rem;
		overflow-x: auto;
		margin-top: 0.8rem;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
		margin-top: 0.6rem;
	}
	th,
	td {
		text-align: left;
		padding: 0.5rem 0.6rem;
		border-bottom: 1px solid #f0f1f3;
	}
	.rep-cell {
		display: flex;
		gap: 0.4rem;
		align-items: center;
	}
	.rep-cell input {
		width: 80px;
		padding: 0.25rem 0.4rem;
		border: 1px solid #d0d5dd;
		border-radius: 4px;
	}
	button {
		padding: 0.3rem 0.7rem;
		border: 1px solid #d0d5dd;
		border-radius: 5px;
		background: white;
		cursor: pointer;
		font-size: 0.8rem;
	}
	button.danger {
		border-color: #f3c6d8;
		color: #d63384;
	}
	button:hover {
		background: #f2f4f7;
	}
</style>
