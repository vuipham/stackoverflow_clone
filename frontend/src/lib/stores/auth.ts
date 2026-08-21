import { writable } from 'svelte/store';
import type { PublicUser } from '$lib/api/client';
import { fetchMe } from '$lib/api/client';

// Ngưỡng đặc quyền — khớp với backend (app/core/privileges.py) để UI có thể
// disable/hiện tooltip đúng ngay trên client, backend vẫn là nơi enforce thật.
export const PRIVILEGE = {
	ASK_ANSWER: 1,
	UPVOTE: 15,
	COMMENT_ON_OTHERS: 50,
	DOWNVOTE: 125,
	EDIT_OTHERS_POST: 500,
	DELETE_OTHERS_QUESTION: 2000
};

export const currentUser = writable<PublicUser | null>(null);
export const authReady = writable(false);

export function setSession(token: string, user: PublicUser) {
	localStorage.setItem('token', token);
	currentUser.set(user);
}

export function clearSession() {
	localStorage.removeItem('token');
	currentUser.set(null);
}

/** Gọi lúc app khởi động để khôi phục phiên đăng nhập từ token đã lưu. */
export async function restoreSession() {
	const token = localStorage.getItem('token');
	if (!token) {
		authReady.set(true);
		return;
	}
	try {
		const user = await fetchMe();
		currentUser.set(user);
	} catch {
		localStorage.removeItem('token');
		currentUser.set(null);
	} finally {
		authReady.set(true);
	}
}
