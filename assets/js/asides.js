document.addEventListener("DOMContentLoaded", () => {
    const asideRefs = document.querySelectorAll('span[data-aside]');
    for (const asideRef of asideRefs) {
        const handleClick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            const asideId = e.target.getAttribute('data-aside');
            if (asideId) {
                const aside = document.querySelector('aside#' + asideId);
                if (aside) {
                    const scrollTop = document.body.parentElement.scrollTop;
                    const visible = aside.classList.toggle('visible');
                    // Work around weird jumping on Firefox that happens the first time we open an aside.
                    // The site theme defines scrolling behaviour on the HTML element so that's what
                    // we need to modify.
                    document.body.parentElement.scrollTo({ top: scrollTop, behavior: 'instant' });
                    if (visible) {
                        aside.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                }
            }
        };
        asideRef.addEventListener('click', handleClick);
        asideRef.addEventListener('auxclick', handleClick);
        asideRef.title = "Click to expand";
    }
});
