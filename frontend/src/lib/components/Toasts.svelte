<script lang="ts">
	import { toasts, dismissToast } from '$lib/stores/toast';

	const icons = { success: '✅', error: '❌', info: 'ℹ️' };
</script>

{#if $toasts.length > 0}
	<div class="toast-stack" role="status" aria-live="polite">
		{#each $toasts as t (t.id)}
			<div class={`toast ${t.type}`}>
				<span class="icon">{icons[t.type]}</span>
				<span class="msg">{t.message}</span>
				<button class="close" onclick={() => dismissToast(t.id)} aria-label="Đóng">×</button>
			</div>
		{/each}
	</div>
{/if}

<style>
	.toast-stack {
		position: fixed;
		bottom: 1.2rem;
		right: 1.2rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		z-index: 9999;
		max-width: 360px;
	}
	.toast {
		display: flex;
		align-items: flex-start;
		gap: 0.55rem;
		padding: 0.7rem 0.9rem;
		border-radius: 6px;
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
		font-size: 0.86rem;
		line-height: 1.35;
		color: white;
		animation: slide-in 0.2s ease-out;
	}
	.toast.success {
		background: #1a7a3a;
	}
	.toast.error {
		background: #c22f2f;
	}
	.toast.info {
		background: #232629;
	}
	.toast .msg {
		flex: 1;
	}
	.toast .close {
		background: none;
		border: none;
		color: rgba(255, 255, 255, 0.75);
		font-size: 1.1rem;
		line-height: 1;
		cursor: pointer;
		padding: 0;
	}
	.toast .close:hover {
		color: white;
	}
	@keyframes slide-in {
		from {
			opacity: 0;
			transform: translateX(16px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}
</style>
