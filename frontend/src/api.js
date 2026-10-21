const BASE_URL = '/api/v1'

// ошибки бэкенда приходят на английском, показываем их по-русски
const MESSAGES = {
  'Payer is not in this event': 'Плательщик не участвует в этом событии',
  'Some users are not in this event': 'Кто-то из участников траты не состоит в событии',
  'Shares do not add up to the total amount': 'Сумма долей не совпадает с суммой траты',
  'Expense has settled debts and cannot be changed': 'По этой трате уже были оплаты, её нельзя удалить',
  'User has unsettled debts in this event': 'У этого человека есть неоплаченные долги в событии',
  'User is already in event': 'Этот человек уже участвует в событии',
  'User with this email already exists': 'Человек с такой почтой уже есть',
  'No unsettled debts between these users': 'Между ними нет неоплаченных долгов',
  'Event not found': 'Событие не найдено',
}

function errorMessage(status, data) {
  if (status === 422) {
    return 'Проверьте заполненные поля'
  }
  const detail = data && data.detail
  return MESSAGES[detail] || detail || `Ошибка сервера (${status})`
}

async function request(method, path, body) {
  let response
  try {
    response = await fetch(BASE_URL + path, {
      method: method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new Error('Сервер не отвечает. Проверьте, что бэкенд запущен')
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(errorMessage(response.status, data))
  }

  if (response.status === 204) {
    return null
  }
  return response.json()
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  delete: (path) => request('DELETE', path),
}
