document.addEventListener("DOMContentLoaded", () => {
    const navs = document.getElementsByTagName("nav");
    const ul = navs[0].appendChild(document.createElement("ul"));
    const li = ul.appendChild(document.createElement("li"));
    const a = li.appendChild(document.createElement("a"));
    a.href = "https://test-gadget.compilers.how/";

    // https://gist.github.com/miguelmota/322c89234d60de578f37d3c6d30f7e41
    const externalLinkIcon = document.createElement("span");
    externalLinkIcon.style.transform = "rotate(90deg)";
    externalLinkIcon.style.display = "inline-block";
    externalLinkIcon.style.position = "relative";
    externalLinkIcon.style.left = "0.6em";
    externalLinkIcon.style.top = "0.14em";
    externalLinkIcon.textContent = "⎋";

    a.textContent = "Test Gadget";
    a.appendChild(externalLinkIcon);
});
