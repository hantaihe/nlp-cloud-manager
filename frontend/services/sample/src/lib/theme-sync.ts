export function initThemeSync() {
    if (typeof window === 'undefined') return () => { };

    const handleMessage = (event: MessageEvent) => {
        if (event.data.type === 'THEME_UPDATE') {
            const theme = event.data.theme;
            if (theme) {
                document.documentElement.setAttribute('data-theme', theme);
            }
        }
    };

    window.addEventListener('message', handleMessage);

    if (window.parent !== window) {
        window.parent.postMessage({ type: 'GET_THEME' }, '*');
    }

    return () => {
        window.removeEventListener('message', handleMessage);
    };
}
