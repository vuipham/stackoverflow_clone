<script lang="ts">
	import { mergeTag, ApiError, type Tag } from '$lib/api/client';

	let { tags, onMerged }: {
		tags: Tag[];
		onMerged: (result: { removedId: string; updatedTag: Tag }) => void;
	} = $props();

	let sourceId = $state('');
	let targetId = $state('');
	let merging = $state(false);
	let msg = $state('');
	let isError = $state(false);

	async function doMerge() {
		if (!sourceId || !targetId) return;
		if (sourceId === targetId) {
			msg = 'Tag nguồn và tag đích không được trùng nhau.';
			isError = true;
			return;
		}
		const sourceName = tags.find((t) => t.id === sourceId)?.name;
		const targetName = tags.find((t) => t.id === targetId)?.name;
		if (!confirm(`Gộp tag "${sourceName}" vào "${targetName}"?\nThao tác này không thể hoàn tác.`)) return;

		merging = true;
		msg = '';
		isError = false;
		try {
			const res = await mergeTag(sourceId, targetId);
			msg = res.message + ` (${res.questionsMigrated} câu hỏi được cập nhật)`;
			onMerged({ removedId: sourceId, updatedTag: res.tag });
			sourceId = '';
			targetId = '';
		} catch (err) {
			msg = err instanceof ApiError ? String(err.detail) : 'Gộp tag thất bại';
			isError = true;
		} finally {
			merging = false;
		}
	}
</script>

<div class="merge-panel">
	<div class="merge-row">
		<label>
			Tag nguồn (sẽ bị xóa)
			<select bind:value={sourceId}>
				<option value="">-- Chọn tag --</option>
				{#each tags as t}
					<option value={t.id}>{t.name} ({t.questionCount})</option>
				{/each}
			</select>
		</label>
		<span class="arrow">→</span>
		<label>
			Tag đích (giữ lại)
			<select bind:value={targetId}>
				<option value="">-- Chọn tag --</option>
				{#each tags as t}
					<option value={t.id}>{t.name} ({t.questionCount})</option>
				{/each}
			</select>
		</label>
		<button onclick={doMerge} disabled={merging || !sourceId || !targetId}>
			{merging ? 'Đang gộp...' : 'Gộp tag'}
		</button>
	</div>
	{#if msg}
		<p class:error={isError} class:success={!isError}>{msg}</p>
	{/if}
</div>

<style>
	.merge-panel {
		padding: 1rem 0 0.5rem;
	}
	.merge-row {
		display: flex;
		gap: 0.8rem;
		align-items: flex-end;
		flex-wrap: wrap;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.82rem;
		color: #5b6673;
	}
	select {
		padding: 0.4rem 0.6rem;
		border: 1px solid #d0d5dd;
		border-radius: 5px;
		font-size: 0.85rem;
		min-width: 160px;
	}
	.arrow {
		font-size: 1.2rem;
		margin-bottom: 0.3rem;
		color: #5b6673;
	}
	button {
		padding: 0.45rem 1rem;
		border: none;
		border-radius: 5px;
		background: #5c6bc0;
		color: white;
		font-weight: 600;
		cursor: pointer;
		font-size: 0.85rem;
		margin-bottom: 0;
	}
	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.error {
		color: #d63384;
		font-size: 0.85rem;
		margin: 0.5rem 0 0;
	}
	.success {
		color: #1a7a3a;
		font-size: 0.85rem;
		margin: 0.5rem 0 0;
	}
</style>
