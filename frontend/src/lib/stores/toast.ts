import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
	id: number;
	type: ToastType;
	message: string;
}

export const toasts = writable<Toast[]>([]);

let seq = 0;

/** Hiện toast toàn cục - tự ẩn sau `duration` ms (mặc định 3500ms). */
export function showToast(message: string, type: ToastType = 'info', duration = 3500) {
	const id = ++seq;
	toasts.update((list) => [...list, { id, type, message }]);
	setTimeout(() => dismissToast(id), duration);
	return id;
}

export function dismissToast(id: number) {
	toasts.update((list) => list.filter((t) => t.id !== id));
}
