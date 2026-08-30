import assert from "node:assert/strict";
import { test } from "node:test";

import { loadDirectionsScript } from "./harness.mjs";

test("directions does nothing when direction steps are missing", () => {
  const harness = loadDirectionsScript();

  assert.equal(harness.directionsContainer.children.length, 0);
  assert.equal(harness.directionsContainer.innerHTML, "");
  assert.equal(harness.document.getElementById("next-step-btn"), null);
});

test("directions does nothing for an empty step list", () => {
  const harness = loadDirectionsScript({ directionSteps: [] });

  assert.equal(harness.directionsContainer.children.length, 0);
  assert.equal(harness.directionsContainer.innerHTML, "");
});

test("directions renders the first step and its ordinary instruction text", () => {
  const instruction = "Leave the lobby and turn right toward the elevators.";
  const harness = loadDirectionsScript({ directionSteps: [instruction] });
  const card = harness.directionsContainer.children[0];
  const nextButton = harness.getElementById("next-step-btn");

  assert.equal(harness.directionsContainer.children.length, 1);
  assert.equal(card.className, "direction-card active");
  assert.equal(card.children[0].textContent, "Step 1");
  assert.equal(card.children[1].textContent, instruction);
  assert.equal(nextButton.textContent, "Next");
  assert.match(harness.directionsContainer.innerHTML, /Step 1/);
  assert.match(harness.directionsContainer.innerHTML, /Leave the lobby/);
});

test("directions advances through steps in order and then shows arrived", () => {
  const harness = loadDirectionsScript({
    directionSteps: [
      "Exit the room and turn left.",
      "Continue straight for 20 feet.",
      "Turn right at the hallway.",
    ],
  });

  const firstButton = harness.getElementById("next-step-btn");
  firstButton.click();
  assert.equal(
    harness.directionsContainer.children[0].children[0].textContent,
    "Step 2",
  );
  assert.equal(
    harness.directionsContainer.children[0].children[1].textContent,
    "Continue straight for 20 feet.",
  );

  const secondButton = harness.getElementById("next-step-btn");
  secondButton.click();
  assert.equal(
    harness.directionsContainer.children[0].children[0].textContent,
    "Step 3",
  );
  assert.equal(
    harness.directionsContainer.children[0].children[1].textContent,
    "Turn right at the hallway.",
  );

  const finalButton = harness.getElementById("next-step-btn");
  finalButton.click();
  const arrivedCard = harness.directionsContainer.children[0];

  assert.equal(arrivedCard.className, "direction-card arrived");
  assert.equal(
    harness.directionsContainer.querySelector("h3").textContent,
    "You have arrived!",
  );
  assert.equal(harness.getElementById("next-step-btn"), null);
});
