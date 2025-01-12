
function menu(open) {
  if (open === undefined) open = !document.body.classList.contains("opened");
  if (open) updateScroll();
  document.body.classList.toggle("opened", open);
  document.getElementById("menu").setAttribute("aria-expanded", open);
}

let themeChannel;
if (window.BroadcastChannel) {
  themeChannel = new BroadcastChannel("theme");
}

function applyTheme(newTheme) {
  activeTheme = newTheme;
  document.documentElement.classList.toggle(
    "dark-theme",
    activeTheme === "dark"
  );
}

function toggleTheme(newTheme) {
  if (newTheme === undefined) newTheme = activeTheme == "dark" ? "light" : "dark";
  applyTheme(newTheme);
  localStorage.setItem("theme", newTheme);
  if (themeChannel) {
    themeChannel.postMessage(newTheme);
  }
}

if (themeChannel) {
  themeChannel.onmessage = (event) => applyTheme(localStorage.getItem("theme"));
}

let articles = {};
let sublists = {};
let sections = [];
let updateHash;

function loadSections() {
  const articleNodes = document.getElementsByTagName("article");
  for (const article of articleNodes) {
    articles[article.dataset.url] = article;
  }
  updateHash = Object.keys(articles).length === 1;

  const pageNavs = document.querySelectorAll("nav li[data-url]");
  for (const pageNav of pageNavs) {
    const article_key = pageNav.dataset.url;
    if (!(article_key in articles)) continue;
    const article = articles[article_key];

    const link = pageNav.getElementsByTagName("a")[0];
    sections.push({
      title: link.innerHTML,
      link: link,
      anchor: article,
      articleKey: article_key,
      first: sections.length === 0,
    });

    const sublist = pageNav.getElementsByTagName("ul")[0];
    if (sublist) {
      sublists[pageNav.dataset.url] = sublist;
      for (const child of sublist.children) {
        const link = child.children[0];
        const anchor = article.querySelector("#" + link.dataset.anchor);

        if (!anchor) {
          link.classList.add("unbound");
        }

        sections.push({
          title: link.innerHTML,
          link: link,
          anchor: anchor,
          hash: link.dataset.anchor,
          articleKey: article_key,
          first: false,
        });
      }
    }
  }

  for (const section of sections) {
    section.link.addEventListener("click", (e) => clickSection(e, section));
  }
}

function clickSection(e, section) {
  e.preventDefault();
  inhibitUpdateScroll();
  if (section.first) {
    if (updateHash) window.location = "#";
    window.scrollTo(0, 0);
    chooseSection(null, "none");
  } else {
    if (updateHash) window.location = "#" + section.hash;
    section.anchor.scrollIntoView();
    chooseSection(section, "none");
  }
  menu(false);
}

function chooseSection(currentSection, scroll="normal") {
  for (const section of sections) {
    section.link.classList.remove("current");
  }

  let effSection = null;

  if (currentSection) {
    effSection = currentSection;
    document.getElementById("awning").classList.add("show");
  } else {
    if (sections.length) {
      effSection = sections[0];
    }
    document.getElementById("awning").classList.remove("show");
  }

  if (hideOtherSectionMenus) {
    const articleKey = effSection ? effSection.articleKey : null;
    for (const key of Object.keys(sublists)) {
      sublists[key].classList.toggle("hide-menu", key != articleKey);
    }
  }

  if (effSection) {
    const link = effSection.link;

    link.classList.add("current");

    if (scroll !== "none") {
      if (scroll === "initial") {
        const nav = document.getElementsByTagName("nav")[0];
        nav.scrollTop = link.offsetTop - nav.offsetTop - nav.clientHeight * 0.3;
      }
      // behavior: smooth doesn't work on Chrome while the user is scrolling the window
      link.scrollIntoView({ behavior: "auto", block: "nearest" });
    }
  }
}

let lastSectionIdx = null;

function updateScroll(initial=false) {
  const scroll = document.documentElement.scrollTop;
  // TODO: scroll-margin-top also depends on CSS media queries
  let currentSectionIdx = sections.length - 1;
  for (; currentSectionIdx >= 0; currentSectionIdx--) {
    const section = sections[currentSectionIdx];
    if (section.anchor && scroll >= section.anchor.offsetTop - (section.first ? 0 : 92)) break;
  }

  if (currentSectionIdx != lastSectionIdx) {
    lastSectionIdx = currentSectionIdx;
    const currentSection = sections[currentSectionIdx];
    chooseSection(currentSection, initial ? "initial" : "normal");
  }
}

let inhibited = false;
let inhibitTimeout;
function inhibitUpdateScroll() {
  inhibited = true;
  clearTimeout(inhibitTimeout);
  inhibitTimeout = setTimeout(() => {
    inhibited = false;
    lastSectionIdx = null;
  }, 150);
}

addEventListener("DOMContentLoaded", () => {
  loadSections();
  updateScroll(true);
  setTimeout(() => document.body.classList.remove("loading"));
  document.getElementById("menu").addEventListener("click", () => menu());
  document.getElementById("menu-background").addEventListener("click", () => menu(false));

  document.getElementById("theme").addEventListener("click", () => toggleTheme());

  addEventListener("scroll", () => {
    if (inhibited) {
      inhibitUpdateScroll();
    } else {
      updateScroll();
    }
  });
});

