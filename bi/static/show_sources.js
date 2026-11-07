
setTimeout(() => {
  const links = document.querySelectorAll(".nav-source-link");
  const menu = document.querySelector("[data-testid='stSidebarContent']");
  const footer = document.querySelector(".st-key-sidebar_footer");
  if (!links.length || !menu || !footer) { return; }
  const hidden = links[links.length - 1].getBoundingClientRect().bottom - footer.getBoundingClientRect().top + 12;
  if (hidden > 0) { menu.scrollBy({top: hidden, behavior: "smooth"}); }
}, 200);
