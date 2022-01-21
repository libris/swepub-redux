export function getYear() {
  const today = new Date();
  return parseInt(today.getFullYear().toString());
}

export function download(text, name, type) {
  const file = new Blob([text], { type });
  const isIE = /* @cc_on!@ */false || !!document.documentMode;
  if (isIE) {
    window.navigator.msSaveOrOpenBlob(file, name);
  } else {
    const linkEl = document.createElement('a');
    linkEl.href = URL.createObjectURL(file);
    document.body.appendChild(linkEl);
    linkEl.style.display = 'none';
    linkEl.download = name;
    linkEl.click();
  }
}
