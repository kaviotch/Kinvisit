/**
 * Fires automatically whenever a Netlify form is submitted.
 *
 * Sends the family an immediate confirmation from a Kinvisit address, and
 * sends Kunal the submission itself. Netlify's own form notification already
 * covers the second one, so if you turn that on you can delete the internal
 * email here.
 *
 * Needs two environment variables, set in Netlify under
 * Site settings -> Environment variables:
 *
 *   RESEND_API_KEY   an API key from resend.com
 *   INTERNAL_EMAIL   where visit requests should land, e.g. kunal@kinvisit.in
 *
 * The domain kinvisit.in must be verified in Resend before mail will send.
 * Until both variables exist the function exits quietly and the submission is
 * still recorded by Netlify Forms, so nothing is ever lost.
 */

const FROM = 'Kinvisit <hello@kinvisit.in>';
const WA = 'https://wa.me/918920428806';

async function send(payload) {
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`resend ${res.status}: ${await res.text()}`);
  return res.json();
}

function esc(v) {
  return String(v == null ? '' : v).replace(/[<>&]/g, (c) => (
    { '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]
  ));
}

exports.handler = async (event) => {
  if (!process.env.RESEND_API_KEY) {
    console.log('RESEND_API_KEY not set, skipping confirmation email');
    return { statusCode: 200, body: 'skipped' };
  }

  let data = {};
  try {
    data = JSON.parse(event.body).payload.data || {};
  } catch (err) {
    console.error('unparseable submission', err);
    return { statusCode: 200, body: 'ignored' };
  }

  const name = (data['your-name'] || '').trim();
  const first = name.split(/\s+/)[0] || 'there';

  const confirmation = `
    <div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;font-size:16px;line-height:1.6;color:#191815;max-width:520px">
      <p style="font-size:20px;margin:0 0 20px"><strong>Kinvisit</strong></p>
      <p>${esc(first)}, we have your request. Here is what happens next.</p>
      <ol style="padding-left:20px">
        <li style="margin-bottom:8px">We call you within one working day, at an hour that works
            where you live${data['your-city'] ? ` (you told us ${esc(data['your-city'])})` : ''}.</li>
        <li style="margin-bottom:8px">On that call we confirm the appointment, the hospital, and
            what you want raised in the room.</li>
        <li>Only then is a companion assigned. You are not charged before that call.</li>
      </ol>
      <p>If the written report does not reach you on the day of the visit, that visit is not billed.</p>
      <p>Anything urgent before then, message us on WhatsApp: <a href="${WA}">${WA}</a></p>
      <p style="color:#55504A;font-size:14px;border-top:1px solid #E5DFD3;padding-top:16px;margin-top:24px">
        Kinvisit is not a medical provider. Our companions document and clarify. They do not
        diagnose, prescribe, or advise. In an emergency, call your local emergency number or go to
        the nearest hospital.
      </p>
    </div>`;

  const rows = Object.entries(data)
    .filter(([k]) => k !== 'form-name' && k !== 'company-website')
    .map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;color:#6E685F">${esc(k)}</td><td style="padding:4px 0"><strong>${esc(v)}</strong></td></tr>`)
    .join('');

  const jobs = [];

  if (data.phone || data.email) {
    const to = data.email || null;
    if (to) {
      jobs.push(send({
        from: FROM,
        to: [to],
        subject: 'We have your Kinvisit request',
        html: confirmation,
      }));
    }
  }

  if (process.env.INTERNAL_EMAIL) {
    jobs.push(send({
      from: FROM,
      to: [process.env.INTERNAL_EMAIL],
      reply_to: data.email || undefined,
      subject: `Visit request: ${name || 'unnamed'}${data['your-city'] ? ` (${data['your-city']})` : ''}`,
      html: `<table style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;font-size:15px">${rows}</table>`,
    }));
  }

  const results = await Promise.allSettled(jobs);
  results.forEach((r) => { if (r.status === 'rejected') console.error(r.reason); });

  return { statusCode: 200, body: 'ok' };
};
