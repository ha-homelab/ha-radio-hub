"use strict";
const search = document.querySelector("#guide-search");
if (search) {
  const cards = [...document.querySelectorAll("[data-search]")];
  const count = document.querySelector("#result-count");
  const empty = document.querySelector("#empty");
  const filter = () => {
    const words = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    cards.forEach(card => {
      card.hidden = !words.every(word => card.dataset.search.includes(word));
      if (!card.hidden) shown++;
    });
    count.textContent = `${shown} of ${cards.length} guides`;
    empty.hidden = shown !== 0;
  };
  search.addEventListener("input", filter);
  document.querySelector("#clear-search").addEventListener("click", () => {
    search.value = ""; filter(); search.focus();
  });
  filter();
}
document.querySelectorAll("pre > code").forEach(code => {
  const row = document.createElement("div"); row.className = "copy-row";
  const status = document.createElement("span"); status.className = "copy-status";
  status.setAttribute("role", "status");
  const button = document.createElement("button"); button.type = "button";
  button.textContent = "Copy code";
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(code.textContent);
      status.textContent = "Copied";
    } catch {
      const range = document.createRange(); range.selectNodeContents(code);
      const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
      status.textContent = "Text selected — press Ctrl+C or ⌘C";
    }
  });
  row.append(status, button); code.parentElement.before(row);
});
document.querySelectorAll("[data-print]").forEach(button => button.addEventListener("click", () => window.print()));
