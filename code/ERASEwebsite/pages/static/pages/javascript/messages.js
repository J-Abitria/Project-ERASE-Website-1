document.querySelectorAll('[data-site-toast]').forEach((toast) => {
    window.setTimeout(() => toast.remove(), 5000);
});
