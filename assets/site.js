"use strict";
const search = document.querySelector("#faq-search");
if (search) {
  document.querySelector(".faq-tools").hidden = false;
  const items = [...document.querySelectorAll(".faq")];
  const filters = [...document.querySelectorAll(".filter")];
  let category = "all";
  const normalize = (value) => value.normalize("NFKC").toLocaleLowerCase("ja");
  function update() {
    const terms = normalize(search.value).trim().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const item of items) {
      const matches = (category === "all" || category === item.dataset.category) && terms.every((term) => normalize(item.textContent).includes(term));
      item.hidden = !matches;
      if (matches) count++;
    }
    document.querySelector("#faq-result").textContent = `${count}件の質問`;
    document.querySelector("#no-results").hidden = count !== 0;
  }
  search.addEventListener("input", update);
  filters.forEach((button) => button.addEventListener("click", () => {
    category = button.dataset.filter;
    filters.forEach((filter) => {
      filter.classList.toggle("active", filter === button);
      filter.setAttribute("aria-pressed", String(filter === button));
    });
    update();
  }));
  update();
}
const form = document.querySelector("#contact-form");
if (form) {
  form.hidden = false;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const fields = new FormData(form);
    const subject = `[${fields.get("app")}] ${fields.get("kind")}`;
    const body = `アプリ：${fields.get("app")}\n種類：${fields.get("kind")}\n端末：${fields.get("device") || "未記入"}\niOS / アプリバージョン：${fields.get("version") || "未記入"}\n\nお問い合わせ内容：\n${fields.get("message")}`;
    location.href = `mailto:${encodeURIComponent(form.dataset.email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    document.querySelector("#mail-status").textContent = "メールアプリで内容を確認し、送信してください。開かない場合は、上のメールアドレスへ直接ご連絡ください。";
  });
}
