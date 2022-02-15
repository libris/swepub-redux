/* eslint no-use-before-define: off */
function handleMouseDownOnce() {
  document.body.classList.remove('user-is-tabbing');
  window.removeEventListener('mousedown', handleMouseDownOnce);
  window.addEventListener('keydown', handleFirstTab);
}
export function enableTabbing() {
  document.body.classList.add('user-is-tabbing');
  window.removeEventListener('keydown', handleFirstTab);
  window.addEventListener('mousedown', handleMouseDownOnce);
}
export function handleFirstTab(e) {
  if (e.keyCode === 9) {
    enableTabbing();
  }
}
