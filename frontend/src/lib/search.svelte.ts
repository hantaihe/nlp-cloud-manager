function createSearchStore() {
    let query = $state('');

    return {
        get query() { return query; },
        set query(val: string) { query = val; },
        clear() { query = ''; }
    };
}

export const searchStore = createSearchStore();
