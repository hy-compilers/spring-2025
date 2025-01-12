document.addEventListener("DOMContentLoaded", () => {
    for (const tokenNode of document.querySelectorAll('.language-python pre.highlight > code > span.n')) {
        if (['match', 'case'].includes(tokenNode.textContent)) {
            tokenNode.className = 'ow';
        }
    }
});
