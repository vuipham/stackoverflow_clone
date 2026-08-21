import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			// Dùng adapter-static ở chế độ SPA (fallback index.html) vì toàn bộ dữ liệu
			// được fetch phía client (onMount) từ backend FastAPI, không dùng SSR load function.
			adapter: adapter({
				fallback: 'index.html'
			})
		})
	]
});
