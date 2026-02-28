import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'ocean' | 'forest';

function createThemeStore() {
    let currentTheme = $state<Theme>(
        (browser && (localStorage.getItem('theme') as Theme)) || 'dark'
    );

    function setTheme(theme: Theme) {
        currentTheme = theme;
        if (browser) {
            localStorage.setItem('theme', theme);
        }
    }

    return {
        get current() { return currentTheme; },
        setTheme
    };
}

export const themeStore = createThemeStore();

if (browser) {
    $effect.root(() => {
        $effect(() => {
            const theme = themeStore.current;
            document.documentElement.setAttribute('data-theme', theme);
        });
    });
}
