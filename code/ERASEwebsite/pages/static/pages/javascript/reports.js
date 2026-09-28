(function () {
    const buttons = document.querySelectorAll('.tab-btn');
    const panes   = document.querySelectorAll('.tab-content');

    function activateTab(tabId) {
        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
        panes.forEach(pane => pane.classList.toggle('active', pane.id === 'tab-' + tabId));
    }

    buttons.forEach(btn => {
        btn.addEventListener('click', () => activateTab(btn.dataset.tab));
    });

    // Initial tab is rendered into HTML; static JavaScript is not Django-templated.
    const tabNavigation = document.querySelector('.report-tabs');
    const serverTab = tabNavigation ? tabNavigation.dataset.initialTab : 'fundraising';
    const urlTab    = new URLSearchParams(window.location.search).get('tab');
    const validTabs = new Set(['fundraising', 'workshops', 'students', 'social']);
    const initialTab = validTabs.has(urlTab) ? urlTab : (validTabs.has(serverTab) ? serverTab : 'fundraising');
    activateTab(initialTab);
})();