const test = require('node:test');
const assert = require('node:assert/strict');
const { submitMessage, attach } = require('../assets/contact.js');
const payload = { access_key: '00000000-0000-0000-0000-000000000000', name: ' Test Visitor ', email: ' visitor@example.com ', message: ' A photography inquiry. ' };
const success = () => ({ ok: true, status: 200, json: async () => ({ success: true, message: 'Email sent successfully!' }) });

function formFixture() {
  let handler;
  const attributes = {};
  const button = { disabled: false, textContent: 'Send message', setAttribute: (k,v) => attributes[k]=v, removeAttribute: k => delete attributes[k] };
  const status = { textContent: '', dataset: {} };
  const form = { resets: 0, querySelector: s => s === '#contactStatus' ? status : button,
    reportValidity: () => true, reset() { this.resets++; },
    addEventListener(type,callback) { if(type === 'submit') handler=callback; } };
  return { form, button, status, attributes, send: () => handler({ preventDefault() {} }) };
}

test('uses the documented JSON endpoint and visitor reply-to email', async () => {
  let request;
  const result = await submitMessage(payload, { fetchImpl: async (url,options) => { request={url,options}; return success(); } });
  assert.equal(request.url,'https://api.web3forms.com/submit');
  assert.equal(request.options.method,'POST');
  assert.equal(request.options.headers['Content-Type'],'application/json');
  assert.deepEqual(JSON.parse(request.options.body),{...payload,name:'Test Visitor',email:'visitor@example.com',message:'A photography inquiry.'});
  assert.equal(result.success,true);
});
test('invalid or empty fields never send a request', async () => {
  let called=false;
  await assert.rejects(submitMessage({...payload,email:'invalid'}, {fetchImpl: async()=>{called=true;}}), /valid email/);
  await assert.rejects(submitMessage({...payload,message:'   '}, {fetchImpl: async()=>{called=true;}}));
  assert.equal(called,false);
});
test('a failed service response never reports success', async () => {
  await assert.rejects(submitMessage(payload,{fetchImpl:async()=>({ok:false,status:400,json:async()=>({success:false})})}),/wasn’t sent/);
  await assert.rejects(submitMessage(payload,{fetchImpl:async()=>({ok:true,status:200,json:async()=>({success:false})})}),/wasn’t sent/);
});
test('malformed responses and rate limits receive clear retry messages', async () => {
  await assert.rejects(submitMessage(payload,{fetchImpl:async()=>({ok:true,status:200,json:async()=>{throw new SyntaxError('Invalid JSON');}})}),/couldn’t confirm/);
  await assert.rejects(submitMessage(payload,{fetchImpl:async()=>({ok:false,status:429,json:async()=>({success:false})})}),/wait a moment/);
});
test('only confirmed success resets the form and restores the button', async () => {
  const fixture=formFixture();
  attach(fixture.form,{fetchImpl:async()=>success(),formData:()=>payload});
  await fixture.send();
  assert.equal(fixture.form.resets,1);
  assert.equal(fixture.status.dataset.state,'success');
  assert.equal(fixture.button.disabled,false);
  assert.equal(fixture.button.textContent,'Send message');
});
test('a network error preserves the message and allows retry', async () => {
  const fixture=formFixture();
  attach(fixture.form,{fetchImpl:async()=>{throw new TypeError('Network unavailable');},formData:()=>payload});
  await fixture.send();
  assert.equal(fixture.form.resets,0);
  assert.equal(fixture.status.dataset.state,'error');
  assert.match(fixture.status.textContent,/message is still here/);
  assert.equal(fixture.button.disabled,false);
});
test('repeated clicks while sending issue only one request', async () => {
  const fixture=formFixture();let resolve,calls=0;
  attach(fixture.form,{fetchImpl:()=>{calls++;return new Promise(r=>{resolve=r;});},formData:()=>payload});
  const first=fixture.send();
  await fixture.send();
  assert.equal(calls,1);
  assert.equal(fixture.button.disabled,true);
  assert.equal(fixture.attributes['aria-busy'],'true');
  resolve(success());await first;
  assert.equal(fixture.button.disabled,false);
});
