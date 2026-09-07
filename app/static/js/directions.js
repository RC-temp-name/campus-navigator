document.addEventListener("DOMContentLoaded", () => {
  if (typeof directionSteps === "undefined" || !directionSteps.length) return;

  const container = document.getElementById("directions-card-container");
  if (!container) return;

  let currentIndex = 0;

  function renderSteps(index) {
    container.replaceChildren();

    const card = document.createElement("div");
    card.className =
      index >= directionSteps.length
        ? "direction-card arrived"
        : "direction-card active";

    const heading = document.createElement("h3");
    heading.textContent =
      index >= directionSteps.length
        ? "You have arrived!"
        : `Step ${index + 1}`;
    card.appendChild(heading);

    if (index < directionSteps.length) {
      const paragraph = document.createElement("p");
      paragraph.textContent = directionSteps[index];
      card.appendChild(paragraph);

      const nextButton = document.createElement("button");
      nextButton.id = "next-step-btn";
      nextButton.textContent = "Next";
      nextButton.addEventListener("click", () => {
        currentIndex++;
        renderSteps(currentIndex);
      });
      card.appendChild(nextButton);
    }

    container.appendChild(card);
  }

  renderSteps(currentIndex);
});
