import { createParcel } from './lib/api'

const historyKey = 'parcel-history'
const keepHours = 24

function readHistory() {
  try {
    return JSON.parse(localStorage.getItem(historyKey) || '[]')
  } catch {
    return []
  }
}

function formatDate(value) {
  const date = new Date(value)
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
}

function remainingSeconds(value) {
  return Math.max(0, Math.floor((new Date(value).getTime() - Date.now()) / 1000))
}

async function upload(formData) {
  const file = formData.get('file')
  const body = new FormData()

  if (file instanceof File && file.type === 'text/plain' && file.name === 'shared_text.txt') {
    body.append('text_content', await file.text())
  } else if (file instanceof File) {
    body.append('files', file)
  }

  const data = await createParcel(body)
  const size = file instanceof File ? file.size : 0

  const entry = {
    code: data.code,
    name: file instanceof File ? file.name : `${data.code}.txt`,
    type: file instanceof File && file.name !== 'shared_text.txt' ? '文件' : '文本',
    pickupUrl: data.pickup_url,
    size,
    expiresAt: data.expires_at,
    createdAt: new Date().toISOString()
  }

  localStorage.setItem(historyKey, JSON.stringify([entry, ...readHistory()].slice(0, 20)))

  return {
    data: {
      code: data.code,
      file_id: data.code,
      filename: entry.name,
      size,
      expire_at: data.expires_at,
      share_url: `/pickup/${data.code}`,
      pickup_url: data.pickup_url
    }
  }
}

const api = {
  async get(url) {
    if (url === '/file-share/config') {
      return { data: { expiry_minutes: keepHours * 60 } }
    }

    if (url === '/file-share/admin/list') {
      const shares = readHistory().map((item) => ({
        file_id: item.code,
        code: item.code,
        filename: item.name,
        username: '本地',
        size: item.size || 0,
        created_at: formatDate(item.createdAt),
        share_url: `/pickup/${item.code}`,
        is_expired: remainingSeconds(item.expiresAt) === 0,
        remaining_seconds: remainingSeconds(item.expiresAt)
      }))

      return { data: { shares } }
    }

    throw { response: { data: { detail: `Unsupported GET ${url}` } } }
  },

  async post(url, formData) {
    if (url.startsWith('/file-share/upload')) {
      return upload(formData)
    }

    throw { response: { data: { detail: `Unsupported POST ${url}` } } }
  }
}

export default api
