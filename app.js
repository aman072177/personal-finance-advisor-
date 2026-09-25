const btn = document.getElementById("adviceBtn");
if (btn) {
  btn.addEventListener("click", async () => {
    const box = document.getElementById("advice");
    btn.disabled = true;
    btn.textContent = "Analyzing...";
    box.textContent = "Please wait...";
    try {
      const response = await fetch("/api/advice");
      const data = await response.json();
      box.textContent = data.advice + (data.ai ? "\n\n✓ Generated with Gemini AI" : "\n\nℹ Using local fallback advice — add GEMINI_API_KEY for Gemini AI.");
    } catch (error) {
      box.textContent = "Could not generate advice. Please try again.";
    } finally {
      btn.disabled = false;
      btn.textContent = "Get AI Advice";
    }
  });
}
