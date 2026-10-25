/* Reject oversized packages before a request can hit the hosting body limit. */
(() => {
  'use strict';
  const input = document.querySelector('input[type="file"][data-package-max-bytes]');
  if (!input) return;
  const validate = () => {
    const file = input.files[0];
    const cap = Number(input.dataset.packageMaxBytes);
    const invalid = file && /\.zip$/i.test(file.name) && file.size > cap;
    input.setCustomValidity(invalid
      ? `ZIP больше ${cap / 1048576} МиБ. Используйте отдельный JSON и порционную загрузку фотографий в галерее.`
      : '');
    return !invalid;
  };
  input.addEventListener('change', () => { validate(); input.reportValidity(); });
  input.form.addEventListener('submit', event => {
    if (!validate()) { event.preventDefault(); input.reportValidity(); }
  });
})();
