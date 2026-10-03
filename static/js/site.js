(() => {
  "use strict";
  document.querySelectorAll(".needs-validation").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });
  document.querySelectorAll("[data-confirm]").forEach((element) => {
    element.addEventListener("click", (event) => {
      if (!window.confirm(element.dataset.confirm)) event.preventDefault();
    });
  });
  const cardInput = document.querySelector("input[name='card_number']");
  if (cardInput) {
    cardInput.addEventListener("input", () => {
      const digits = cardInput.value.replace(/\D/g, "").slice(0, 16);
      cardInput.value = digits.replace(/(.{4})/g, "$1 ").trim();
    });
  }

  let catalogRequest = null;
  const replaceCatalog = async (targetUrl, { pushHistory = true, scrollY = window.scrollY } = {}) => {
    const currentCatalog = document.querySelector("#catalog");
    if (!currentCatalog) {
      window.location.assign(targetUrl);
      return;
    }

    if (catalogRequest) catalogRequest.abort();
    const request = new AbortController();
    catalogRequest = request;
    currentCatalog.classList.add("is-loading");

    try {
      const response = await fetch(targetUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        signal: request.signal,
      });
      if (!response.ok) throw new Error(`Catalog request failed: ${response.status}`);

      const nextDocument = new DOMParser().parseFromString(await response.text(), "text/html");
      const nextCatalog = nextDocument.querySelector("#catalog");
      if (!nextCatalog) throw new Error("Catalog section is missing in the response");

      const pillsScroll = currentCatalog.querySelector(".category-pills")?.scrollLeft || 0;
      if (pushHistory) {
        history.replaceState({ catalog: true, scrollY }, "", window.location.href);
        history.pushState({ catalog: true, scrollY }, "", targetUrl);
      }
      document.title = nextDocument.title;
      currentCatalog.replaceWith(nextCatalog);
      const nextPills = nextCatalog.querySelector(".category-pills");
      if (nextPills) nextPills.scrollLeft = pillsScroll;
      window.scrollTo(0, scrollY);
    } catch (error) {
      if (error.name !== "AbortError") window.location.assign(targetUrl);
    } finally {
      if (catalogRequest === request) catalogRequest = null;
    }
  };

  if (document.querySelector("#catalog")) {
    history.replaceState({ catalog: true, scrollY: window.scrollY }, "", window.location.href);
  }

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-catalog-navigation]");
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    replaceCatalog(link.href);
  });

  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form[data-catalog-form]");
    if (!form || !form.checkValidity()) return;
    event.preventDefault();
    const targetUrl = new URL(form.action, window.location.href);
    targetUrl.search = new URLSearchParams(new FormData(form)).toString();
    targetUrl.hash = "catalog";
    replaceCatalog(targetUrl.toString());
  });

  window.addEventListener("popstate", (event) => {
    if (event.state?.catalog && document.querySelector("#catalog")) {
      replaceCatalog(window.location.href, { pushHistory: false, scrollY: event.state.scrollY || 0 });
    }
  });
})();
