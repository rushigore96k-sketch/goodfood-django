document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[type="number"]').forEach((input) => {
    input.addEventListener('change', () => {
      const min = Number(input.min || 0);
      const max = Number(input.max || 99);
      const value = Number(input.value || min);
      input.value = Math.min(max, Math.max(min, value));
    });
  });
});
