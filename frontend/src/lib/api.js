const apiBase = '/api'

async function unwrap(response) {
  if (response.ok) {
    return response.json()
  }

  let message = '请求失败'

  try {
    const data = await response.json()
    message = data.detail || message
  } catch {
    //
  }

  throw new Error(message)
}

export async function createParcel(formData) {
  const response = await fetch(`${apiBase}/parcels`, {
    method: 'POST',
    body: formData
  })

  return unwrap(response)
}

export async function pickupParcel(payload) {
  const response = await fetch(`${apiBase}/pickup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  return unwrap(response)
}

export async function fetchParcelMeta(code) {
  const response = await fetch(`${apiBase}/parcels/${code}`)
  return unwrap(response)
}
