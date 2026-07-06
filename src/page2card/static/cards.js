(() => {
  const box = document.querySelector('.lightbox');
  const buttons = [...document.querySelectorAll('.card-preview')];
  if (!box || buttons.length === 0) return;
  const img = box.querySelector('img');
  let index = 0;
  const show = (i) => { index = (i + buttons.length) % buttons.length; img.src = buttons[index].querySelector('img').src; box.hidden = false; };
  const close = () => { box.hidden = true; };
  buttons.forEach((button, i) => button.addEventListener('click', () => show(i)));
  box.querySelector('.lightbox-close').addEventListener('click', close);
  box.querySelector('.lightbox-prev').addEventListener('click', () => show(index - 1));
  box.querySelector('.lightbox-next').addEventListener('click', () => show(index + 1));
  box.addEventListener('click', (event) => { if (event.target === box) close(); });
  document.addEventListener('keydown', (event) => {
    if (box.hidden) return;
    if (event.key === 'Escape') close();
    if (event.key === 'ArrowLeft') show(index - 1);
    if (event.key === 'ArrowRight') show(index + 1);
  });
})();
