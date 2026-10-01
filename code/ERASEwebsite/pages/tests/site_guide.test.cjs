const test = require('node:test');
const assert = require('node:assert/strict');
const guide = require('../static/pages/javascript/site_guide.js');

const pages = [
    { path: '/about/', titleEn: 'About', titleEs: 'Acerca de', keywords: ['about', 'mission', 'misión'] },
    { path: '/calendar/', titleEn: 'Events Calendar', titleEs: 'Calendario de eventos', keywords: ['events', 'rsvp', 'eventos'] },
    { path: '/rsvp-listing/', titleEn: 'RSVP Listing', titleEs: 'Lista de confirmaciones', keywords: ['attendees'] }
];

test('matches navigation questions in English and Spanish', () => {
    assert.equal(guide.findPage('Where can I RSVP?', pages).path, '/calendar/');
    assert.equal(guide.findPage('Quiero ver eventos', pages).path, '/calendar/');
    assert.equal(guide.findPage('I need the mission', pages).path, '/about/');
    assert.equal(guide.findPage('A question with no known topic', pages), null);
});

test('recognizes the current page and its summary requests', () => {
    assert.equal(guide.isSummaryRequest('Summarize this page'), true);
    assert.equal(guide.isSummaryRequest('Resume esta página'), true);
    assert.equal(guide.currentPage('/about/', pages).path, '/about/');
    assert.equal(guide.currentPage('/rsvp-listing/3/', pages).path, '/rsvp-listing/');
});
