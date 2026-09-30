(function () {
    'use strict';

    const ui = {
        en: {
            title: 'Site guide', subtitle: 'Find your way around Project ERASE', close: 'Close site guide',
            summary: 'Summarize this page', events: 'Find events', input: 'Ask where to find information',
            placeholder: 'Ask where to find information…', send: 'Send',
            note: "Answers come from this site's page guide. Questions stay in your browser.",
            welcome: 'Hi! Ask me where to find something, or ask for a summary of this page.',
            opening: 'Would you like to open {title}?', open: 'Open {title}',
            page: 'This page: {summary}', sections: 'Visible sections include {sections}.',
            unknown: "I couldn't match that to a page. Try asking about events, the map, students, or contact information.",
            noSummary: 'I can help you find information elsewhere on this site.'
        },
        es: {
            title: 'Guía del sitio', subtitle: 'Encuentre información en Project ERASE', close: 'Cerrar guía del sitio',
            summary: 'Resumir esta página', events: 'Buscar eventos', input: 'Pregunte dónde encontrar información',
            placeholder: 'Pregunte dónde encontrar información…', send: 'Enviar',
            note: 'Las respuestas provienen de la guía de páginas. Sus preguntas permanecen en su navegador.',
            welcome: '¡Hola! Pregúnteme dónde encontrar algo o pida un resumen de esta página.',
            opening: '¿Quiere abrir {title}?', open: 'Abrir {title}',
            page: 'Esta página: {summary}', sections: 'Las secciones visibles incluyen {sections}.',
            unknown: 'No encontré una página para esa pregunta. Pruebe con eventos, el mapa, estudiantes o contacto.',
            noSummary: 'Puedo ayudarle a encontrar información en otras páginas del sitio.'
        }
    };

    function normalize(value) {
        return value.toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();
    }

    function matchesPhrase(query, phrase) {
        return (` ${query} `).includes(` ${normalize(phrase)} `);
    }

    function findPage(question, pages) {
        const query = normalize(question);
        let best = null;
        let bestScore = 0;
        for (const page of pages) {
            const phrases = [page.titleEn, page.titleEs, ...page.keywords];
            let score = 0;
            for (const phrase of phrases) {
                if (matchesPhrase(query, phrase)) {
                    const words = normalize(phrase).split(' ').length;
                    score = Math.max(score, words * 3 + normalize(phrase).length / 100);
                }
            }
            if (score > bestScore) {
                best = page;
                bestScore = score;
            }
        }
        return best;
    }

    function isSummaryRequest(question) {
        const query = normalize(question);
        return /\b(this page|current page|here|esta pagina|pagina actual|aqui)\b/.test(query)
            || /\b(summarize|summary|resumir|resumen)\b/.test(query);
    }

    function currentPage(pathname, pages) {
        const path = pathname.replace(/\/?$/, '/');
        return pages.find(page => page.path === path)
            || pages.find(page => page.path === '/rsvp-listing/' && path.startsWith('/rsvp-listing/'))
            || null;
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { normalize, findPage, isSummaryRequest, currentPage };
    }
    if (typeof document === 'undefined') return;

    const root = document.getElementById('site-guide');
    const catalog = document.getElementById('site-guide-catalog');
    if (!root || !catalog) return;

    const language = document.documentElement.lang.toLowerCase().startsWith('es') ? 'es' : 'en';
    const words = ui[language];
    const pages = Array.from(catalog.content.querySelectorAll('a')).map(anchor => ({
        path: new URL(anchor.getAttribute('href'), window.location.origin).pathname,
        href: new URL(anchor.getAttribute('href'), window.location.origin).href,
        titleEn: anchor.dataset.titleEn,
        titleEs: anchor.dataset.titleEs,
        summaryEn: anchor.dataset.summaryEn,
        summaryEs: anchor.dataset.summaryEs,
        keywords: anchor.dataset.keywords.split('|')
    }));
    const panel = document.getElementById('site-guide-panel');
    const launcher = document.getElementById('site-guide-launcher');
    const close = document.getElementById('site-guide-close');
    const log = document.getElementById('site-guide-log');
    const form = document.getElementById('site-guide-form');
    const input = document.getElementById('site-guide-input');
    let greeted = false;

    function title(page) { return language === 'es' ? page.titleEs : page.titleEn; }
    function summary(page) { return language === 'es' ? page.summaryEs : page.summaryEn; }
    function format(pattern, values) {
        return pattern.replace(/\{(\w+)\}/g, (_, key) => values[key] || '');
    }
    function appendMessage(content, kind, destination) {
        const message = document.createElement('div');
        message.className = `site-guide-message site-guide-message-${kind}`;
        const text = document.createElement('p');
        text.textContent = content;
        message.appendChild(text);
        if (destination) {
            const action = document.createElement('a');
            action.href = destination.href;
            action.className = 'site-guide-action';
            action.textContent = format(words.open, { title: title(destination) });
            message.appendChild(action);
        }
        log.appendChild(message);
        while (log.children.length > 50) log.firstElementChild.remove();
        log.scrollTop = log.scrollHeight;
    }
    function setOpen(open) {
        panel.hidden = !open;
        launcher.setAttribute('aria-expanded', String(open));
        if (open) {
            if (!greeted) {
                appendMessage(words.welcome, 'assistant');
                greeted = true;
            }
            input.focus();
        } else {
            launcher.focus();
        }
    }
    function visibleSections() {
        return Array.from(document.querySelectorAll('main h1, main h2, .page-header h1'))
            .filter(element => element.getClientRects().length > 0)
            .map(element => element.textContent.replace(/\s+/g, ' ').trim())
            .filter(Boolean).slice(0, 3);
    }
    function answer(question) {
        const here = currentPage(window.location.pathname, pages);
        const page = findPage(question, pages);
        if (isSummaryRequest(question) && (!page || page === here || /\b(this page|current page|here|esta pagina|pagina actual|aqui)\b/.test(normalize(question)))) {
            if (!here) {
                appendMessage(words.noSummary, 'assistant');
                return;
            }
            let response = format(words.page, { summary: summary(here) });
            const sections = visibleSections();
            if (sections.length > 1) response += ` ${format(words.sections, { sections: sections.join(', ') })}`;
            appendMessage(response, 'assistant');
            return;
        }
        if (!page) {
            appendMessage(words.unknown, 'assistant');
            return;
        }
        appendMessage(`${summary(page)} ${format(words.opening, { title: title(page) })}`, 'assistant', page);
    }

    document.getElementById('site-guide-title').textContent = words.title;
    document.getElementById('site-guide-subtitle').textContent = words.subtitle;
    close.setAttribute('aria-label', words.close);
    panel.setAttribute('aria-label', words.title);
    document.getElementById('site-guide-summary').textContent = words.summary;
    document.getElementById('site-guide-events').textContent = words.events;
    document.getElementById('site-guide-input-label').textContent = words.input;
    input.placeholder = words.placeholder;
    document.getElementById('site-guide-send').textContent = words.send;
    document.getElementById('site-guide-note').textContent = words.note;
    launcher.textContent = words.title;

    launcher.addEventListener('click', () => setOpen(panel.hidden));
    close.addEventListener('click', () => setOpen(false));
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !panel.hidden) setOpen(false);
    });
    form.addEventListener('submit', event => {
        event.preventDefault();
        const question = input.value.trim();
        if (!question) return;
        appendMessage(question, 'user');
        answer(question);
        input.value = '';
        input.focus();
    });
    document.getElementById('site-guide-summary').addEventListener('click', () => {
        appendMessage(words.summary, 'user');
        answer(words.summary);
    });
    document.getElementById('site-guide-events').addEventListener('click', () => {
        appendMessage(words.events, 'user');
        answer(words.events);
    });
})();
