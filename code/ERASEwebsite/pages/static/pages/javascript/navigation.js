(() => {
    const navigation = document.getElementById('main-navigation');
    const toggle = navigation.querySelector('.nav-toggle');
    const dropdowns = [...navigation.querySelectorAll('details')];
    const mobile = window.matchMedia('(max-width: 900px)');

    // Keep navigation available when JavaScript is disabled or fails to load.
    navigation.classList.add('nav-enhanced');
    toggle.hidden = false;

    function closeMenu() {
        toggle.setAttribute('aria-expanded', 'false');
        navigation.classList.remove('menu-open');
        dropdowns.forEach(dropdown => { dropdown.open = false; });
    }

    toggle.addEventListener('click', () => {
        const open = toggle.getAttribute('aria-expanded') !== 'true';
        if (!open) closeMenu();
        else {
            toggle.setAttribute('aria-expanded', 'true');
            navigation.classList.add('menu-open');
        }
    });

    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('toggle', () => {
            if (dropdown.open) {
                dropdowns.forEach(other => { if (other !== dropdown) other.open = false; });
            }
        });
    });

    document.addEventListener('click', event => {
        if (!navigation.contains(event.target)) closeMenu();
    });
    navigation.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        const openDropdown = dropdowns.find(dropdown => dropdown.open);
        if (openDropdown) {
            openDropdown.open = false;
            openDropdown.querySelector('summary').focus();
        } else if (mobile.matches && navigation.classList.contains('menu-open')) {
            closeMenu();
            toggle.focus();
        }
    });
    mobile.addEventListener('change', () => {
        const focusWillHide = mobile.matches && navigation.querySelector('.nav-menu').contains(document.activeElement);
        closeMenu();
        if (focusWillHide) toggle.focus();
    });
})();
