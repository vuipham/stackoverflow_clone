<script lang="ts">
	let { content = '' }: { content: string } = $props();

	function renderSimpleMarkdown(text: string) {
		if (!text) return '';
		
		// Escape HTML
		let html = text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;');

		// Code Blocks (```code```)
		html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
			return `<pre class="so-code-block"><code>${code.trim()}</code></pre>`;
		});

		// Inline Code (`code`)
		html = html.replace(/`([^`]+)`/g, '<code class="so-inline-code">$1</code>');

		// Bold (**text**)
		html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

		// Italic (*text*)
		html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

		// Headings (# Heading)
		html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
		html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
		html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

		// Line breaks & paragraphs
		const paragraphs = html.split(/\n\n+/);
		return paragraphs
			.map((p) => {
				if (p.startsWith('<pre') || p.startsWith('<h1') || p.startsWith('<h2') || p.startsWith('<h3')) {
					return p;
				}
				return `<p>${p.replace(/\n/g, '<br/>')}</p>`;
			})
			.join('');
	}
</script>

<div class="so-markdown-content">
	<!-- eslint-disable-next-line svelte/no-at-html-tags -->
	{@html renderSimpleMarkdown(content)}
</div>

<style>
	.so-markdown-content {
		font-size: 0.95rem;
		line-height: 1.6;
		color: #232629;
	}

	.so-markdown-content :global(p) {
		margin: 0 0 0.8rem;
	}

	.so-markdown-content :global(strong) {
		color: #0c0d0e;
	}

	.so-markdown-content :global(pre.so-code-block) {
		background: #f6f6f6;
		border: 1px solid #e3e6e8;
		border-radius: 5px;
		padding: 0.8rem 1rem;
		overflow-x: auto;
		font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace;
		font-size: 0.88rem;
		margin: 0.8rem 0;
		color: #2f3337;
	}

	.so-markdown-content :global(code.so-inline-code) {
		background: #e3e6e8;
		color: #2f3337;
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		font-family: ui-monospace, 'Cascadia Code', monospace;
		font-size: 0.85rem;
	}

	.so-markdown-content :global(h1),
	.so-markdown-content :global(h2),
	.so-markdown-content :global(h3) {
		color: #0c0d0e;
		margin: 1rem 0 0.5rem;
	}
</style>
