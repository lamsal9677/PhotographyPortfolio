/* Web3Forms contact integration. No email client or backend server is required. */
(function () {
  'use strict';
  const ENDPOINT = 'https://api.web3forms.com/submit';

  async function submitMessage(payload, options = {}) {
    const fetcher = options.fetchImpl || globalThis.fetch;
    const body = { ...payload };
    for (const key of ['name', 'email', 'message']) body[key] = String(body[key] || '').trim();
    if (!body.name || !body.message || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email)) {
      throw new Error('Please add your name, a valid email address, and a message.');
    }
    if (!body.access_key) throw new Error('The form is temporarily unavailable. Please use the email link.');
    if (body.botcheck) throw new Error('Unable to submit this message.');
    const response = await fetcher(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
      signal: options.signal
    });
    let result;
    try { result = await response.json(); }
    catch { throw new Error('We couldn’t confirm delivery. Your message is still here. Please try again.'); }
    if (!response.ok || result.success !== true) {
      throw new Error(response.status === 429
        ? 'Please wait a moment before trying again. Your message is still here.'
        : 'Your message wasn’t sent. Please try again or use the email link.');
    }
    return result;
  }

  function attach(form, options = {}) {
    if (!form) return;
    const button = form.querySelector('button[type="submit"]');
    const status = form.querySelector('#contactStatus');
    const makeData = options.formData || (element => Object.fromEntries(new FormData(element).entries()));
    let busy = false;
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (busy || !form.reportValidity()) return;
      busy = true;
      button.disabled = true;
      button.textContent = 'Sending...';
      button.setAttribute('aria-busy', 'true');
      status.textContent = 'Sending your message...';
      status.dataset.state = 'sending';
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 25000);
      try {
        await submitMessage(makeData(form), { fetchImpl: options.fetchImpl, signal: controller.signal });
        form.reset();
        status.textContent = 'Thank you - your message has been sent. I’ll reply by email.';
        status.dataset.state = 'success';
      } catch (error) {
        status.textContent = error.name === 'AbortError' || error instanceof TypeError
          ? 'We couldn’t confirm delivery. Your message is still here. Check your connection and try again.'
          : error.message;
        status.dataset.state = 'error';
      } finally {
        clearTimeout(timeout);
        busy = false;
        button.disabled = false;
        button.textContent = 'Send message';
        button.removeAttribute('aria-busy');
      }
    });
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { submitMessage, attach };
  if (typeof document !== 'undefined') attach(document.querySelector('#contactForm'));
})();
