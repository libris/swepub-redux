export async function fetchAsync(url, options = null, acceptHeader, responseHeader) {
  let response;
  // await response of fetch call
  if (options) {
    response = await fetch(url, options);
  } else {
    response = await fetch(url);
  }
  if (response.status === 204) {
    return response;
  }
  if (response.status >= 400) {
    return response;
  }
  // only proceed once promise is resolved
  let data = {};

  if (acceptHeader && acceptHeader.startsWith('text')) {
    // parse as text
    const text = await response.text();
    // add the UTF-8 BOM at the start of the text for proper encoding
    data.text = `\uFEFF${text}`;
  } else {
    data = await response.json();
  }

  // extract requested response header
  if (responseHeader) {
    const header = response.headers.get(responseHeader);

    if (header) {
      data[responseHeader] = header;
    }
  }

  data.statusCode = response.status;
  return data;
}

export async function get(url, acceptHeader = false, responseHeader = false) {
  const headers = new Headers();
  headers.append('Content-Type', 'application/json');
  if (acceptHeader) {
    headers.append('Accept', acceptHeader);
  }
  const operation = await fetchAsync(url, {
    headers,
    method: 'GET',
  }, acceptHeader, responseHeader);
  return operation;
}

export async function post(url, body, acceptHeader = false) {
  const headers = new Headers();
  headers.append('Content-Type', 'application/json');
  if (acceptHeader) {
    headers.append('Accept', acceptHeader);
  }
  const operation = await fetchAsync(url, {
    method: 'POST',
    headers,
    body,
  }, acceptHeader);
  return operation;
}
