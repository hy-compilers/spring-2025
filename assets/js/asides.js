(() => {
    document.addEventListener("DOMContentLoaded", () => {
        const asideRefs = document.querySelectorAll('span[data-aside]');
        for (const asideRef of asideRefs) {
            const handleClick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                const asideId = e.target.getAttribute('data-aside');
                if (asideId) {
                    openAside(asideId);
                }
            };
            asideRef.addEventListener('click', handleClick);
            asideRef.addEventListener('auxclick', handleClick);
            asideRef.title = "Click to expand";
        }
    });

    window.addEventListener("load", async () => {
        if (window.location.hash) {
            await wait(1);  // Let page layout complete. Not sure why necessary.
            const asideId = window.location.hash.substring(1);
            const aside = openAside(asideId, 'center');
            if (aside) {
                flashAnimation(aside);
            }
        }
    });

    function openAside(asideId, scrollBlock = 'nearest') {
        const aside = document.querySelector('aside#' + asideId);
        if (aside) {
            const scrollTop = document.body.parentElement.scrollTop;
            const visible = aside.classList.toggle('visible');
            // Work around weird jumping on Firefox that happens the first time we open an aside.
            // The site theme defines scrolling behaviour on the HTML element so that's what
            // we need to modify.
            document.body.parentElement.scrollTo({ top: scrollTop, behavior: 'instant' });
            if (visible) {
                aside.scrollIntoView({ behavior: 'smooth', block: scrollBlock });
            }
        }
        return aside;
    }

    async function flashAnimation(element) {
        const isInView = element.getBoundingClientRect().top < window.innerHeight;
        for (let i = 0; i < 10; i++) {
            if (isInView) {
                break;
            }
            await wait(100);
        }

        const millis = 120;
        for (let i = 0; i < 4; i++) {
            element.style.transition = `filter ${millis}ms ease-out`;
            element.style.filter = 'brightness(1.5)';
            await wait(millis);
            element.style.transition = `filter ${millis}ms ease-in`;
            element.style.filter = 'brightness(1)';
            await wait(millis);
        }
    }

    async function wait(millis) {
        await new Promise(resolve => setTimeout(resolve, millis));
    }

})();
