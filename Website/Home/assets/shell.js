(function () {
  var btn = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!btn || !nav) return;

  function setOpen(open) {
    nav.classList.toggle("open", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.textContent = open ? "Close" : "Menu";
  }

  btn.addEventListener("click", function () {
    setOpen(btn.getAttribute("aria-expanded") !== "true");
  });

  nav.addEventListener("click", function (event) {
    var link = event.target && event.target.closest ? event.target.closest("a") : null;
    if (link) setOpen(false);
  });
})();
