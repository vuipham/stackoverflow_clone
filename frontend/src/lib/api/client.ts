const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
	status: number;
	detail: unknown;
	constructor(status: number, detail: unknown) {
		super(typeof detail === 'string' ? detail : JSON.stringify(detail));
		this.status = status;
		this.detail = detail;
	}
}

function getToken(): string | null {
	if (typeof localStorage === 'undefined') return null;
	return localStorage.getItem('token');
}

async function request<T>(
	path: string,
	options: { method?: string; body?: unknown; auth?: boolean } = {}
): Promise<T> {
	const { method = 'GET', body, auth = false } = options;
	const headers: Record<string, string> = { 'Content-Type': 'application/json' };

	if (auth) {
		const token = getToken();
		if (token) headers['Authorization'] = `Bearer ${token}`;
	}

	const res = await fetch(`${API_BASE_URL}${path}`, {
		method,
		headers,
		body: body ? JSON.stringify(body) : undefined
	});

	const data = await res.json().catch(() => null);

	if (!res.ok) {
		throw new ApiError(res.status, data?.detail ?? data ?? 'Lỗi không xác định');
	}
	return data as T;
}

// ---- Auth ----
export interface PublicUser {
	id: string;
	username: string;
	email: string;
	displayName: string;
	reputation: number;
	isAdmin: boolean;
}

export function register(payload: {
	username: string;
	email: string;
	password: string;
	displayName?: string;
}) {
	return request<{ token: string; user: PublicUser }>('/api/auth/register', {
		method: 'POST',
		body: payload
	});
}

export function login(payload: { username: string; password: string }) {
	return request<{ token: string; user: PublicUser }>('/api/auth/login', {
		method: 'POST',
		body: payload
	});
}

export function fetchMe() {
	return request<PublicUser>('/api/auth/me', { auth: true });
}

// ---- Questions ----
export interface Question {
	id: string;
	title: string;
	body: string;
	tags: string[];
	authorId: string;
	viewCount: number;
	voteScore: number;
	answerCount: number;
	acceptedAnswerId: string | null;
	isIndexed: boolean;
	createdAt: string;
	updatedAt: string;
}

export function listQuestions(tag?: string) {
	const qs = tag ? `?tag=${encodeURIComponent(tag)}` : '';
	return request<{ questions: Question[] }>(`/api/questions${qs}`);
}

export function getQuestion(id: string) {
	return request<{ question: Question }>(`/api/questions/${id}`);
}

export function createQuestion(payload: { title: string; body: string; tags: string[] }) {
	return request<{ question: Question }>('/api/questions', {
		method: 'POST',
		body: payload,
		auth: true
	});
}

// ---- Votes ----
export function castVote(payload: {
	targetType: 'question' | 'answer';
	targetId: string;
	value: 1 | -1;
}) {
	return request<{ message: string; newVoteScore: number }>('/api/votes', {
		method: 'POST',
		body: payload,
		auth: true
	});
}

// ---- Answers ----
export interface Answer {
	id: string;
	questionId: string;
	authorId: string;
	body: string;
	voteScore: number;
	isAccepted: boolean;
	createdAt: string;
}

export function listAnswers(questionId: string) {
	return request<{ answers: Answer[] }>(`/api/questions/${questionId}/answers`);
}

export function createAnswer(questionId: string, body: string) {
	return request<{ answer: Answer }>(`/api/questions/${questionId}/answers`, {
		method: 'POST',
		body: { body },
		auth: true
	});
}

export function acceptAnswer(answerId: string) {
	return request<{ answer: Answer }>(`/api/answers/${answerId}/accept`, {
		method: 'POST',
		auth: true
	});
}

export function deleteAnswer(answerId: string) {
	return request<{ message: string }>(`/api/answers/${answerId}`, {
		method: 'DELETE',
		auth: true
	});
}

// ---- Comments ----
export interface Comment {
	id: string;
	targetType: 'question' | 'answer';
	targetId: string;
	authorId: string;
	content: string;
	createdAt: string;
}

export function listComments(targetType: 'question' | 'answer', targetId: string) {
	return request<{ comments: Comment[] }>(
		`/api/comments?targetType=${targetType}&targetId=${targetId}`
	);
}

export function createComment(targetType: 'question' | 'answer', targetId: string, content: string) {
	return request<{ comment: Comment }>('/api/comments', {
		method: 'POST',
		body: { targetType, targetId, content },
		auth: true
	});
}

export function deleteComment(commentId: string) {
	return request<{ message: string }>(`/api/comments/${commentId}`, {
		method: 'DELETE',
		auth: true
	});
}

// ---- Tags ----
export interface Tag {
	id: string;
	name: string;
	description: string;
	questionCount: number;
}

export function listTags() {
	return request<{ tags: Tag[] }>('/api/tags');
}

export function updateTag(tagId: string, description: string) {
	return request<{ tag: Tag }>(`/api/tags/${tagId}`, {
		method: 'PUT',
		body: { description },
		auth: true
	});
}

export function deleteTag(tagId: string) {
	return request<{ message: string }>(`/api/tags/${tagId}`, {
		method: 'DELETE',
		auth: true
	});
}

// ---- Search (Chức năng B) ----
export interface SearchResultItem {
	questionId: string;
	title: string;
	tags: string[];
	voteScore: number;
	answerCount: number;
	similarityScore: number;
	similarityPercent: number;
}

export interface SearchResponse {
	method: 'tfidf' | 'sbert';
	query: string;
	elapsedMs: number;
	results: SearchResultItem[];
}

export function searchTfidf(q: string, topK = 10) {
	return request<SearchResponse>(
		`/api/search/tfidf?q=${encodeURIComponent(q)}&top_k=${topK}`
	);
}

export function searchSbert(q: string, topK = 10) {
	return request<SearchResponse>(
		`/api/search/sbert?q=${encodeURIComponent(q)}&top_k=${topK}`
	);
}

// ---- Admin ----
export interface AdminUser {
	id: string;
	username: string;
	email: string;
	displayName: string;
	reputation: number;
	isAdmin: boolean;
	isBanned: boolean;
}

export function adminListUsers(q?: string) {
	const qs = q ? `?q=${encodeURIComponent(q)}` : '';
	return request<{ users: AdminUser[] }>(`/api/admin/users${qs}`, { auth: true });
}

export function adminBanUser(userId: string, isBanned: boolean) {
	return request<{ user: AdminUser }>(`/api/admin/users/${userId}/ban`, {
		method: 'PATCH',
		body: { isBanned },
		auth: true
	});
}

export function adminAdjustReputation(userId: string, delta: number, reason = 'admin_adjust') {
	return request<{ user: AdminUser }>(`/api/admin/users/${userId}/reputation`, {
		method: 'PATCH',
		body: { delta, reason },
		auth: true
	});
}

export function adminTriggerReindex() {
	return request<{ tfidf: unknown; sbert: unknown }>('/api/admin/search/reindex', {
		method: 'POST',
		auth: true
	});
}

export interface BenchmarkLogEntry {
	method: string;
	query: string;
	elapsedMs: number;
	resultCount: number;
}

export function adminGetBenchmarkLog(limit = 50) {
	return request<{ logs: BenchmarkLogEntry[] }>(
		`/api/admin/search/benchmark-log?limit=${limit}`,
		{ auth: true }
	);
}
