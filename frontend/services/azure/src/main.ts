import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'
import { initThemeSync } from '@shared/theme/theme-sync'

initThemeSync();

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app

