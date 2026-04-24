import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
	base: mode === 'production' ? '/services/azure/' : '/',
	plugins: [svelte()],
	resolve: {
		alias: {
			'@shared': path.resolve(__dirname, '../../shared')
		}
	},
	server: {
		port: 5176,
		host: true,
		cors: true
	}
}))
